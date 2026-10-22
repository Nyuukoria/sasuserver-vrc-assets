PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS pictures (id TEXT PRIMARY KEY, data BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE, name TEXT NOT NULL,
 password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('owner','member','viewer')),
 active INTEGER NOT NULL DEFAULT 1, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), csrf TEXT NOT NULL, expires REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS invites (
 id TEXT PRIMARY KEY, token TEXT NOT NULL UNIQUE, email TEXT NOT NULL, role TEXT NOT NULL,
 created_by TEXT NOT NULL REFERENCES users(id), created REAL NOT NULL, expires REAL NOT NULL,
 used REAL, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS nodes (
 id TEXT PRIMARY KEY, parent TEXT REFERENCES nodes(id), name TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('file','folder')), size INTEGER NOT NULL DEFAULT 0,
 mime TEXT NOT NULL DEFAULT 'application/octet-stream', owner TEXT NOT NULL REFERENCES users(id),
 created REAL NOT NULL, updated REAL NOT NULL, deleted REAL, trash_root TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS node_names ON nodes(COALESCE(parent,''),name COLLATE NOCASE) WHERE deleted IS NULL;
CREATE INDEX IF NOT EXISTS node_parent ON nodes(parent,deleted);
CREATE TABLE IF NOT EXISTS uploads (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), parent TEXT REFERENCES nodes(id),
 name TEXT NOT NULL, size INTEGER NOT NULL, mime TEXT NOT NULL, offset INTEGER NOT NULL DEFAULT 0,
 created REAL NOT NULL, updated REAL NOT NULL, node_id TEXT REFERENCES nodes(id)
);
CREATE TABLE IF NOT EXISTS stars (
 user_id TEXT NOT NULL REFERENCES users(id), node_id TEXT NOT NULL REFERENCES nodes(id),
 PRIMARY KEY(user_id,node_id)
);
CREATE TABLE IF NOT EXISTS activity (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT REFERENCES users(id), action TEXT NOT NULL,
 name TEXT NOT NULL, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (key TEXT NOT NULL, created REAL NOT NULL);
CREATE INDEX IF NOT EXISTS attempts_key ON attempts(key,created);

CREATE UNIQUE INDEX IF NOT EXISTS pending_upload_name ON uploads(COALESCE(parent,''),name COLLATE NOCASE) WHERE node_id IS NULL;

CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    body TEXT NOT NULL,
    created REAL NOT NULL,
    FOREIGN KEY(node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS comments_node_created ON comments(node_id,created,id);
