# Telegram OBS packaging

Read `/home/dennweiss/AGENTS.md` and `/home/dennweiss/.codex/AGENTS.md`.

- Scope: NullWire, an unofficial Telegram Desktop source build for Ubuntu 26.04 amd64. Enable hardware video decoding by default with software fallback; preserve user opt-out and licenses. Binary repacks are superseded and must not be released.
- Use `.state/` for private scratch and backups; never upload it. Build TMPDIR: `/srv/temp/telegram` locally; explicitly configured checkout `.state/tmp` on the VPS. Export TMPDIR before build tools.
- Stable `home:dwolfF:telegram` must not build directly. Release only exact staging artifacts that passed integrity, installation and offline visible-window tests. Staging publishing remains disabled.
- Missing/ambiguous upstream metadata, changed hashes or revisions, downgrades and failed checks must prevent publication.
- TDD is mandatory for executable behavior in packaging, controllers, source preparation, verification and migration: first run a relevant failing behavioral test, then implement, verify and refactor. Add characterization tests before modifying existing code; do not call later-added coverage historical TDD. See `docs/TESTING.md` and `.cursor/rules/tdd.mdc`.
- Run `python3 -m unittest discover -s tests -v` before every source upload. Use regression tests for material controller and packaging guards.
- User constraint: astra-n100 may run only a lightweight OBS build trigger. No compilation, package verification containers or GUI checks there. Build in OBS, test locally. Never publish API credentials or profile data. API registration is authorized in the local browser; user handles login.
- Stop only Telegram cron and wait for its active run before edits. Never edit executing scripts or run concurrent publishers.
- Profile migration must close Telegram, verify a private backup, refuse overwrites and preserve the Snap source profile. Never print tdata, credentials or raw private logs.
- Distinguish package tests, live window checks and verified authenticated functionality. Never send a Telegram message as a test without explicit permission.
