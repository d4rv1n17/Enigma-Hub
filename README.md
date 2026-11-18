# Enigma Hub

Desktop launcher for Enigma Studio apps and games. Windows 10/11, per-user installation.

## Install

Download **EnigmaHubSetup.exe** from [Releases](https://github.com/d4rv1n17/Enigma-Hub/releases/latest). Setup lets you choose the installation folder and desktop shortcut. Remove Hub through Windows Settings → Apps. Product installations and personal preferences are preserved.

## Features

- Enigma Cube and Enigma Disk installation, launch, update, and removal.
- Verified downloads using official release SHA-256 digests.
- Local game launch and links to the official game pages and stores.
- Release news with an offline cache.
- English by default, plus Russian, Romanian, German, Spanish, and French.
- Optional interface animations and a startup intro.
- Hub updates download in the background. Restart from the update button to install the new version.
- Search the catalog and library; filter favorites and sort by recent launches or name.
- Connect an existing Cube or Disk installation without reinstalling it.
- Favorite products and keep a local history of launches, installations and updates.
- Read full release notes inside Hub with formatted Markdown.
- Verify the main installed executable against the baseline saved after a verified Hub installation. This does not check every application data file.
- Export local diagnostics without local installation paths; clean cached product installers without removing apps.
- Switch languages immediately, choose whether to show the startup intro, and navigate with Ctrl+1–5 / Ctrl+K.
- Opening Hub again activates the existing window instead of starting another instance.
- Per-monitor HiDPI awareness, fractional scaling and vector-rendered navigation icons, logos and decorative artwork.
- A persistent transfer panel shows downloaded bytes, average speed and estimated download time. Downloads can be cancelled before installation starts; incomplete files are removed.
- Preflight free-space checks before product downloads and installation.
- Home offers quick launch for the three most recently used products that are still installed.

## Development

Install Python 3.13+, install requirements.txt using pip, then run enigma_hub.py.

## Build a release

Create a virtual environment with Python 3.13 or newer, install requirements-build.txt, then run build_release.py. The Windows release is built with Python 3.15. Output/build-info.json records the runtime and package versions.

The Output directory contains EnigmaHub.exe, EnigmaHubSetup.exe, and SHA256SUMS.txt.

Increment VERSION in hub_update.py for each release. Publish a stable GitHub release tagged vMAJOR.MINOR.PATCH with EnigmaHubSetup.exe and SHA256SUMS.txt. Hub uses GitHub's SHA-256 release asset digest to verify the installer.

## Local data

Preferences and cached news live in %APPDATA%/EnigmaHub. Downloaded product installers are under downloads; Hub updates are under hub-updates. A failed Hub installation records update-error.log.

## Version 1.1.0

The website/GitHub edition has a unified graphite-and-yellow design, custom product artwork, searchable library, favorites, recent launches, local activity history, executable verification and diagnostics. News and the branded installer share the same visual style. Store packaging remains a separate future distribution channel.
