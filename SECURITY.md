# Security

Enigma Hub downloads installers only from the configured official GitHub repositories, checks release SHA-256 digests, and requires a restart to apply Hub updates.

Report suspected vulnerabilities privately through GitHub's **Report a vulnerability** feature or contact the repository owner before opening a public issue containing exploit details or sensitive data.

Published Windows builds are currently unsigned. SHA-256 verifies file integrity and depends on the security of the GitHub release account. It does not replace an independent code-signing identity.

Dependency checks run weekly and on changes. They cover published package advisories and do not constitute a full audit of every native Qt component. Current Qt bindings ship Qt 5.15.2 on Windows.

Use the latest published release. Release 1.0.2 migrated the embedded Python runtime to Python 3.15 and rejected linked installer destinations. Release 1.1.0 extends those target checks to product operations and clears incomplete downloads on failure. Its file-verification feature compares the main executable to a locally recorded baseline; it is not a full application-directory or malware scan.
