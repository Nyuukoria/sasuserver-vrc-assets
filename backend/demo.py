"""Small, clearly labelled sample content, used only by explicit local-test setup."""
import io
import json
import struct
import time
import uuid
import zipfile
import zlib


def palette_png():
    colors = [(211, 151, 178), (240, 215, 222), (193, 177, 216), (183, 202, 181)]
    width, height = 640, 360
    row = b''.join(bytes(colors[min(3, x // 160)]) for x in range(width))
    raw = (b'\0' + row) * height
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def seed_samples(con, storage, owner_id):
    now = time.time()
    def folder(name, parent=None):
        node_id = uuid.uuid4().hex
        con.execute('INSERT INTO nodes(id,parent,name,kind,owner,created,updated) VALUES(?,?,?,"folder",?,?,?)', (node_id, parent, name, owner_id, now, now))
        return node_id
    def file(name, content, parent=None, mime='text/plain'):
        node_id = uuid.uuid4().hex
        (storage / 'objects' / node_id).write_bytes(content)
        con.execute('INSERT INTO nodes(id,parent,name,kind,size,mime,owner,created,updated) VALUES(?,?,?,"file",?,?,?,?,?)', (node_id, parent, name, len(content), mime, owner_id, now, now))
        return node_id
    welcome = folder('Start here')
    assets = folder('Avatar projects')
    worlds = folder('World ideas')
    images = folder('Moodboard')
    file('Welcome to your local drive.txt', b'This is the real Sasu Drive app, running only on your PC.\n\nTry uploading files or a folder, creating an invitation, starring a file, previewing an image, and restoring something from trash.\n\nThese are sample files, not real VRChat assets. Nothing is uploaded to an external server.\n', welcome)
    file('Cozy room checklist.md', b'# A cozy little world\n\n- [ ] Warm lighting\n- [ ] A place for plushies\n- [ ] Rain at the window\n- [ ] Test the video player\n', worlds, 'text/markdown')
    file('Palette.png', palette_png(), images, 'image/png')
    file('Project notes.json', json.dumps({'type':'sample only', 'ideas':['avatars','worlds','textures'], 'version':1}, indent=2).encode(), assets, 'application/json')
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr('Sample project/README.txt', 'Sample archive for testing downloads. This is not a Unity project.\n')
        zipped.writestr('Sample project/notes/ideas.txt', 'A little space for your next idea.\n')
    starred = file('Sample project.zip', archive.getvalue(), assets, 'application/zip')
    con.execute('INSERT INTO stars VALUES(?,?)', (owner_id, starred))
