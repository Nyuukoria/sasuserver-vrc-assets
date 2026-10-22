# Nyuukoria Drive

A private home for avatar assets, worlds, folders, and everything else your invited
circle makes. Built for **sasutendo.tech**, hosted on your own storage VPS.

A dark interface with rose accents and an optional light theme, a responsive sidebar, list/grid
views, live storage usage, and a calm empty state. There is no public sign-up and
no public file sharing.

## What works

- Profile pictures, animated GIFs, banners, bios, display names, folder covers, and uploader avatars with upload times.
- File and folder comments: members can post and remove their own comments; the owner can moderate; viewers can read.
- Back/up navigation, browser history, media collections, image thumbnails, and server-side sorting.

- Owner-created, email-bound, single-use invitation links with expiration and revocation.
- Owner, member (browse/upload), and viewer (browse/download) accounts.
- Shared workspace: all active invitees can see all workspace files. This version
  does **not** offer isolated per-person drives or per-folder sharing permissions.
- Whole-folder uploads with nested paths, drag-and-drop, individual files of any
  extension, two concurrent transfers, 8 MiB chunks, pause/cancel, retries, and
  resume by selecting the same file and destination again after reconnecting.
- Folder creation, file downloads, rename/move, search, pagination, personal stars,
  images/assets collections, recent activity, trash, restore, owner-only permanent deletion.
- Safe in-browser previews for common images, MP4/WebM video, and MP3/OGG/WAV audio.
  HTML, SVG, scripts, and other active file types download as attachments.
- Member disabling immediately revokes active sessions. Password recovery happens
  from the server console. The initial owner can only be created from that console.
- Local filesystem storage with SQLite metadata; Docker Compose + Caddy HTTPS.

## Updating the running server

After merging changes into `main`, run these commands from the repository directory:

```sh
git pull --ff-only origin main
sudo docker compose up -d --build --force-recreate drive
sudo docker compose ps drive
sudo docker compose logs --tail=50 drive
```

This rebuilds the app and bundled frontend. The existing `app_state` volume keeps
accounts, profiles, pictures and comments; the storage bind mount keeps uploads.
Caddy can keep running for an app-only update. Reload the browser after deployment.
The former offline launcher, sample content and browser owner-setup mode have
been removed. The server-console owner setup and password recovery remain available.

## Put it online

Follow **[the step-by-step server guide](docs/DEPLOY.md)**. The short version is:

1. Get a compatible Ubuntu 24.04 VPS and mount its large storage disk.
2. Install Docker Engine and the Compose plugin.
3. Clone this repo on the server and fill in `.env` from `.env.example`.
4. Point the old domain to the VPS, with the Cloudflare records set to **DNS only**.
5. Run `docker compose up -d --build`.
6. Create your owner account using `docker compose exec drive python -m backend.manage create-owner`.
7. Sign in at `https://sasutendo.tech`, then **People & invites → Create invitation**.

The website and uploads run on the VPS. This project is **not** a Cloudflare Pages
app; Pages cannot store a 4 TB local filesystem or run this Python server.
The separate `nyuukoria.tech` personal website and its Pages/KV setup are untouched.

## Development checks

Python 3.12 is the tested version. Install `requirements-dev.txt` in a virtual
environment before running the backend checks. No frontend build is required.

```sh
python -m pytest -q
npm ci
npm test
npm run check
```

Node is needed only for the frontend DOM tests, not for the app or server deployment.
GitHub Actions checks backend behavior, frontend wiring, Compose configuration,
and Docker image building.

## How it stores your files

The database lives on the fast boot disk in Docker volume `app_state`; uploaded
content lives on the HDD bind mount. Files are stored as opaque IDs beneath
`objects/`; incomplete transfers live in `uploads/`. Folder names and the mapping
between files and IDs are in SQLite. Do not move arbitrary files directly into
`objects/`; upload them through the app. Back up **both** the database and HDD data.

Passwords use salted scrypt hashes. Sessions and invitation tokens are hashed in
the database; cookies are Secure, HttpOnly, and SameSite=Lax. Requests that change
state check the public origin and a session CSRF token. All file/API routes require
an active session, except login, invite acceptance/inspection, and the configured
status flag. User content is never served from the public static web directory.

Invites prove possession of the private invite link and require the specified email
when choosing the account; this version does not send verification emails or offer
email delivery/reset flows. You copy and send invitations privately yourself.

## Operational limits

- Run exactly **one Uvicorn worker / one app replica**: chunk locks are in-process.
  This is intentional for a small shared drive on one storage VPS.
- A paused/interrupted upload reserves its complete final size. Cancel it from
  **Unfinished uploads** to free that reservation. The owner can cancel any upload;
  members can only inspect/cancel their own.
- Select **the same source file** to resume. Browser resume matching uses name,
  path, size, and modification time; it is not a content-integrity proof. Do not
  substitute a different file with the same metadata.
- Folder selection uploads files and their nested paths. Empty folders are retained
  when dropped from a desktop browser; directory pickers cannot report empty
  folders. You can also create them with **New folder**.
- Downloads are authenticated individual files, with HTTP range support. Folder ZIP
  downloads, sync clients, public links, and per-folder ACLs are not implemented.
- This is an initial custom release. Automated tests cover access rules, invitation
  races, upload resume/chunk bounds, storage limits, and file lifecycle. A real VPS,
  Docker end-to-end run, and desktop/mobile browser upload smoke test are still
  required before relying on it as the only copy of important assets.
