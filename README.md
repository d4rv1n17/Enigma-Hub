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

## Development

Install Python 3.13+, install requirements.txt using pip, then run enigma_hub.py.

## Build a release

Create a virtual environment with Python 3.13 or newer, install requirements-build.txt, then run build_release.py. The Windows release is built with Python 3.15. Output/build-info.json records the runtime and package versions.

The Output directory contains EnigmaHub.exe, EnigmaHubSetup.exe, and SHA256SUMS.txt.

Increment VERSION in hub_update.py for each release. Publish a stable GitHub release tagged vMAJOR.MINOR.PATCH with EnigmaHubSetup.exe and SHA256SUMS.txt. Hub uses GitHub's SHA-256 release asset digest to verify the installer.

## Local data

Preferences and cached news live in %APPDATA%/EnigmaHub. Downloaded product installers are under downloads; Hub updates are under hub-updates. A failed Hub installation records update-error.log.
