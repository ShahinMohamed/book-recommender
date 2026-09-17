# Security policy

Please report vulnerabilities privately through GitHub's security advisory
feature. Do not open a public issue with secrets, credentials, personal reading
history, or an exploit proof of concept.

Supported releases are the latest commit on `main`. Rotate `SECRET_KEY` and the
PostgreSQL password before deployment, terminate TLS at a trusted reverse proxy,
and keep PostgreSQL off the public network.
