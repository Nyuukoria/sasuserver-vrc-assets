import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app import create_app
from image_helpers import palette_png
from test_drive import app, client_for, upload_file, ORIGIN


def gif_bytes(frames=3):
    output = io.BytesIO()
    images = [Image.new('RGB', (30, 20), ('red', 'green', 'blue')[i % 3]) for i in range(frames)]
    images[0].save(output, 'GIF', save_all=True, append_images=images[1:], duration=80, loop=0, comment=b'private metadata')
    return output.getvalue()


@pytest.mark.parametrize('kind,size', [('avatar', (256, 256)), ('banner', (960, 320))])
def test_animated_pictures_have_matching_mime_and_bounded_size(app, kind, size):
    owner = client_for(app)
    result = owner.post('/api/me/' + kind, content=gif_bytes())
    assert result.status_code == 200, result.text
    url = result.json()['url']
    response = owner.get(url)
    assert response.headers['content-type'] == 'image/gif'
    assert response.content.startswith((b'GIF87a', b'GIF89a'))
    with Image.open(io.BytesIO(response.content)) as image:
        assert image.size == size
        assert image.n_frames == 3
        assert 'comment' not in image.info
    assert owner.get('/api/me').json()[kind + '_url'] == url
    assert owner.get('/api/users/owner').json()[kind + '_url'] == url
    assert owner.get('/api/admin').json()['users'][0][kind + '_url'] == url
    assert TestClient(app, base_url=ORIGIN).get(url).status_code == 401
    replacement = owner.post('/api/me/' + kind, content=palette_png()).json()['url']
    assert owner.get(replacement).headers['content-type'] == 'image/webp'
    assert owner.get(url).status_code == 404
    assert owner.delete('/api/me/' + kind).status_code == 200
    assert owner.get(replacement).status_code == 404


def test_previously_stored_gifs_work_without_reuploading(app):
    owner = client_for(app)
    # Older versions saved GIF bytes in pictures but labelled every response WebP.
    with app.state.db() as con:
        con.execute('INSERT INTO pictures VALUES(?,?)', ('old-gif', gif_bytes()))
        con.execute('UPDATE users SET banner=? WHERE id="owner"', ('old-gif',))
    assert owner.get('/api/pictures/old-gif').headers['content-type'] == 'image/gif'


def test_animation_limits_and_banner_permissions(app):
    owner = client_for(app)
    url = owner.post('/api/me/banner', content=palette_png()).json()['url']
    assert owner.post('/api/me/banner', content=gif_bytes(121)).status_code == 400
    assert owner.get('/api/me').json()['banner_url'] == url
    assert owner.post('/api/me/banner', content=palette_png(), headers={'X-CSRF-Token': ''}).status_code == 403
    assert owner.post('/api/me/banner', content=palette_png(), headers={'Origin': 'https://wrong.example'}).status_code == 403
    viewer = client_for(app, 'viewer')
    assert viewer.post('/api/me/banner', content=palette_png()).status_code == 200


def test_comments_post_read_permissions_and_moderation(app):
    owner, friend, other, viewer = (client_for(app, name) for name in ['owner', 'friend', 'other', 'viewer'])
    node_id = upload_file(owner)
    path = f'/api/nodes/{node_id}/comments'
    anonymous = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN})
    assert anonymous.get(path).status_code == 401
    assert anonymous.post(path, json={'body': 'Anonymous'}).status_code == 401
    assert viewer.post(path, json={'body': 'Read-only'}).status_code == 403
    assert friend.post(path, json={'body': 'No CSRF'}, headers={'X-CSRF-Token': ''}).status_code == 403
    assert friend.post(path, json={'body': 'No origin'}, headers={'Origin': ''}).status_code == 403
    for invalid, status in [('', 422), ('  \n\t ', 400), ('x' * 1001, 422)]:
        assert friend.post(path, json={'body': invalid}).status_code == status
    picture = friend.post('/api/me/avatar', content=palette_png()).json()['url']
    body = '<script>alert("no")</script>\nA useful comment'
    result = friend.post(path, json={'body': '  ' + body + '  '})
    assert result.status_code == 200, result.text
    comment_id = result.json()['id']
    comments = viewer.get(path).json()
    assert len(comments) == 1
    assert comments[0]['body'] == body
    assert comments[0]['user_id'] == 'friend'
    assert comments[0]['user_avatar'] == picture
    assert other.delete('/api/comments/' + comment_id).status_code == 403
    assert viewer.delete('/api/comments/' + comment_id).status_code == 403
    assert friend.delete('/api/comments/' + comment_id).status_code == 200
    second = friend.post(path, json={'body': 'Owner can moderate'}).json()['id']
    assert owner.delete('/api/comments/' + second).status_code == 200
    assert owner.get(path).json() == []


def test_comments_persist_and_follow_folder_lifecycle(app):
    owner = client_for(app)
    folder = owner.post('/api/folders', json={'name': 'Folder'}).json()['id']
    child = upload_file(owner, parent=folder)
    comment_id = owner.post(f'/api/nodes/{child}/comments', json={'body': 'Keep this'}).json()['id']
    owner.post(f'/api/nodes/{folder}/comments', json={'body': 'Folder comment'})
    with app.state.db() as con:
        database = con.execute('PRAGMA database_list').fetchone()['file']
    from pathlib import Path
    restarted = create_app(Path(database).parent, app.state.storage, ORIGIN, True)
    fresh = client_for(restarted)
    assert fresh.get(f'/api/nodes/{child}/comments').json()[0]['id'] == comment_id
    owner.delete('/api/nodes/' + folder)
    assert owner.get(f'/api/nodes/{child}/comments').status_code == 404
    assert owner.post(f'/api/nodes/{child}/comments', json={'body': 'Trashed'}).status_code == 404
    assert owner.delete('/api/comments/' + comment_id).status_code == 404
    owner.post(f'/api/nodes/{folder}/restore')
    assert owner.get(f'/api/nodes/{child}/comments').json()[0]['body'] == 'Keep this'
    owner.delete('/api/nodes/' + folder)
    assert owner.delete(f'/api/nodes/{folder}/permanent').status_code == 200
    with app.state.db() as con:
        assert con.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 0


def test_server_has_no_offline_mode_and_revalidates_frontend(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCAL_TEST_MODE', '1')
    application = create_app(tmp_path / 'state', tmp_path / 'files', ORIGIN, True)
    client = TestClient(application, base_url=ORIGIN, headers={'Origin': ORIGIN})
    assert client.get('/api/status').json() == {'configured': False}
    assert client.post('/api/local-setup', json={}).status_code in (404, 405)
    for path in ['/', '/app.js', '/style.css']:
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers['Cache-Control'] == 'no-cache'
        assert "style-src 'self'" in response.headers['Content-Security-Policy']
        assert "'unsafe-inline'" not in response.headers['Content-Security-Policy']
