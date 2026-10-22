# Sasu Drive on HostBRR, step by step

This guide deploys the supplied repository on your VPS at **sasutendo.tech**.
It does not change **nyuukoria.tech** or the Pages project serving that website.

## 1. Order the server

Go to [HostBRR's Hybrid Storage VPS page](https://hostbrr.com/hybrid-storage-vps.html).
Select monthly billing and move the storage selector to **4**:

- **Hybrid 4TB**, Frankfurt, Germany
- 2 vCPUs / 4 GB RAM / 60 GB NVMe boot + 4 TB HDD
- Full root access and a dedicated IPv4 address
- Public configurator price checked 2026-10-16: **€10/month before VAT**

For more room, **Hybrid 8TB** was listed at **€20/month before VAT**, with 4 vCPUs,
8 GB RAM and 120 GB NVMe boot. Check the actual checkout total, stock and billing
terms. Use **Ubuntu 24.04 LTS**. Do not select a shared Storagebox or NAT-only plan
for this deployment. You do not need a paid database, object-storage service or API key.

## 2. Prepare the disk

Connect to your VPS using SSH. Identify the disks:

```sh
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,MODEL
findmnt
```

The 4 TB HDD volume must be mounted separately from the small NVMe boot disk.
Use `/mnt/sasu-storage` as its mount point, persist it in `/etc/fstab` by filesystem
UUID, and confirm that it is mounted again after reboot. On a new unformatted
volume, disk formatting and partitioning must be done against the **verified empty
storage device**. The boot device name is not safe to guess. If unsure, share the
`lsblk` output before formatting anything; this guide deliberately does not run
`mkfs` against a guessed `/dev/sdb` or `/dev/vdb`.

Once the HDD is correctly mounted:

```sh
findmnt --mountpoint /mnt/sasu-storage
sudo mkdir -p /mnt/sasu-storage/drive-files
sudo chown 10001:10001 /mnt/sasu-storage/drive-files
sudo chmod 750 /mnt/sasu-storage/drive-files
df -h /mnt/sasu-storage/drive-files
```

`df` must show the large storage filesystem, not the small `/` filesystem.
The app runs as UID/GID 10001 and needs write access to this directory. Do not
recursively change ownership of the entire server filesystem.

## 3. Install Docker

Follow [Docker Engine's official Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/),
including the **Docker Compose plugin**, and install Git if needed:

```sh
sudo apt-get update
sudo apt-get install -y git
sudo docker version
sudo docker compose version
```

The examples below use `sudo docker` so no Docker group changes are required.
Allow SSH and inbound TCP 80/443 in the HostBRR firewall and any OS firewall.
UDP 443 is optional for HTTP/3. Do not publish port 8000: only Caddy should be public.
If enabling a firewall, preserve SSH access before applying the rules.

## 4. Get the project and configure it

After merging the drive PR into the repository's default branch:

```sh
sudo mkdir -p /opt/sasu-drive
sudo chown "$USER":"$USER" /opt/sasu-drive
git clone https://github.com/Nyuukoria/sasuserver-vrc-assets.git /opt/sasu-drive
cd /opt/sasu-drive
cp .env.example .env
nano .env
```

Set these values:

```dotenv
DOMAIN=sasutendo.tech
ACME_EMAIL=your-own-email@example.com
DRIVE_STORAGE_PATH=/mnt/sasu-storage/drive-files
STORAGE_CAPACITY_BYTES=4000000000000
```

For an 8 TB plan use `8000000000000`. The capacity value is the app's total storage
limit, including trashed files and reservations for unfinished uploads; it does not
create physical disk space. Actual free space is also checked. The dashboard shows
the smaller of the configured capacity and the mounted filesystem's total size.

Keep `.env` private. Never enter a server password, invite token, or user password
into a GitHub issue or commit it to the repository.

## 5. Point the old domain at this server

If these old hostnames are still attached to your personal Pages project, detach
only `sasutendo.tech`, `www.sasutendo.tech`, and `admin.sasutendo.tech` from it and
remove their old Pages DNS records. Keep all `nyuukoria.tech` hostnames connected.

In **Cloudflare → sasutendo.tech → DNS**, set:

| Type | Name | Target | Proxy |
| --- | --- | --- | --- |
| A | `@` | Your VPS's public IPv4 address | **DNS only** (gray cloud) |
| CNAME | `www` | `sasutendo.tech` | **DNS only** (gray cloud) |

An AAAA record is optional: add it only if the server's IPv6 is configured and can
reach Caddy. Remove old conflicting A/AAAA/CNAME website records. Leave mail MX,
TXT and mail-related DNS records unchanged. This app uses `/` for the drive and
`People & invites` for administration; it does not require an `admin` subdomain.

Use **DNS only** initially so large file transfers go directly to your VPS.
Caddy handles trusted HTTPS certificates automatically using the domain and
`ACME_EMAIL`. There is no Cloudflare Worker or Pages deployment for this app.
Cloudflare proxying can be revisited later with its upload, timeout and caching
limits in mind; never cache authenticated API/file responses.

If old Worker routes, redirects or Cloudflare Access hostname rules still apply
to `sasutendo.tech`, inspect and remove only the rules belonging to the retired
personal website. Leave unrelated services and `nyuukoria.tech` rules untouched.

## 6. Start it and create the owner

```sh
cd /opt/sasu-drive
sudo docker compose config --quiet
sudo docker compose up -d --build
sudo docker compose ps
sudo docker compose logs --tail=80
sudo docker compose exec drive python -m backend.manage create-owner
```

Enter your email, display name and a password when prompted. Password entry is
hidden. There is no default admin password, public setup page, or public signup.
The command refuses to create another owner if one already exists.

Open **https://sasutendo.tech**, sign in using **your email and chosen password**,
then use **People & invites → Create invitation**. Enter your friend's email,
choose Member or Viewer access, and copy the link. Send it privately yourself;
the app does not automatically email it. Each link can be accepted once and only
for its assigned email. Membership is for the whole shared workspace.

## 7. Check the complete flow

Before uploading everything:

1. Sign in as the owner, create a folder, and upload a small file.
2. Refresh the browser, download the file, and compare its content with the original.
3. Upload a nested folder containing a `.unitypackage`, image and another file.
4. Start a larger file, pause it, refresh, and select the **same file** in the same
   folder. Confirm that it resumes and the final file matches the original.
5. Create an invitation. Accept it in a private browser window; confirm that the
   member can browse/upload and cannot invite others or edit your files.
6. Disable that member from the owner account and confirm their next API operation
   requires signing in again. Enable them if desired; their old session stays revoked.
7. Move a disposable test file to trash and restore it. Only the owner can empty
   individual trashed items permanently.
8. Restart the app with `sudo docker compose restart drive` and confirm accounts,
   folders and files persist. Check `df -h` to confirm uploads use the HDD.

Native folder picking is most reliable in current desktop browsers. Phones can
upload individual files through their system file picker; folder picker support
varies by browser and operating system.

## Updates and maintenance

```sh
cd /opt/sasu-drive
git pull --ff-only origin main
sudo docker compose up -d --build --force-recreate drive
sudo docker compose ps drive
sudo docker compose logs --tail=50 drive
```

Merge the desired pull request into `main` first. For app/frontend changes,
Caddy can stay running. The image includes `web/`, so rebuilding `drive` updates
banner and comment code too. Reload the browser; use Ctrl+F5 once if an older
script or stylesheet is still displayed. Accounts, profiles, pictures and comments
remain in `app_state`; uploaded files remain on the mounted storage disk.

Do not increase the Uvicorn worker count or run multiple app replicas. Chunk
serialization is designed for one application process on one VPS.

To recover an account password from the server:

```sh
sudo docker compose exec drive python -m backend.manage reset-password
```

To remove uploads inactive for over seven days:

```sh
sudo docker compose exec drive python -m backend.manage cleanup-uploads
```

This releases their reserved space; those transfers can no longer resume. Run it
only when no intended long-paused upload needs to be kept. The owner can also cancel
specific unfinished uploads from the website.

## Back up and restore

Use an independent backup destination. Both parts are required:

- the `app_state` volume (SQLite database, including folder/file mappings, users,
  invitations and sessions), and
- the mounted HDD's `drive-files/objects` content; include `uploads/` if transfers
  should survive the restore.

For a simple consistent backup, stop `drive` while taking the database and storage
snapshot/copy, then start it again. If copying a live SQLite database, use SQLite's
backup API rather than copying just the main `.sqlite3` file and ignoring its WAL.
Test restoration to an isolated instance with a different domain before relying on
it. Provider RAID-6 is disk redundancy; it is not a separate recoverable backup.
Ask HostBRR whether any backup add-on includes the **bulk HDD disk**, not only the
NVMe boot disk. Verify the restored HDD files and metadata belong to the same snapshot.

## If it does not open

- **HTTPS/certificate error:** check A/AAAA records, DNS propagation, TCP 80/443 and
  `sudo docker compose logs caddy`.
- **Container unhealthy/permission error:** check the HDD is mounted, the bind path
  exists, and the directory is writable by UID 10001.
- **Origin not allowed:** `.env` DOMAIN must match the hostname you opened. Use the
  apex `sasutendo.tech`; `www` redirects there.
- **Upload refused/storage full:** cancel old unfinished uploads or permanently
  delete disposable trash as the owner, then check disk usage and configured capacity.
- **Login throttled:** wait 15 minutes. Password resets use the console command above.
