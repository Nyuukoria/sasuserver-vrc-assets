# Try the website on your PC

This starts the actual Nyuukoria Drive app locally, with working uploads, folders,
accounts, previews and invitations. It is for trying the website before hosting.

## Windows offline download

1. Download and **extract all** of `Nyuukoria-Drive-Offline-Windows.zip` to a normal folder.
2. Open the extracted folder and double-click **START-WINDOWS.bat**.
3. Your browser opens at **http://127.0.0.1:8765** (or the next available port).
4. Choose your local name, email and password. The email is just a login;
   no email is sent. Leave sample content checked to see populated folders.

Keep the console window open while using the website. Close it to stop.
Run the same launcher to return later. Your test data remains in `local-test-data`.
To reset the test, stop the app and rename that folder before launching again.

The complete Windows x64 ZIP includes Python and dependencies. After downloading
and extracting it, no internet, Python installation, Docker, domain or server is needed.
The app uses system fonts and bundled icons and artwork. The launcher does not install anything.
The 20 GB test limit is a ceiling, not a reservation of disk space.

Only this PC can connect. To test an invitation, create one from Members and open
it in a private/incognito browser window **on the same PC**. It cannot be used by
friends on other devices until the real server is set up.

## From source (Windows, macOS or Linux)

With Python 3.12 or newer installed:

```sh
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# macOS/Linux:
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run-local.py
```

On Windows, `START-WINDOWS.bat` also handles source-only setup. That version needs
internet for its first dependency installation. The complete offline ZIP does not.

## Later, on the real server

Follow [DEPLOY.md](DEPLOY.md) using Docker Compose. Local mode is off by default;
its browser account-creation route is absent from the normal server app. Create
the real owner using the server console and invite other people normally.
The launcher uses separate test files and never changes DNS or the live website.
The sample content is not deployed. Local accounts and test files do not migrate
automatically: upload the files you want to keep after configuring the real server.

## Rebuild the portable download

Download Python 3.13.16's Windows x64 embeddable ZIP from the official release
page. `scripts/build-offline-windows.py` checks its published SHA-256. Download
the Windows dependency wheels into a separate directory:

```sh
python -m pip download --dest wheels --platform win_amd64 --python-version 313 --implementation cp --abi cp313 --only-binary=:all: -r requirements.txt colorama==0.4.6
python scripts/build-offline-windows.py --python-zip python-3.13.16-embed-amd64.zip --wheels wheels --output offline-output/Nyuukoria-Drive-Offline-Windows.zip
```

Third-party licenses are included with the runtime and dependency metadata.

## Updating an existing local test

Stop the previous launcher before updating. Extract the new ZIP to a new folder,
then copy your entire `local-test-data` folder from the old extracted app into the
new one before launching. Your accounts, files and folders will carry over. Keep
the old folder as a backup until you have checked the new version.

## Pictures and navigation

Click your avatar or the profile button to update your display name and picture.
Open a folder's details with its three-dot button to set or remove a cover image.
Profile and cover uploads accept PNG/JPG/WebP/GIF up to 8 MB and 16 megapixels;
animated pictures use their first frame. General file uploads accept all types,
including videos. Browser previews depend on the browser's supported codecs;
the original file can always be downloaded.

Use back/up buttons, clickable breadcrumbs, and browser back/forward to navigate.
`/` focuses search, `Alt + Up` opens the parent folder, and `Ctrl/Cmd + A` selects
the currently loaded items. The sort menu applies to the complete result set.
The default theme is dark; a light preference is remembered when you switch.
