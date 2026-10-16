from fastapi.testclient import TestClient
from backend.app import create_app

BODY = {'name': 'Yuuki', 'email': 'local@example.com', 'password': 'local-test-password', 'samples': True}
ORIGIN = 'http://127.0.0.1:8765'


def make(tmp_path, enabled=True, host='127.0.0.1'):
    app = create_app(tmp_path / 'state', tmp_path / 'files', ORIGIN, False, local_test=enabled)
    return TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}, client=(host, 50000))


def test_local_setup_is_absent_in_production(tmp_path):
    client = make(tmp_path, False)
    assert client.get('/api/status').json()['local_test'] is False
    assert client.post('/api/local-setup', json=BODY).status_code in (404, 405)


def test_local_setup_rejects_remote_clients(tmp_path):
    client = make(tmp_path, host='192.0.2.1')
    assert client.get('/api/status').json()['local_test'] is False
    assert client.post('/api/local-setup', json=BODY).status_code == 403


def test_local_setup_seeds_real_files_and_only_runs_once(tmp_path):
    client = make(tmp_path)
    assert client.get('/api/status').json() == {'configured': False, 'local_test': True}
    response = client.post('/api/local-setup', json=BODY)
    assert response.status_code == 200, response.text
    assert 'HttpOnly' in response.headers['set-cookie']
    assert 'Secure' not in response.headers['set-cookie']
    user = client.get('/api/me').json()
    assert user['role'] == 'owner'
    assert client.get('/api/stats').json()['files'] == 5
    assert client.post('/api/local-setup', json=BODY).status_code == 409
    client.headers['X-CSRF-Token'] = user['csrf']
    invite = client.post('/api/invites', json={'email': 'friend@example.com'}).json()
    assert invite['url'].startswith(ORIGIN + '/?invite=')
    folders = client.get('/api/nodes').json()['items']
    moodboard = next(item for item in folders if item['name'] == 'Moodboard')
    image = client.get('/api/nodes', params={'parent': moodboard['id']}).json()['items'][0]
    download = client.get('/api/nodes/' + image['id'] + '/download')
    assert download.content.startswith(b'\x89PNG')


def test_samples_can_be_omitted_and_login_survives_restart(tmp_path):
    client = make(tmp_path)
    assert client.post('/api/local-setup', json={**BODY, 'samples': False}).status_code == 200
    assert client.get('/api/nodes').json()['items'] == []
    restarted = make(tmp_path)
    assert restarted.get('/api/status').json()['configured'] is True
    assert restarted.post('/api/login', json=BODY).status_code == 200
