# Enigma Hub 1.2.3 verification

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
