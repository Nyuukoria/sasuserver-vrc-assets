import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from backend.app import CHUNK, create_app, digest, hash_password

ORIGIN = 'https://sasutendo.tech'


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv('STORAGE_CAPACITY_BYTES', '4000000000000')
    application = create_app(tmp_path / 'state', tmp_path / 'storage', ORIGIN, True)
    with application.state.db() as con:
        for user, role in [('owner', 'owner'), ('friend', 'member'), ('viewer', 'viewer'), ('other', 'member')]:
            con.execute('INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,?,?)', (user, f'{user}@example.com', user.title(), hash_password('test-password-only'), role, time.time()))
    return application


def client_for(app, user='owner'):
    client = TestClient(app, base_url=ORIGIN)
    client.headers['Origin'] = ORIGIN
    login = client.post('/api/login', json={'email': f'{user}@example.com', 'password': 'test-password-only'})
    assert login.status_code == 200
    csrf = client.get('/api/me').json()['csrf']
    client.headers['X-CSRF-Token'] = csrf
    return client


def upload_file(client, name='avatar.unitypackage', data=b'private content', parent=None):
    start = client.post('/api/uploads', json={'name': name, 'size': len(data), 'parent': parent})
    assert start.status_code == 200, start.text
    upload_id = start.json()['id']
    if data:
        response = client.patch('/api/uploads/' + upload_id, content=data, headers={'Upload-Offset': '0'})
        assert response.status_code == 200, response.text
    done = client.post('/api/uploads/' + upload_id + '/complete')
    assert done.status_code == 200, done.text
    return done.json()['id']


def test_public_signup_and_file_access_are_closed(app):
    client = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN})
    for path in ['/api/nodes', '/api/stats', '/api/activity', '/api/admin', '/api/uploads', '/api/nodes/anything/download']:
        assert client.get(path).status_code == 401
    assert client.post('/api/signup', json={}).status_code in (404, 405)
    assert client.post('/api/join', json={'email': 'stranger@example.com', 'name': 'Stranger', 'password': 'long-password', 'token': 'invented-token-' * 3}).status_code == 400
    assert client.get('/').status_code == 200
    assert client.get('/backend/app.py').status_code == 404
    assert client.get('/state/drive.sqlite3').status_code == 404


def test_cookies_csrf_origin_and_logout(app):
    client = client_for(app)
    cookie = client.cookies.get('sasu_session')
    assert cookie
    # Session values in the database are digests, not reusable bearer cookies.
    with app.state.db() as con:
        assert con.execute('SELECT token FROM sessions').fetchone()[0] == digest(cookie)
    response = client.post('/api/folders', json={'name': 'Blocked'}, headers={'X-CSRF-Token': ''})
    assert response.status_code == 403
    for origin in ['https://evil.example', 'null', '']:
        assert client.post('/api/folders', json={'name': 'Blocked'}, headers={'Origin': origin}).status_code == 403
    assert client.post('/api/logout').status_code == 200
    assert client.get('/api/me').status_code == 401
    response = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}).post('/api/login', json={'email': 'owner@example.com', 'password': 'test-password-only'})
    for flag in ['Secure', 'HttpOnly', 'SameSite=lax']:
        assert flag in response.headers['set-cookie']


def test_single_use_email_bound_invite_and_revocation(app):
    owner = client_for(app)
    invite = owner.post('/api/invites', json={'email': 'new@example.com', 'role': 'member'}).json()
    token = invite['url'].split('invite=')[1]
    outsider = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN})
    assert outsider.get('/api/invite', params={'token': token}).json()['email'] == 'new@example.com'
    wrong = {'email': 'wrong@example.com', 'name': 'New', 'password': 'test-password-only', 'token': token}
    assert outsider.post('/api/join', json=wrong).status_code == 400
    wrong['email'] = 'new@example.com'
    assert outsider.post('/api/join', json=wrong).status_code == 200
    assert outsider.get('/api/me').json()['role'] == 'member'
    assert outsider.post('/api/join', json=wrong).status_code == 400
    assert outsider.get('/api/invite', params={'token': token}).status_code == 404
    second = owner.post('/api/invites', json={'email': 'next@example.com'}).json()
    owner.delete('/api/invites/' + second['id'])
    assert outsider.get('/api/invite', params={'token': second['url'].split('invite=')[1]}).status_code == 404
    assert 'token' not in str(owner.get('/api/admin').json())


def test_expired_invite_and_unprivileged_invites(app):
    owner, friend = client_for(app), client_for(app, 'friend')
    assert friend.post('/api/invites', json={'email': 'new@example.com'}).status_code == 403
    assert owner.post('/api/invites', json={'email': 'new@example.com', 'role': 'owner'}).status_code == 400
    invite = owner.post('/api/invites', json={'email': 'new@example.com'}).json()
    with app.state.db() as con:
        con.execute('UPDATE invites SET expires=0 WHERE id=?', (invite['id'],))
    assert friend.get('/api/invite', params={'token': invite['url'].split('invite=')[1]}).status_code == 404


def test_simultaneous_acceptance_only_consumes_invite_once(app):
    owner = client_for(app)
    invite = owner.post('/api/invites', json={'email': 'racer@example.com'}).json()
    body = {'email': 'racer@example.com', 'name': 'Racer', 'password': 'test-password-only', 'token': invite['url'].split('invite=')[1]}
    def accept(_):
        with TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}) as client:
            return client.post('/api/join', json=body).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(accept, range(2))) == [200, 400]


def test_disable_account_revokes_sessions(app):
    owner, friend = client_for(app), client_for(app, 'friend')
    assert owner.patch('/api/users/friend', json={'active': False}).status_code == 200
    assert friend.get('/api/nodes').status_code == 401
    assert owner.patch('/api/users/owner', json={'active': False}).status_code == 400
    assert owner.patch('/api/users/friend', json={'active': True}).status_code == 200
    assert friend.get('/api/nodes').status_code == 401
    assert client_for(app, 'friend').get('/api/nodes').status_code == 200


def test_viewer_cannot_mutate_files(app):
    owner, viewer = client_for(app), client_for(app, 'viewer')
    file_id = upload_file(owner)
    folder = owner.post('/api/folders', json={'name': 'Root'}).json()['id']
    for method, path, body in [('post', '/api/folders', {'name': 'No'}), ('post', '/api/uploads', {'name': 'No', 'size': 1}), ('patch', '/api/nodes/' + file_id, {'name': 'No'})]:
        assert getattr(viewer, method)(path, json=body).status_code == 403
    assert viewer.delete('/api/nodes/' + folder).status_code == 403
    assert viewer.get('/api/nodes/' + file_id + '/download').content == b'private content'
    assert viewer.post('/api/nodes/' + file_id + '/star').status_code == 200


def test_nested_folder_upload_resume_and_download_range(app):
    friend = client_for(app, 'friend')
    folder = friend.post('/api/folders', json={'name': 'Worlds'}).json()['id']
    child = friend.post('/api/folders', json={'name': 'Cozy room', 'parent': folder}).json()['id']
    assert friend.post('/api/folders', json={'name': 'Worlds'}).json()['id'] == folder
    start = friend.post('/api/uploads', json={'name': 'scene.blend', 'size': 10, 'parent': child}).json()
    path = '/api/uploads/' + start['id']
    assert friend.patch(path, content=b'01234', headers={'Upload-Offset': '0'}).json()['offset'] == 5
    assert friend.patch(path, content=b'wrong', headers={'Upload-Offset': '0'}).status_code == 409
    assert friend.post(path + '/complete').status_code == 409
    # Reconnect with a completely new browser session and continue the same upload.
    again = client_for(app, 'friend')
    assert again.get(path).json()['offset'] == 5
    assert again.patch(path, content=b'56789', headers={'Upload-Offset': '5'}).status_code == 200
    file_id = again.post(path + '/complete').json()['id']
    assert again.post(path + '/complete').json()['id'] == file_id
    assert again.get('/api/nodes/' + file_id + '/download').content == b'0123456789'
    ranged = again.get('/api/nodes/' + file_id + '/download', headers={'Range': 'bytes=2-5'})
    assert ranged.status_code == 206 and ranged.content == b'2345'
    listed = again.get('/api/nodes', params={'parent': child}).json()
    assert [x['name'] for x in listed['breadcrumbs']] == ['Worlds', 'Cozy room']
    assert listed['items'][0]['name'] == 'scene.blend'


def test_chunk_limit_and_wrong_size_preserve_committed_offset(app):
    client = client_for(app)
    upload = client.post('/api/uploads', json={'name': 'large.bin', 'size': CHUNK + 10}).json()['id']
    path = '/api/uploads/' + upload
    assert client.patch(path, content=b'x' * (CHUNK + 1), headers={'Upload-Offset': '0'}).status_code == 413
    assert client.get(path).json()['offset'] == 0
    assert (app.state.storage / 'uploads' / upload).stat().st_size == 0
    short = client.post('/api/uploads', json={'name': 'short.bin', 'size': 3}).json()['id']
    assert client.patch('/api/uploads/' + short, content=b'1234', headers={'Upload-Offset': '0'}).status_code == 413
    assert client.get('/api/uploads/' + short).json()['offset'] == 0


def test_upload_ids_are_private_and_owner_can_cancel(app):
    friend, other, owner = client_for(app, 'friend'), client_for(app, 'other'), client_for(app)
    upload = friend.post('/api/uploads', json={'name': 'private.bin', 'size': 4}).json()['id']
    assert other.get('/api/uploads/' + upload).status_code == 404
    assert other.delete('/api/uploads/' + upload).status_code == 404
    assert owner.delete('/api/uploads/' + upload).status_code == 200
    assert not (app.state.storage / 'uploads' / upload).exists()


def test_names_traversal_and_ownership(app):
    owner, friend = client_for(app), client_for(app, 'friend')
    for name in ['../secret', '.', '..', 'a/b', 'a\\b', 'bad\x00name', '']:
        assert owner.post('/api/folders', json={'name': name}).status_code in (400, 422)
    file_id = upload_file(owner)
    assert friend.patch('/api/nodes/' + file_id, json={'name': 'stolen'}).status_code == 403
    assert friend.delete('/api/nodes/' + file_id).status_code == 403
    folder = friend.post('/api/folders', json={'name': 'Shared'}).json()['id']
    upload_file(owner, name='inside.bin', parent=folder)
    assert friend.delete('/api/nodes/' + folder).status_code == 403
    assert friend.patch('/api/nodes/' + folder, json={'name': 'renamed'}).status_code == 403
    assert owner.delete('/api/nodes/' + folder).status_code == 200


def test_move_cycles_name_conflicts_and_trash_restore(app):
    owner = client_for(app)
    a = owner.post('/api/folders', json={'name': 'A'}).json()['id']
    b = owner.post('/api/folders', json={'name': 'B', 'parent': a}).json()['id']
    assert owner.patch('/api/nodes/' + a, json={'parent': b, 'move': True}).status_code == 400
    file_id = upload_file(owner, parent=b)
    assert owner.delete('/api/nodes/' + a).status_code == 200
    assert owner.get('/api/nodes/' + file_id + '/download').status_code == 404
    trash = owner.get('/api/nodes?view=trash').json()['items']
    assert [x['id'] for x in trash] == [a]
    assert owner.post('/api/nodes/' + a + '/restore').status_code == 200
    assert owner.get('/api/nodes/' + file_id + '/download').status_code == 200
    assert owner.delete('/api/nodes/' + a).status_code == 200
    owner.post('/api/folders', json={'name': 'A'})
    assert owner.post('/api/nodes/' + a + '/restore').status_code == 409


def test_permanent_delete_and_pending_subtree_protection(app):
    owner = client_for(app)
    folder = owner.post('/api/folders', json={'name': 'Throwaway'}).json()['id']
    file_id = upload_file(owner, parent=folder)
    unfinished = owner.post('/api/uploads', json={'name': 'unfinished.bin', 'size': 4, 'parent': folder}).json()['id']
    owner.delete('/api/nodes/' + folder)
    assert owner.delete('/api/nodes/' + folder + '/permanent').status_code == 409
    owner.delete('/api/uploads/' + unfinished)
    assert owner.delete('/api/nodes/' + folder + '/permanent').status_code == 200
    assert not (app.state.storage / 'objects' / file_id).exists()
    assert owner.get('/api/stats').json()['used'] == 0


def test_dangerous_files_are_attachments_and_stars_are_personal(app):
    owner, friend = client_for(app), client_for(app, 'friend')
    file_id = upload_file(owner, name='payload.svg', data=b'<svg onload="alert(1)"/>')
    response = owner.get('/api/nodes/' + file_id + '/download?preview=true')
    assert response.headers['content-type'] == 'application/octet-stream'
    assert response.headers['content-disposition'].startswith('attachment')
    assert 'sandbox' in response.headers['content-security-policy']
    owner.post('/api/nodes/' + file_id + '/star')
    assert len(owner.get('/api/nodes?view=starred').json()['items']) == 1
    assert len(friend.get('/api/nodes?view=starred').json()['items']) == 0
    assert response.headers['cache-control'] == 'no-store'


def test_storage_quota_includes_pending_uploads_and_trash(tmp_path, monkeypatch):
    monkeypatch.setenv('STORAGE_CAPACITY_BYTES', '10')
    app = create_app(tmp_path / 's', tmp_path / 'd', ORIGIN, True)
    with app.state.db() as con:
        con.execute('INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,?,?)', ('owner', 'owner@example.com', 'Owner', hash_password('test-password-only'), 'owner', time.time()))
    owner = client_for(app)
    upload = owner.post('/api/uploads', json={'name': 'first', 'size': 8}).json()['id']
    assert owner.post('/api/uploads', json={'name': 'second', 'size': 3}).status_code == 507
    owner.delete('/api/uploads/' + upload)
    file_id = upload_file(owner, name='file', data=b'12345678')
    owner.delete('/api/nodes/' + file_id)
    assert owner.post('/api/uploads', json={'name': 'third', 'size': 3}).status_code == 507


def test_search_and_pagination(app):
    owner = client_for(app)
    for name in ['Room A', 'Room B', 'Texture C']:
        owner.post('/api/folders', json={'name': name})
    first = owner.get('/api/nodes?limit=1').json()
    second = owner.get('/api/nodes?limit=1&offset=1').json()
    assert first['total'] == 3 and first['items'][0]['id'] != second['items'][0]['id']
    assert owner.get('/api/nodes?q=room').json()['total'] == 2
    assert owner.get('/api/nodes?offset=-1').status_code == 400


def test_login_rate_limit_survives_errors(app):
    outsider = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN})
    for _ in range(8):
        assert outsider.post('/api/login', json={'email': 'nobody@example.com', 'password': 'wrong'}).status_code == 401
    assert outsider.post('/api/login', json={'email': 'nobody@example.com', 'password': 'wrong'}).status_code == 429


def test_crash_recovery_after_finalize_rename(app):
    owner = client_for(app)
    upload_id = owner.post('/api/uploads', json={'name': 'recover.bin', 'size': 4}).json()['id']
    owner.patch('/api/uploads/' + upload_id, content=b'1234', headers={'Upload-Offset': '0'})
    # Simulate the process exiting after rename but before the DB transaction commits.
    (app.state.storage / 'uploads' / upload_id).rename(app.state.storage / 'objects' / upload_id)
    assert owner.post('/api/uploads/' + upload_id + '/complete').status_code == 200
    assert owner.get('/api/nodes/' + upload_id + '/download').content == b'1234'


def test_empty_file_and_duplicate_pending_name(app):
    owner = client_for(app)
    empty = upload_file(owner, name='empty.txt', data=b'')
    assert owner.get('/api/nodes/' + empty + '/download').content == b''
    assert owner.post('/api/uploads', json={'name': 'same', 'size': 2}).status_code == 200
    assert owner.post('/api/uploads', json={'name': 'SAME', 'size': 2}).status_code == 409


def test_member_activity_does_not_expose_invitation_email_addresses(app):
    owner, friend = client_for(app), client_for(app, 'friend')
    owner.post('/api/invites', json={'email': 'private-invite@example.com'})
    assert 'private-invite@example.com' in owner.get('/api/activity').text
    assert 'private-invite@example.com' not in friend.get('/api/activity').text


def test_concurrent_moves_cannot_create_a_folder_cycle(app):
    owner = client_for(app)
    a = owner.post('/api/folders', json={'name': 'A'}).json()['id']
    b = owner.post('/api/folders', json={'name': 'B'}).json()['id']
    def move(pair):
        client = client_for(app)
        return client.patch('/api/nodes/' + pair[0], json={'parent': pair[1], 'move': True}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(move, [(a, b), (b, a)]))
    assert sorted(results) == [200, 400]
