# Enigma ecosystem protocol 1

Release set: Hub 1.3.0, Cube 3.3.0, Disk 2.1.0. Deploy Hub first.

## Launch

Packaged interactive products consume `ENIGMA_HUB_ENDPOINT` and `ENIGMA_HUB_TICKET` from their child-process environment. The endpoint must be HTTP on literal `127.0.0.1` with path `/claim`, no credentials, query or fragment. Proxies are disabled. A product POSTs a bounded JSON `{ "product": "cube|disk", "ticket": "..." }`. Hub stores random 256-bit tickets only in memory, bound to one product for 90 seconds, and consumes them once. It has no HTTP launch or filesystem command. This is local integration, not a DRM/security boundary against the Windows user.

A direct launch without a valid ticket opens the installed, supported Hub with `--product cube|disk --action launch --product-exe <absolute exe>` and exits. Hub forwards bounded newline-framed JSON to its single-instance local socket. Only known product ids/actions and regular, absolute, correctly named executable paths are accepted. Supplied paths reject symlinks/junctions. Paths with spaces are argument-list entries, never shell code. The library adopts an existing custom install path without reinstalling it. `--action updates` opens Hub update management; `open` opens the library.

Clients require an installation marker identifying Hub >=1.3.0. Missing or outdated Hub produces a recovery message. Source development is independent (Python source / .NET Debug); solver, scheduled snapshot and uninstall entry points are separate maintenance paths.

## Lifecycle and updates

Hub supplies the ticket and owns version checks and verified downloads. Packaged products do not use their legacy self-updaters. Scheduled Disk snapshots remain offline Windows tasks and block replacement while running. Before updating/removing, Hub checks the exact executable process path, including externally launched instances; it repeats the check after a download. Installers refuse to force-close products. Windows file locks remain the final replacement safeguard.

Hub can close to a quick-launch tray while a product it started is running. Quit Hub never kills children. Ticket verification occurs only at startup: Hub exit/crash does not interrupt ongoing work. Disk also has a per-user single-instance mutex and current-user-only activation pipe.

## Release and recovery

1. Build and verify all three products, preserving existing profiles.
2. Publish/install Hub 1.3.0 before making the dependent product releases current.
3. Publish Cube 3.3.0 and Disk 2.1.0 with asset SHA-256 digests.
4. An old Hub must be updated/restarted before installing these product builds. Already installed old Cube/Disk versions keep their previous behavior until updated.
5. Uninstalling Hub leaves product files and personal data. Dependent products need Hub restored to launch again. No account, online entitlement, telemetry or process-termination watchdog is introduced.
