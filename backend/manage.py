"""Owner bootstrap and password recovery run from an authenticated server shell."""
import argparse
import getpass
import time
from .app import app, email_address, hash_password, uid


def main():
    parser = argparse.ArgumentParser(description='Manage Sasu Drive from the server console.')
    parser.add_argument('command', choices=['create-owner', 'reset-password', 'cleanup-uploads'])
    args = parser.parse_args()
    db = app.state.db
    if args.command == 'cleanup-uploads':
        with db() as con:
            # Leave actively transferring uploads alone; only stale incomplete uploads expire.
            rows = con.execute('SELECT id FROM uploads WHERE node_id IS NULL AND updated<?', (time.time() - 7 * 86400,)).fetchall()
            for row in rows:
                con.execute('DELETE FROM uploads WHERE id=?', (row['id'],))
        for row in rows:
            (app.state.storage / 'uploads' / row['id']).unlink(missing_ok=True)
            (app.state.storage / 'objects' / row['id']).unlink(missing_ok=True)
        print(f'Removed {len(rows)} uploads inactive for more than seven days.')
        return
    email = email_address(input('Email address: '))
    name = input('Display name: ').strip() if args.command == 'create-owner' else None
    if name is not None and not 1 <= len(name) <= 60:
        raise SystemExit('Display name must have 1–60 characters.')
    password = getpass.getpass('Password (at least 10 characters): ')
    if len(password) < 10 or len(password) > 256:
        raise SystemExit('Password must have 10–256 characters.')
    if password != getpass.getpass('Repeat password: '):
        raise SystemExit('Passwords did not match.')
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        if args.command == 'create-owner':
            if con.execute('SELECT 1 FROM users WHERE role="owner"').fetchone():
                raise SystemExit('An owner already exists. Use reset-password for recovery.')
            con.execute('INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,"owner",?)', (uid(), email, name, hash_password(password), time.time()))
        else:
            user = con.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
            if not user:
                raise SystemExit('No account has that email address.')
            con.execute('UPDATE users SET password=? WHERE id=?', (hash_password(password), user['id']))
            con.execute('DELETE FROM sessions WHERE user_id=?', (user['id'],))
    print('Account created. You can sign in to your drive.' if name is not None else 'Password updated. Previous sessions have been signed out.')


if __name__ == '__main__':
    main()
