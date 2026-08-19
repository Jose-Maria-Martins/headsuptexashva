# Security Policy

## Supported versions

This is a local research demo. Only the latest `main` branch receives fixes.

## Reporting

If you discover a security issue (e.g., unsafe defaults in the Flask demo exposed to a network), please report privately to the repository maintainers rather than opening a public issue.

## Known limitations

- The Flask UI uses global in-memory state and enables debug mode when run via `python ui/app.py` — **not suitable for public deployment** without hardening (see IMPROVEMENT_PLAN.md).
- Do not expose the debugger on `0.0.0.0` outside trusted local networks.
