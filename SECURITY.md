# Security Policy

## Supported Versions

This repository is currently maintained from the default branch.

## Reporting a Vulnerability

Please do not open a public issue for vulnerabilities involving credentials, unsafe file handling, prompt injection, data leakage, or remote execution risk.

Report security concerns privately to the repository maintainer through GitHub.

## Secret Handling

Do not commit:

- `.env` files;
- API keys;
- OAuth tokens;
- Redis credentials;
- Google service-account files;
- SSH keys;
- private certificates;
- local databases or vector stores containing private documents.

Use `.env.example` for placeholders only.
