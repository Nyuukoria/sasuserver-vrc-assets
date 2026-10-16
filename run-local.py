"""Launch an isolated loopback-only test instance, without Docker or hosting."""
import argparse
import os
from pathlib import Path
import socket
import threading
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='Run Sasu Drive privately on this PC.')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65525:
        parser.error('Choose a port between 1024 and 65525.')
    listener = None
    for port in range(args.port, args.port + 10):
        candidate = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            candidate.bind(('127.0.0.1', port))
            candidate.listen(128)
            listener = candidate
            break
        except OSError:
            candidate.close()
    if listener is None:
        raise SystemExit('The local test ports are busy. Close the previous Sasu Drive window and try again.')
    url = f'http://127.0.0.1:{port}'
    os.environ.update({
        'PUBLIC_ORIGIN': url,
        'COOKIE_SECURE': 'false',
        'LOCAL_TEST_MODE': '1',
        'STATE_DIR': str(ROOT / 'local-test-data' / 'state'),
        'STORAGE_DIR': str(ROOT / 'local-test-data' / 'files'),
        'STORAGE_CAPACITY_BYTES': '20000000000',
    })
    try:
        import uvicorn
        from backend.app import app
    except ImportError as error:
        listener.close()
        raise SystemExit('Runtime dependencies are missing. Use the complete offline Windows ZIP, or install requirements.txt first.\n' + str(error))
    print('\nSasu Drive - local test\n')
    print('Open: ' + url)
    print('Test files: ' + str(ROOT / 'local-test-data'))
    print('Only this PC can connect. The test storage limit is 20 GB.')
    print('Create your local owner account in the browser on first launch.')
    print('Keep this window open. Press Ctrl+C to stop.\n')
    if not args.no_browser:
        def open_when_ready():
            for _ in range(60):
                try:
                    # Never route a local health check through an inherited HTTP proxy.
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                    with opener.open(url + '/health', timeout=1) as response:
                        if response.status == 200:
                            webbrowser.open(url)
                            return
                except OSError:
                    time.sleep(.25)
        threading.Thread(target=open_when_ready, daemon=True).start()
    config = uvicorn.Config(app, host='127.0.0.1', port=port, workers=1, proxy_headers=False, access_log=False, log_level='warning')
    try:
        uvicorn.Server(config).run(sockets=[listener])
    finally:
        listener.close()


if __name__ == '__main__':
    main()
