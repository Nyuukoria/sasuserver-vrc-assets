import io
import sqlite3
import time
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from backend.app import create_app, hash_password
from image_helpers import palette_png
from test_drive import app, client_for, upload_file, ORIGIN


def test_profile_picture_is_private_reencoded_and_replaceable(app):
    member = client_for(app, 'friend')
    result = member.post('/api/me/avatar', content=palette_png())
    assert result.status_code == 200, result.text
    url = result.json()['url']
    assert TestClient(app, base_url=ORIGIN).get(url).status_code == 401
    image = client_for(app).get(url)
    assert image.headers['content-type'] == 'image/webp'
    with Image.open(io.BytesIO(image.content)) as picture:
        assert picture.size == (256, 256)
    assert member.get('/api/me').json()['avatar_url'] == url
    assert member.patch('/api/me', json={'name': 'New name'}).status_code == 200
    node_id = upload_file(member)
    item = next(n for n in member.get('/api/nodes').json()['items'] if n['id'] == node_id)
    assert item['owner_name'] == 'New name'
    assert item['owner_avatar'] == url
    created = item['created']
    member.patch('/api/nodes/' + node_id, json={'name': 'renamed.txt'})
    assert member.get('/api/nodes').json()['items'][0]['created'] == created
    replacement = member.post('/api/me/avatar', content=palette_png()).json()['url']
    assert replacement != url
    assert member.get(url).status_code == 404
    assert member.delete('/api/me/avatar').status_code == 200
    assert member.get(replacement).status_code == 404


def test_viewer_can_edit_own_profile_but_not_folder_covers(app):
    viewer, owner = client_for(app, 'viewer'), client_for(app)
    folder = owner.post('/api/folders', json={'name': 'Folder'}).json()['id']
    assert viewer.post('/api/me/avatar', content=palette_png()).status_code == 200
    assert viewer.patch('/api/me', json={'name': 'Viewer name'}).status_code == 200
    assert viewer.post(f'/api/nodes/{folder}/cover', content=palette_png()).status_code == 403
    assert viewer.delete(f'/api/nodes/{folder}/cover').status_code == 403
    assert viewer.post('/api/me/avatar', content=palette_png(), headers={'X-CSRF-Token': ''}).status_code == 403
    assert viewer.post('/api/me/avatar', content=palette_png(), headers={'Origin': 'https://bad.example'}).status_code == 403


def test_folder_cover_permissions_trash_restore_and_purge(app):
    friend, other, owner = client_for(app, 'friend'), client_for(app, 'other'), client_for(app)
    folder = friend.post('/api/folders', json={'name': 'Project'}).json()['id']
    assert other.post(f'/api/nodes/{folder}/cover', content=palette_png()).status_code == 403
    response = friend.post(f'/api/nodes/{folder}/cover', content=palette_png())
    assert response.status_code == 200, response.text
    url = response.json()['url']
    with Image.open(io.BytesIO(friend.get(url).content)) as image:
        assert image.size == (960, 540)
    assert friend.get('/api/nodes').json()['items'][0]['cover_url'] == url
    assert friend.delete('/api/nodes/' + folder).status_code == 200
    assert friend.get(url).status_code == 404
    assert friend.post(f'/api/nodes/{folder}/restore').status_code == 200
    assert friend.get(url).status_code == 200
    friend.delete('/api/nodes/' + folder)
    assert owner.delete(f'/api/nodes/{folder}/permanent').status_code == 200
    with app.state.db() as con:
        assert con.execute('SELECT COUNT(*) FROM pictures').fetchone()[0] == 0


def test_invalid_or_oversized_pictures_leave_existing_avatar_unchanged(app):
    owner = client_for(app)
    url = owner.post('/api/me/avatar', content=palette_png()).json()['url']
    for content in [b'<svg onload="alert(1)"></svg>', b'not an image', b'\x89PNG\r\n\x1a\n']:
        assert owner.post('/api/me/avatar', content=content).status_code == 400
    assert owner.post('/api/me/avatar', content=b'x' * (8 * 1024 * 1024 + 1)).status_code == 413
    data = io.BytesIO()
    Image.new('RGB', (4100, 4100)).save(data, 'PNG')
    assert owner.post('/api/me/avatar', content=data.getvalue()).status_code == 400
    assert owner.get('/api/me').json()['avatar_url'] == url


def test_media_uploads_and_sorted_pagination(app):
    owner = client_for(app)
    for name in ['sample.mkv', 'sample.mp4', 'sample.mp3', 'arbitrary.custom']:
        upload_file(owner, name, b'example bytes')
    assert {n['name'] for n in owner.get('/api/nodes?view=videos').json()['items']} == {'sample.mkv', 'sample.mp4'}
    assert owner.get('/api/nodes?view=audio').json()['items'][0]['name'] == 'sample.mp3'
    page = owner.get('/api/nodes?sort=name&limit=1&offset=1').json()
    assert page['items'][0]['name'] == 'sample.mkv'
    assert page['total'] == 4


def test_additive_migration_keeps_existing_accounts_and_files(tmp_path):
    state, storage = tmp_path / 'state', tmp_path / 'files'
    state.mkdir()
    with sqlite3.connect(state / 'drive.sqlite3') as con:
        con.executescript((Path(__file__).parents[1] / 'backend/schema.sql').read_text())
        con.execute('INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,?,?)', ('old', 'old@example.com', 'Old user', hash_password('old-password'), 'owner', time.time()))
        con.execute('INSERT INTO nodes(id,name,kind,owner,created,updated) VALUES(?,?,?,?,?,?)', ('old-folder', 'Existing folder', 'folder', 'old', time.time(), time.time()))
    application = create_app(state, storage, ORIGIN, True)
    with application.state.db() as con:
        assert con.execute('SELECT avatar FROM users WHERE id="old"').fetchone()[0] is None
        assert con.execute('SELECT cover,name FROM nodes').fetchone()['name'] == 'Existing folder'
    # Opening a second time is safe too.
    create_app(state, storage, ORIGIN, True)
