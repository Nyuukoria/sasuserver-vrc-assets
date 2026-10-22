"""Sasu Drive: one private workspace, invited accounts, streamed local-disk storage."""
import asyncio
import hashlib
import hmac
import ipaddress
import mimetypes
import os
import secrets
import shutil
import sqlite3
import time
import unicodedata
import uuid
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

ROOT = Path(__file__).resolve().parent.parent
CHUNK = 8 * 1024 * 1024
SESSION_AGE = 7 * 86400


def uid():
    return uuid.uuid4().hex


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password):
    salt = secrets.token_hex(16)
    key = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1, dklen=64)
    return salt + ':' + key.hex()


def check_password(password, stored):
    salt, expected = stored.split(':', 1)
    key = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1, dklen=64)
    return hmac.compare_digest(key.hex(), expected)


def clean_name(value):
    value = unicodedata.normalize('NFC', value.strip())
    if not value or value in ('.', '..') or len(value.encode()) > 240 or any(c in value for c in '/\\') or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise HTTPException(400, 'Use a name without slashes or control characters (up to 240 bytes).')
    return value


def email_address(value):
    value = value.strip().lower()
    if len(value) > 254 or value.count('@') != 1 or not all(value.split('@')) or any(c.isspace() for c in value):
        raise HTTPException(400, 'Enter a valid email address.')
    return value


class Login(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=6, max_length=256)


class Join(Login):
    token: str = Field(min_length=20, max_length=200)
    name: str = Field(min_length=1, max_length=60)


class LocalSetup(Login):
    name: str = Field(min_length=1, max_length=60)
    samples: bool = True


class Invitation(BaseModel):
    email: str = Field(max_length=254)
    role: str = 'member'
    days: int = Field(default=7, ge=1, le=30)


class Folder(BaseModel):
    name: str = Field(max_length=240)
    parent: str | None = None


class EditNode(BaseModel):
    name: str | None = Field(default=None, max_length=240)
    parent: str | None = None
    move: bool = False


class Upload(BaseModel):
    name: str = Field(max_length=240)
    parent: str | None = None
    size: int = Field(ge=0, le=10_000_000_000_000)
    mime: str = Field(default='application/octet-stream', max_length=200)


class UserEdit(BaseModel):
    active: bool


class ProfileEdit(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    bio: str = Field(default='', max_length=500)
    theme_color: str = Field(default='', max_length=30)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=256)


def create_app(state_dir=None, storage_dir=None, origin=None, secure=None, local_test=None):
    local_mode = local_test if local_test is not None else os.environ.get('LOCAL_TEST_MODE') == '1'
    state = Path(state_dir or os.environ.get('STATE_DIR', ROOT / 'state')).resolve()
    storage = Path(storage_dir or os.environ.get('STORAGE_DIR', ROOT / 'data')).resolve()
    public_origin = (origin or os.environ.get('PUBLIC_ORIGIN', 'https://sasutendo.tech')).rstrip('/')
    secure_cookie = secure if secure is not None else os.environ.get('COOKIE_SECURE', 'true').lower() == 'true'
    capacity = int(os.environ.get('STORAGE_CAPACITY_BYTES', '4000000000000'))
    state.mkdir(parents=True, exist_ok=True)
    for part in ('objects', 'uploads'):
        (storage / part).mkdir(parents=True, exist_ok=True)

    database = state / 'drive.sqlite3'

    @contextmanager
    def db():
        connection = sqlite3.connect(database, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    with db() as con:
        con.executescript((ROOT / 'backend/schema.sql').read_text())
        # Additive migrations keep existing accounts, uploads and local test data.
        for table, column in [('users', 'avatar'), ('users', 'banner'), ('users', 'bio'), ('users', 'theme_color'), ('nodes', 'cover')]:
            if column not in {row['name'] for row in con.execute('PRAGMA table_info(' + table + ')')}:
                con.execute('ALTER TABLE ' + table + ' ADD COLUMN ' + column + ' TEXT')

    app = FastAPI(title='Nyuukoria Drive', docs_url=None, redoc_url=None, openapi_url=None)
    app.state.db = db
    app.state.storage = storage
    upload_locks = {}
    dummy_password = hash_password(secrets.token_urlsafe(32))

    def audit(con, user, action, name):
        con.execute('INSERT INTO activity(user_id,action,name,created) VALUES(?,?,?,?)', (user['id'], action, name, time.time()))

    def current_user(request, con, write=False, owner=False):
        token = request.cookies.get('sasu_session', '')
        row = con.execute('SELECT u.*, s.csrf FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>? AND u.active=1', (digest(token), time.time())).fetchone()
        if not row:
            raise HTTPException(401, 'Please sign in to your drive.')
        if request.method not in ('GET', 'HEAD'):
            if not hmac.compare_digest(request.headers.get('X-CSRF-Token', ''), row['csrf']):
                raise HTTPException(403, 'Your session needs refreshing. Reload the page and try again.')
        if owner and row['role'] != 'owner':
            raise HTTPException(403, 'Only the workspace owner can do that.')
        if write and row['role'] == 'viewer':
            raise HTTPException(403, 'Your invitation gives you read-only access.')
        return row

    def session(con, user_id):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        con.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
        con.execute('INSERT INTO sessions VALUES(?,?,?,?)', (digest(token), user_id, csrf, time.time() + SESSION_AGE))
        response = JSONResponse({'ok': True})
        response.set_cookie('sasu_session', token, max_age=SESSION_AGE, httponly=True, secure=secure_cookie, samesite='lax', path='/')
        return response

    def throttle(con, key, limit=8):
        now = time.time()
        con.execute('DELETE FROM attempts WHERE created<?', (now - 900,))
        count = con.execute('SELECT COUNT(*) FROM attempts WHERE key=?', (key,)).fetchone()[0]
        if count >= limit:
            raise HTTPException(429, 'Too many attempts. Please try again in 15 minutes.')
        con.execute('INSERT INTO attempts VALUES(?,?)', (key, now))

    def node(con, node_id, deleted=False):
        row = con.execute('SELECT * FROM nodes WHERE id=?', (node_id,)).fetchone()
        if not row or (row['deleted'] is not None and not deleted):
            raise HTTPException(404, 'This item is no longer available.')
        return row

    def parent_folder(con, parent):
        if parent and node(con, parent)['kind'] != 'folder':
            raise HTTPException(400, 'Choose a folder as the destination.')

    def can_change(con, item, user):
        if user['role'] == 'owner':
            return
        if user['role'] == 'viewer' or item['owner'] != user['id']:
            raise HTTPException(403, 'Only the uploader or workspace owner can change this item.')
        if item['kind'] == 'folder':
            foreign = con.execute('WITH RECURSIVE tree AS (SELECT id,owner FROM nodes WHERE id=? UNION ALL SELECT n.id,n.owner FROM nodes n JOIN tree t ON n.parent=t.id) SELECT 1 FROM tree WHERE owner<>? LIMIT 1', (item['id'], user['id'])).fetchone()
            if foreign:
                raise HTTPException(403, 'This folder contains someone else’s files. Ask the owner to move or remove it.')

    def view_node(con, item, user):
        result = dict(item)
        uploader = con.execute('SELECT name,avatar FROM users WHERE id=?', (item['owner'],)).fetchone()
        result['owner_name'] = uploader['name']
        result['owner_avatar'] = picture_url(uploader['avatar'])
        result['cover_url'] = picture_url(item['cover'])
        result['starred'] = bool(con.execute('SELECT 1 FROM stars WHERE user_id=? AND node_id=?', (user['id'], item['id'])).fetchone())
        if item['kind'] == 'folder':
            result['children'] = con.execute('SELECT COUNT(*) FROM nodes WHERE parent=? AND deleted IS NULL', (item['id'],)).fetchone()[0]
        return result

    @app.post('/api/auth/change-password')
    def change_password(body: PasswordChangeRequest, request: Request):
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            user = current_user(request, con, write=True)
            if not check_password(body.current_password, user['password']):
                raise HTTPException(400, 'Incorrect current password.')
            con.execute('UPDATE users SET password=? WHERE id=?', (hash_password(body.new_password), user['id']))
            audit(con, user, 'changed password', user['name'])
        return {'ok': True}

    @app.middleware('http')
    async def safeguards(request, call_next):
        if request.url.path.startswith('/api/') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            if request.headers.get('Origin') != public_origin:
                return JSONResponse({'detail': 'Request origin is not allowed.'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers.setdefault('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(sqlite3.IntegrityError)
    async def duplicate(request, error):
        return JSONResponse({'detail': 'An item with that name or email already exists.'}, status_code=409)

    @app.get('/health')
    def health():
        return {'ok': True}

    def is_loopback(request):
        try:
            return bool(request.client and ipaddress.ip_address(request.client.host).is_loopback)
        except ValueError:
            return False

    @app.get('/api/status')
    def status(request: Request):
        with db() as con:
            return {'configured': bool(con.execute('SELECT 1 FROM users WHERE role="owner"').fetchone()), 'local_test': bool(local_mode and is_loopback(request))}

    if local_mode:
        @app.post('/api/local-setup')
        def local_setup(body: LocalSetup, request: Request):
            if not is_loopback(request):
                raise HTTPException(403, 'Local setup is available only from this PC.')
            if len(body.password) < 6:
                raise HTTPException(400, 'Choose a password with at least 6 characters.')
            name, email = body.name.strip(), email_address(body.email)
            if not name:
                raise HTTPException(400, 'Enter your name.')
            hashed = hash_password(body.password)
            with db() as con:
                con.execute('BEGIN IMMEDIATE')
                if con.execute('SELECT 1 FROM users WHERE role="owner"').fetchone():
                    raise HTTPException(409, 'The local owner is already set up. Sign in with that account.')
                user_id = uid()
                con.execute('INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,"owner",?)', (user_id, email, name, hashed, time.time()))
                if body.samples:
                    from .demo import seed_samples
                    seed_samples(con, storage, user_id)
                return session(con, user_id)

    @app.post('/api/login')
    def login(body: Login, request: Request):
        email = email_address(body.email)
        key = digest((request.client.host if request.client else '') + ':' + email)
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            throttle(con, key)
            throttle(con, digest('login-ip:' + (request.client.host if request.client else '')), 40)
        with db() as con:
            user = con.execute('SELECT * FROM users WHERE email=? AND active=1', (email,)).fetchone()
            if not check_password(body.password, user['password'] if user else dummy_password) or not user:
                raise HTTPException(401, 'Email or password is incorrect.')
            con.execute('DELETE FROM attempts WHERE key=?', (key,))
            return session(con, user['id'])

    @app.get('/api/invite')
    def inspect_invite(token: str):
        with db() as con:
            invite = con.execute('SELECT * FROM invites WHERE token=? AND used IS NULL AND revoked=0 AND expires>?', (digest(token), time.time())).fetchone()
            if not invite:
                raise HTTPException(404, 'This invitation has expired, was revoked, or has already been used.')
            return {'email': invite['email'], 'role': invite['role'], 'expires': invite['expires']}

    @app.post('/api/join')
    def join(body: Join, request: Request):
        if len(body.password) < 6:
            raise HTTPException(400, 'Choose a password with at least 6 characters.')
        email, name = email_address(body.email), body.name.strip()
        if not name:
            raise HTTPException(400, 'Enter your name.')
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            throttle(con, digest('join:' + (request.client.host if request.client else '')), 20)
        hashed = hash_password(body.password)
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            invite = con.execute('SELECT * FROM invites WHERE token=? AND used IS NULL AND revoked=0 AND expires>?', (digest(body.token), time.time())).fetchone()
            if not invite or invite['email'].lower() != email:
                raise HTTPException(400, 'This invitation is invalid or belongs to another email address.')
            user_id, now = uid(), time.time()
            con.execute('INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,?,?)', (user_id, email, name, hashed, invite['role'], now))
            con.execute('UPDATE invites SET used=? WHERE id=?', (now, invite['id']))
            return session(con, user_id)

    @app.get('/api/me')
    def me(request: Request):
        with db() as con:
            user = current_user(request, con)
            return {
                **{key: user[key] for key in ('id', 'email', 'name', 'role', 'csrf', 'bio', 'theme_color')},
                'avatar_url': picture_url(user['avatar']),
                'banner_url': picture_url(user['banner'])
            }

    def picture_url(picture_id):
        return '/api/pictures/' + picture_id if picture_id else None

    @app.patch('/api/me')
    def edit_profile(body: ProfileEdit, request: Request):
        name = body.name.strip()
        bio = body.bio.strip()
        theme_color = body.theme_color.strip()
        if not name:
            raise HTTPException(400, 'Enter a display name.')
        with db() as con:
            user = current_user(request, con)
            con.execute('UPDATE users SET name=?, bio=?, theme_color=? WHERE id=?', (name, bio, theme_color, user['id']))
        return {'ok': True}

    async def picture_change(request, folder_id=None, remove=False, is_banner=False):
        with db() as con:
            user = current_user(request, con, write=bool(folder_id))
            if folder_id:
                item = node(con, folder_id)
                if item['kind'] != 'folder':
                    raise HTTPException(400, 'Only folders can have a cover.')
                can_change(con, item, user)
        content = None
        if not remove:
            from .pictures import normalize_picture
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > 8 * 1024 * 1024:
                    raise HTTPException(413, 'Choose an image smaller than 8 MB.')
            content = await run_in_threadpool(normalize_picture, bytes(data), bool(folder_id or is_banner))
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            user = current_user(request, con, write=bool(folder_id))
            if folder_id:
                item = node(con, folder_id)
                can_change(con, item, user)
            previous = item['cover'] if folder_id else (user['banner'] if is_banner else user['avatar'])
            picture_id = uid() if content else None
            if content:
                used = con.execute('SELECT COALESCE(SUM(size),0) FROM nodes WHERE kind="file"').fetchone()[0]
                pictures = con.execute('SELECT COALESCE(SUM(length(data)),0) FROM pictures').fetchone()[0]
                pending = con.execute('SELECT COALESCE(SUM(size),0) FROM uploads WHERE node_id IS NULL').fetchone()[0]
                if used + pictures + pending + len(content) > capacity:
                    raise HTTPException(507, 'The drive is full. Free some space first.')
                con.execute('INSERT INTO pictures(id,data) VALUES(?,?)', (picture_id, content))
            if folder_id:
                con.execute('UPDATE nodes SET cover=?,updated=? WHERE id=?', (picture_id, time.time(), folder_id))
            elif is_banner:
                con.execute('UPDATE users SET banner=? WHERE id=?', (picture_id, user['id']))
            else:
                con.execute('UPDATE users SET avatar=? WHERE id=?', (picture_id, user['id']))
            if previous:
                con.execute('DELETE FROM pictures WHERE id=?', (previous,))
        return {'url': picture_url(picture_id)}

    @app.post('/api/me/avatar')
    async def change_avatar(request: Request):
        return await picture_change(request)

    @app.delete('/api/me/avatar')
    async def remove_avatar(request: Request):
        return await picture_change(request, remove=True)

    @app.post('/api/me/banner')
    async def change_banner(request: Request):
        return await picture_change(request, is_banner=True)

    @app.delete('/api/me/banner')
    async def remove_banner(request: Request):
        return await picture_change(request, remove=True, is_banner=True)

    @app.post('/api/nodes/{node_id}/cover')
    async def change_cover(node_id: str, request: Request):
        return await picture_change(request, node_id)

    @app.delete('/api/nodes/{node_id}/cover')
    async def remove_cover(node_id: str, request: Request):
        return await picture_change(request, node_id, remove=True)

    @app.get('/api/pictures/{picture_id}')
    def picture(picture_id: str, request: Request):
        from fastapi.responses import Response
        with db() as con:
            current_user(request, con)
            row = con.execute('SELECT data FROM pictures WHERE id=? AND (EXISTS(SELECT 1 FROM users WHERE avatar=? OR banner=?) OR EXISTS(SELECT 1 FROM nodes WHERE cover=? AND deleted IS NULL))', (picture_id, picture_id, picture_id, picture_id)).fetchone()
            if not row:
                raise HTTPException(404, 'This picture is no longer available.')
            return Response(bytes(row['data']), media_type='image/webp', headers={'Content-Security-Policy': "default-src 'none'; sandbox"})

    @app.post('/api/logout')
    def logout(request: Request):
        with db() as con:
            current_user(request, con)
            con.execute('DELETE FROM sessions WHERE token=?', (digest(request.cookies.get('sasu_session', '')),))
        response = JSONResponse({'ok': True})
        response.delete_cookie('sasu_session', path='/', secure=secure_cookie, httponly=True, samesite='lax')
        return response

    @app.get('/api/admin')
    def admin(request: Request):
        with db() as con:
            current_user(request, con, owner=True)
            users = [{**dict(x), 'avatar_url': picture_url(x['avatar'])} for x in con.execute('SELECT id,name,email,role,active,created,avatar FROM users ORDER BY created')]
            invites = [dict(x) for x in con.execute('SELECT id,email,role,created,expires,used,revoked FROM invites ORDER BY created DESC')]
            return {'users': users, 'invites': invites}

    @app.post('/api/invites')
    def invite(body: Invitation, request: Request):
        if body.role not in ('member', 'viewer'):
            raise HTTPException(400, 'Choose member or viewer access.')
        with db() as con:
            user = current_user(request, con, owner=True)
            email = email_address(body.email)
            if con.execute('SELECT 1 FROM users WHERE email=?', (email,)).fetchone():
                raise HTTPException(409, 'That email already has an account. Manage it under Members.')
            token, now, invite_id = secrets.token_urlsafe(32), time.time(), uid()
            con.execute('INSERT INTO invites(id,token,email,role,created_by,created,expires) VALUES(?,?,?,?,?,?,?)', (invite_id, digest(token), email, body.role, user['id'], now, now + body.days * 86400))
            audit(con, user, 'invited', email)
            return {'id': invite_id, 'url': public_origin + '/?invite=' + token}

    @app.delete('/api/invites/{invite_id}')
    def revoke_invite(invite_id: str, request: Request):
        with db() as con:
            current_user(request, con, owner=True)
            con.execute('UPDATE invites SET revoked=1 WHERE id=?', (invite_id,))
            return {'ok': True}

    @app.patch('/api/users/{user_id}')
    def update_user(user_id: str, body: UserEdit, request: Request):
        with db() as con:
            current_user(request, con, owner=True)
            target = con.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            if not target or target['role'] == 'owner':
                raise HTTPException(400, 'The owner account cannot be disabled.')
            con.execute('UPDATE users SET active=? WHERE id=?', (int(body.active), user_id))
            con.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))
            return {'ok': True}

    @app.get('/api/stats')
    def stats(request: Request):
        with db() as con:
            current_user(request, con)
            disk = shutil.disk_usage(storage)
            used = con.execute('SELECT COALESCE(SUM(size),0) FROM nodes WHERE kind="file"').fetchone()[0]
            used += con.execute('SELECT COALESCE(SUM(length(data)),0) FROM pictures').fetchone()[0]
            pending = con.execute('SELECT COALESCE(SUM(offset),0) FROM uploads WHERE node_id IS NULL').fetchone()[0]
            counts = dict(con.execute('SELECT kind,COUNT(*) FROM nodes WHERE deleted IS NULL GROUP BY kind').fetchall())
            return {'used': used, 'pending': pending, 'capacity': min(capacity, disk.total), 'free': disk.free, 'files': counts.get('file', 0), 'folders': counts.get('folder', 0), 'members': con.execute('SELECT COUNT(*) FROM users WHERE active=1').fetchone()[0]}

    @app.get('/api/nodes')
    def list_nodes(request: Request, parent: str | None = None, view: str = 'files', q: str = '', offset: int = 0, limit: int = 200, sort: str = 'updated'):
        if offset < 0 or not 1 <= limit <= 1000:
            raise HTTPException(400, 'Invalid page size or offset.')
        with db() as con:
            user = current_user(request, con)
            conditions, args = ['n.deleted IS NULL'], []
            if view == 'trash':
                conditions = ['n.deleted IS NOT NULL', 'n.id=n.trash_root']
            elif view == 'starred':
                conditions.append('EXISTS(SELECT 1 FROM stars s WHERE s.node_id=n.id AND s.user_id=?)')
                args.append(user['id'])
            elif view == 'images':
                conditions += ['n.kind="file"', 'n.mime LIKE "image/%"']
            elif view == 'videos':
                conditions += ['n.kind="file"', 'n.mime LIKE "video/%"']
            elif view == 'audio':
                conditions += ['n.kind="file"', 'n.mime LIKE "audio/%"']
            elif view == 'archives':
                conditions += ['n.kind="file"', '(LOWER(n.name) LIKE "%.zip" OR LOWER(n.name) LIKE "%.rar" OR LOWER(n.name) LIKE "%.7z" OR LOWER(n.name) LIKE "%.unitypackage")']
            elif view != 'recent' and not q:
                parent_folder(con, parent)
                conditions.append('n.parent IS ?')
                args.append(parent)
            if q:
                conditions.append('instr(lower(n.name),lower(?))>0')
                args.append(q[:200])
            clause = ' AND '.join(conditions)
            total = con.execute('SELECT COUNT(*) FROM nodes n WHERE ' + clause, args).fetchone()[0]
            ordering = {'updated': 'n.updated DESC', 'created': 'n.created DESC', 'name': 'n.name COLLATE NOCASE', 'size': 'n.size DESC'}.get(sort, 'n.updated DESC')
            rows = con.execute('SELECT n.* FROM nodes n WHERE ' + clause + ' ORDER BY n.kind DESC,' + ordering + ',n.id LIMIT ? OFFSET ?', [*args, limit, offset]).fetchall()
            breadcrumbs, cursor = [], parent
            while cursor:
                folder = node(con, cursor)
                breadcrumbs.insert(0, {'id': folder['id'], 'name': folder['name']})
                cursor = folder['parent']
            return {'items': [view_node(con, x, user) for x in rows], 'breadcrumbs': breadcrumbs, 'limit': limit, 'total': total}

    @app.post('/api/folders')
    def create_folder(body: Folder, request: Request):
        with db() as con:
            user = current_user(request, con, write=True)
            con.execute('BEGIN IMMEDIATE')
            parent_folder(con, body.parent)
            name = clean_name(body.name)
            existing = con.execute('SELECT * FROM nodes WHERE parent IS ? AND name=? COLLATE NOCASE AND deleted IS NULL', (body.parent, name)).fetchone()
            if existing:
                if existing['kind'] != 'folder':
                    raise HTTPException(409, 'A file already uses that folder name.')
                return view_node(con, existing, user)
            now, node_id = time.time(), uid()
            con.execute('INSERT INTO nodes(id,parent,name,kind,owner,created,updated) VALUES(?,?,?,"folder",?,?,?)', (node_id, body.parent, name, user['id'], now, now))
            audit(con, user, 'created folder', name)
            return view_node(con, node(con, node_id), user)

    @app.patch('/api/nodes/{node_id}')
    def edit_node(node_id: str, body: EditNode, request: Request):
        with db() as con:
            user = current_user(request, con, write=True)
            con.execute('BEGIN IMMEDIATE')
            item = node(con, node_id)
            can_change(con, item, user)
            name = clean_name(body.name) if body.name is not None else item['name']
            parent = body.parent if body.move else item['parent']
            parent_folder(con, parent)
            cursor = parent
            while cursor:
                if cursor == node_id:
                    raise HTTPException(400, 'A folder cannot be moved inside itself.')
                cursor = node(con, cursor)['parent']
            con.execute('UPDATE nodes SET name=?,parent=?,updated=? WHERE id=?', (name, parent, time.time(), node_id))
            audit(con, user, 'updated', name)
            return view_node(con, node(con, node_id), user)

    @app.delete('/api/nodes/{node_id}')
    def trash_node(node_id: str, request: Request):
        with db() as con:
            user = current_user(request, con, write=True)
            con.execute('BEGIN IMMEDIATE')
            item = node(con, node_id)
            can_change(con, item, user)
            con.execute('WITH RECURSIVE tree(id) AS (SELECT ? UNION ALL SELECT n.id FROM nodes n JOIN tree t ON n.parent=t.id WHERE n.deleted IS NULL) UPDATE nodes SET deleted=?,trash_root=? WHERE id IN tree AND deleted IS NULL', (node_id, time.time(), node_id))
            audit(con, user, 'moved to trash', item['name'])
            return {'ok': True}

    @app.post('/api/nodes/{node_id}/restore')
    def restore(node_id: str, request: Request):
        with db() as con:
            user = current_user(request, con, write=True)
            con.execute('BEGIN IMMEDIATE')
            item = node(con, node_id, deleted=True)
            can_change(con, item, user)
            if item['trash_root'] != node_id:
                raise HTTPException(400, 'Restore the containing folder first.')
            if item['parent']:
                parent = node(con, item['parent'], deleted=True)
                if parent['deleted']:
                    raise HTTPException(409, 'Restore the parent folder first.')
            con.execute('UPDATE nodes SET deleted=NULL,trash_root=NULL WHERE trash_root=?', (node_id,))
            audit(con, user, 'restored', item['name'])
            return {'ok': True}

    @app.delete('/api/nodes/{node_id}/permanent')
    def purge(node_id: str, request: Request):
        with db() as con:
            user = current_user(request, con, owner=True)
            con.execute('BEGIN IMMEDIATE')
            item = node(con, node_id, deleted=True)
            if item['deleted'] is None or item['trash_root'] != node_id:
                raise HTTPException(400, 'Move this item to trash first.')
            all_rows = con.execute('WITH RECURSIVE tree AS (SELECT id,kind,cover FROM nodes WHERE id=? UNION ALL SELECT n.id,n.kind,n.cover FROM nodes n JOIN tree t ON n.parent=t.id) SELECT * FROM tree', (node_id,)).fetchall()
            tree = 'WITH RECURSIVE tree(id) AS (SELECT ? UNION ALL SELECT n.id FROM nodes n JOIN tree t ON n.parent=t.id) '
            if con.execute(tree + 'SELECT 1 FROM uploads WHERE node_id IS NULL AND parent IN tree LIMIT 1', (node_id,)).fetchone():
                raise HTTPException(409, 'Cancel unfinished uploads in this folder before deleting it permanently.')
            con.execute(tree + 'DELETE FROM stars WHERE node_id IN tree', (node_id,))
            con.execute(tree + 'DELETE FROM uploads WHERE parent IN tree OR node_id IN tree', (node_id,))
            con.execute('PRAGMA defer_foreign_keys=ON')
            con.execute(tree + 'DELETE FROM nodes WHERE id IN tree', (node_id,))
            for row in all_rows:
                if row['cover']:
                    con.execute('DELETE FROM pictures WHERE id=?', (row['cover'],))
            audit(con, user, 'permanently deleted', item['name'])
        for row in all_rows:
            if row['kind'] == 'file':
                (storage / 'objects' / row['id']).unlink(missing_ok=True)
        return {'ok': True}

    @app.post('/api/nodes/{node_id}/star')
    def toggle_star(node_id: str, request: Request):
        with db() as con:
            user = current_user(request, con)
            node(con, node_id)
            if con.execute('SELECT 1 FROM stars WHERE user_id=? AND node_id=?', (user['id'], node_id)).fetchone():
                con.execute('DELETE FROM stars WHERE user_id=? AND node_id=?', (user['id'], node_id))
                return {'starred': False}
            con.execute('INSERT INTO stars VALUES(?,?)', (user['id'], node_id))
            return {'starred': True}

    @app.post('/api/uploads')
    def start_upload(body: Upload, request: Request):
        with db() as con:
            user = current_user(request, con, write=True)
            con.execute('BEGIN IMMEDIATE')
            parent_folder(con, body.parent)
            name = clean_name(body.name)
            if con.execute('SELECT 1 FROM nodes WHERE parent IS ? AND name=? COLLATE NOCASE AND deleted IS NULL', (body.parent, name)).fetchone():
                raise HTTPException(409, 'An item already has that name. Rename your file before uploading.')
            if con.execute('SELECT 1 FROM uploads WHERE parent IS ? AND name=? COLLATE NOCASE AND node_id IS NULL', (body.parent, name)).fetchone():
                raise HTTPException(409, 'An upload with this name is already in progress. Resume or cancel it first.')
            used = con.execute('SELECT COALESCE(SUM(size),0) FROM nodes').fetchone()[0]
            used += con.execute('SELECT COALESCE(SUM(length(data)),0) FROM pictures').fetchone()[0]
            reserved = con.execute('SELECT COALESCE(SUM(size),0) FROM uploads WHERE node_id IS NULL').fetchone()[0]
            pending_bytes = con.execute('SELECT COALESCE(SUM(offset),0) FROM uploads WHERE node_id IS NULL').fetchone()[0]
            if used + reserved + body.size > capacity or body.size + reserved - pending_bytes > max(0, shutil.disk_usage(storage).free - 64 * 1024 * 1024):
                raise HTTPException(507, 'There isn’t enough free storage for this upload. Empty trash or cancel unfinished uploads.')
            upload_id, now = uid(), time.time()
            with (storage / 'uploads' / upload_id).open('xb'):
                pass
            mime = mimetypes.guess_type(name)[0] or body.mime
            con.execute('INSERT INTO uploads(id,user_id,parent,name,size,mime,created,updated) VALUES(?,?,?,?,?,?,?,?)', (upload_id, user['id'], body.parent, name, body.size, mime, now, now))
            return {'id': upload_id, 'offset': 0, 'chunk_size': CHUNK}

    def owned_upload(con, upload_id, user):
        upload = con.execute('SELECT * FROM uploads WHERE id=? AND (user_id=? OR ?="owner")', (upload_id, user['id'], user['role'])).fetchone()
        if not upload:
            raise HTTPException(404, 'Upload not found.')
        return upload

    @app.get('/api/uploads')
    def pending_uploads(request: Request):
        with db() as con:
            user = current_user(request, con)
            return [dict(x) for x in con.execute('SELECT id,name,size,offset,updated FROM uploads WHERE (user_id=? OR ?="owner") AND node_id IS NULL ORDER BY updated DESC', (user['id'], user['role']))]

    @app.get('/api/uploads/{upload_id}')
    def upload_status(upload_id: str, request: Request):
        with db() as con:
            user = current_user(request, con)
            upload = owned_upload(con, upload_id, user)
            return {'id': upload_id, 'offset': upload['offset'], 'size': upload['size'], 'node_id': upload['node_id']}

    @app.patch('/api/uploads/{upload_id}')
    async def upload_chunk(upload_id: str, request: Request):
        lock = upload_locks.setdefault(upload_id, asyncio.Lock())
        async with lock:
            with db() as con:
                user = current_user(request, con, write=True)
                upload = owned_upload(con, upload_id, user)
                parent_folder(con, upload['parent'])
                if upload['node_id']:
                    raise HTTPException(409, 'This upload is already complete.')
                try:
                    offset = int(request.headers.get('Upload-Offset', '-1'))
                except ValueError:
                    raise HTTPException(400, 'Invalid upload offset.')
                if offset != upload['offset']:
                    raise HTTPException(409, 'Upload offset changed. Resume from the server’s current offset.')
                expected_size = upload['size']
            temp = storage / 'uploads' / upload_id
            received = 0
            try:
                with temp.open('r+b') as stream:
                    stream.truncate(offset)
                    stream.seek(offset)
                    async for chunk in request.stream():
                        received += len(chunk)
                        if received > CHUNK or offset + received > expected_size:
                            raise HTTPException(413, 'Upload chunk exceeds the allowed size.')
                        await run_in_threadpool(stream.write, chunk)
                    await run_in_threadpool(stream.flush)
                    await run_in_threadpool(os.fsync, stream.fileno())
                with db() as con:
                    current_user(request, con, write=True)
                    con.execute('UPDATE uploads SET offset=?,updated=? WHERE id=?', (offset + received, time.time(), upload_id))
            except BaseException:
                with temp.open('r+b') as stream:
                    stream.truncate(offset)
                raise
            return {'offset': offset + received}

    @app.post('/api/uploads/{upload_id}/complete')
    async def complete_upload(upload_id: str, request: Request):
        lock = upload_locks.setdefault(upload_id, asyncio.Lock())
        async with lock:
            with db() as con:
                user = current_user(request, con, write=True)
                con.execute('BEGIN IMMEDIATE')
                upload = owned_upload(con, upload_id, user)
                if upload['node_id']:
                    return {'id': upload['node_id']}
                parent_folder(con, upload['parent'])
                temp = storage / 'uploads' / upload_id
                destination = storage / 'objects' / upload_id
                source = temp if temp.exists() else destination
                if upload['offset'] != upload['size'] or not source.is_file() or source.stat().st_size != upload['size']:
                    raise HTTPException(409, 'Upload is incomplete. Resume it before finishing.')
                node_id, now = upload_id, time.time()
                con.execute('INSERT INTO nodes(id,parent,name,kind,size,mime,owner,created,updated) VALUES(?,?,?,"file",?,?,?,?,?)', (node_id, upload['parent'], upload['name'], upload['size'], upload['mime'], user['id'], now, now))
                if source != destination:
                    os.replace(source, destination)
                con.execute('UPDATE uploads SET node_id=? WHERE id=?', (node_id, upload_id))
                audit(con, user, 'uploaded', upload['name'])
            upload_locks.pop(upload_id, None)
            return {'id': node_id}

    @app.delete('/api/uploads/{upload_id}')
    async def cancel_upload(upload_id: str, request: Request):
        lock = upload_locks.setdefault(upload_id, asyncio.Lock())
        async with lock:
            with db() as con:
                user = current_user(request, con, write=True)
                upload = owned_upload(con, upload_id, user)
                if upload['node_id']:
                    raise HTTPException(409, 'Use the file menu to remove a completed upload.')
                con.execute('DELETE FROM uploads WHERE id=?', (upload_id,))
            (storage / 'uploads' / upload_id).unlink(missing_ok=True)
        return {'ok': True}

    @app.get('/api/nodes/{node_id}/download')
    def download(node_id: str, request: Request, preview: bool = False):
        with db() as con:
            current_user(request, con)
            item = node(con, node_id)
            if item['kind'] != 'file':
                raise HTTPException(400, 'Open a folder to download its files.')
            file_path = storage / 'objects' / item['id']
            if not file_path.is_file():
                raise HTTPException(404, 'The file is missing from server storage. Contact the owner.')
            mime = mimetypes.guess_type(item['name'])[0] or 'application/octet-stream'
            safe_preview = mime in ('image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/avif', 'video/mp4', 'video/webm', 'audio/mpeg', 'audio/ogg', 'audio/wav')
            return FileResponse(file_path, filename=item['name'], media_type=mime if safe_preview else 'application/octet-stream', content_disposition_type='inline' if preview and safe_preview else 'attachment', headers={'Content-Security-Policy': "default-src 'none'; sandbox", 'Cache-Control': 'private, no-store'})

    @app.get('/api/activity')
    def activity(request: Request):
        with db() as con:
            user = current_user(request, con)
            return [dict(x) for x in con.execute('SELECT a.action,a.name,a.created,u.name AS actor FROM activity a LEFT JOIN users u ON a.user_id=u.id WHERE (?="owner" OR a.action<>"invited") ORDER BY a.id DESC LIMIT 30', (user['role'],))]

    app.mount('/', StaticFiles(directory=ROOT / 'web', html=True), name='web')
    return app


app = create_app()