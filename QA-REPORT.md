# Enigma Hub 1.3.1 setup recovery verification

Date: 2026-11-21 (client time).

- Reproduced the missing prerequisite: an unregistered Output copy could offer a product update although no supported Hub was installed.
- Product install/update now checks the registered installation marker and actual Hub executable version before downloading or starting a worker. Six-language messages explain installing Hub with EnigmaHubSetup.exe and reopening it from Start.
- Cube 3.3.1 quiet setup returns a normal failure even when stderr is None or unusable. The original error is saved locally; Hub displays a fresh setup error rather than just exit code 1.
- 66 Hub tests and 247 Cube tests passed, including the new prerequisite and missing-stderr regressions.
- On the affected PC, Hub 1.3.0 was installed normally. Retrying the real Cube update through Hub succeeded: 3.2.1 to 3.3.0 in the previously selected installation folder, with SHA-256 verification and refreshed Hub state.

## Previous 1.3.0 ecosystem verification

Date: 2026-11-21. Windows x64; Python 3.15 / PyQt5; .NET SDK 10.0.401.

- 64 Hub tests passed, including live loopback ticket validation, replay/wrong-product rejection, exact executable process detection, custom-path routing, tray actions, safe quitting and forwarding product launch requests to an already running Hub.
- The complete Cube suite passed: 245 tests, including the changed settings action and packaged launch/update behavior.
- The real C# HubLink source passed version/endpoint checks. Cross-process Python/C# checks accepted a Disk ticket and rejected replay and Cube tickets.
- Hub 1.3.0, Cube 3.3.0 and Disk 2.1.0 application/installers built successfully. Disk's installer built without compiler warnings; app restore reported NU1900 because the sandbox could not fetch NuGet advisory data.
- Real packaged Cube and Disk processes consumed Hub tickets, opened visible windows, continued running after the broker was shut down, and exited cleanly. Cube used an isolated data profile. No existing product install was replaced; no scan or timer was started. No Disk scheduled task was present or modified.
- Release coordination and recovery requirements are recorded in [ECOSYSTEM.md](ECOSYSTEM.md). The dependent product releases must follow Hub 1.3.0, not precede it.

## Previous 1.2.3 verification

Date: 2026-11-19. Environment: Windows 11 x64, Python 3.15.0, PyQt5 5.15.11 / Qt 5.15.2.

## Results

- 52 automated tests passed, covering navigation, settings, library, news, product version detection, downloads, cancellation, installation, rollback, removal and single-instance startup.
- 22 interface checks passed separately at Qt scale factors 1.25 and 1.5. Layout tests cover 820/1040/1440-pixel window widths and six interface languages; all four settings sections are checked in every language.
- A real Hub 1.2.2 application payload from the verified public release was installed in a dedicated test directory, with a separate uninstall-registry key and uniquely named shortcut. The current installer implementation waited for its process to exit, upgraded it to the actual 1.2.3 executable and relaunched it. File hashes, installed version and registry version matched the new build.
- The compiled uninstaller removed the test Hub, preserved a control personal file and cleaned up its detached temporary executable. The test's registry entry, shortcut and test directory were then removed.
- Website, both studio game pages, Google Play and Hub support links returned HTTP 200.
- A scan of tracked text source for common credential/private-key patterns found no matches. GitHub CI also runs syntax checks, regression tests and the Python-package advisory audit.

## Fixed during this review

- Settings write failures are handled without an uncaught GUI exception, preserve the previous on-disk settings and show a readable error. UTF-8 BOM settings are accepted.
- Incomplete product/installer staging files are cleaned after network or copy failures.
- Failed Hub installation restores the previous executable files and registration. Partial registry writes are also rolled back.
- Hub-update cache paths reject links/junctions and invalid version paths. An update withdrawn from the feed no longer leaves a stale install button.
- Steam discovery reads the client's registered path and additional libraries; incomplete game downloads are not treated as ready installations. Invalid saved links/executables are rejected.
- Closing while background requests finish hides the window immediately. Reopening cancels the pending close and restores usable controls, while preserving a maximized window.
- Removal waits for the original installer process, tolerates brief file-handle teardown and cleans the detached helper. Quiet-mode recovery failures no longer hide the original installation error.

## Scope and remaining limitations

- The native lifecycle check used isolated registration/shortcut names and the current installer entry point with real old/new executable payloads. Normal user installations and their files were not replaced by the audit.
- Steam discovery was verified with controlled client/library manifests; launching purchased studio games through real store accounts was not exercised.
- This is not a clean-machine Windows 10/11 compatibility matrix, a penetration test or a complete audit of native Qt components. Advisory checks cover published Python-package advisories.
- Windows binaries remain unsigned, as previously agreed. SmartScreen reputation and publisher signing are separate from this functional verification.
