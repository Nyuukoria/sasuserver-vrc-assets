"""Assemble an offline Windows x64 test bundle from verified Python and wheels."""
import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
PYTHON_SHA256 = '97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297'


def extract(archive, destination):
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            target = (destination / entry.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError('Unsafe archive entry')
        source.extractall(destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python-zip', type=Path, required=True)
    parser.add_argument('--wheels', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.python_zip.read_bytes()).hexdigest() != PYTHON_SHA256:
        raise SystemExit('Python archive does not match the official Python 3.13.16 x64 checksum.')
    wheels = sorted(args.wheels.glob('*.whl'))
    if len(wheels) < 15:
        raise SystemExit('Dependency wheels are missing; see docs/LOCAL-TEST.md.')
    with tempfile.TemporaryDirectory() as temp:
        bundle = Path(temp) / 'Sasu-Drive-Offline-Windows'
        bundle.mkdir()
        for directory in ('backend', 'web'):
            shutil.copytree(ROOT / directory, bundle / directory, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('run-local.py', 'START-WINDOWS.bat', 'requirements.txt'):
            shutil.copy2(ROOT / name, bundle / name)
        shutil.copy2(ROOT / 'docs/LOCAL-TEST.md', bundle / 'README-OFFLINE.txt')
        extract(args.python_zip, bundle / 'runtime')
        (bundle / 'runtime/python313._pth').write_text('python313.zip\n.\n..\n../vendor\n', encoding='utf-8')
        for wheel in wheels:
            extract(wheel, bundle / 'vendor')
        manifest = ['Python 3.13.16 Windows x64, https://www.python.org/downloads/release/python-31316/', 'Python archive SHA-256: ' + PYTHON_SHA256, '', 'Dependency wheel SHA-256:']
        manifest += [hashlib.sha256(w.read_bytes()).hexdigest() + '  ' + w.name for w in wheels]
        (bundle / 'DEPENDENCY-SOURCES.txt').write_text('\n'.join(manifest) + '\n', encoding='utf-8')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(bundle.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(bundle.parent))
    print(args.output.resolve())
    print('SHA-256: ' + hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
