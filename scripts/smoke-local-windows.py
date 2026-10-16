"""Exercise the bundled Windows runtime and real local HTTP server."""
import argparse
import http.cookiejar
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('zip', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        with zipfile.ZipFile(args.zip) as archive:
            archive.extractall(temp)
        root = Path(temp) / 'Sasu-Drive-Offline-Windows'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        # run-local accepts a ten-port search window.
        port = min(port, 65525)
        url = f'http://127.0.0.1:{port}'
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        process = subprocess.Popen([str(root / 'runtime/python.exe'), str(root / 'run-local.py'), '--no-browser', '--port', str(port)], cwd=root)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Bundled server exited before startup')
                try:
                    with opener.open(url + '/health', timeout=1) as response:
                        assert response.status == 200
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Bundled server did not start')
            csrf = ''
            def request(path, method='GET', body=None, raw=False, extra=None):
                headers = {'Origin': url, 'X-CSRF-Token': csrf, **(extra or {})}
                if isinstance(body, dict):
                    body = json.dumps(body).encode()
                    headers['Content-Type'] = 'application/json'
                req = urllib.request.Request(url + path, data=body, method=method, headers=headers)
                with opener.open(req, timeout=10) as response:
                    content = response.read()
                    return content if raw else json.loads(content)
            assert b'Make room for' in request('/', raw=True) or b'Sasu' in request('/', raw=True)
            assert request('/api/status')['local_test'] is True
            request('/api/local-setup', 'POST', {'name': 'Local tester', 'email': 'local@example.com', 'password': 'offline-test-password', 'samples': True})
            csrf = request('/api/me')['csrf']
            assert request('/api/stats')['files'] == 5
            upload = request('/api/uploads', 'POST', {'name': 'offline-test.txt', 'size': 3})
            request('/api/uploads/' + upload['id'], 'PATCH', b'abc', extra={'Upload-Offset': '0', 'Content-Type': 'application/octet-stream'})
            node = request('/api/uploads/' + upload['id'] + '/complete', 'POST')['id']
            assert request('/api/nodes/' + node + '/download', raw=True) == b'abc'
            invite = request('/api/invites', 'POST', {'email': 'friend@example.com'})
            assert invite['url'].startswith(url + '/?invite=')
            print('Portable Windows runtime: local setup, samples, upload, download and invitation passed.')
        finally:
            process.terminate()
            process.wait(timeout=15)


if __name__ == '__main__':
    main()
