# Verification status

Updated: 2026-11-09, Asia/Yekaterinburg.

## Accepted scope

- Native Ubuntu 26.04 amd64 Debian package, distributed from the user's OBS project.
- Build Telegram Desktop from sources, with native hardware video decoding enabled by default on compatible hardware.
- Use the existing small server only as a lightweight OBS trigger. All compilation belongs in OBS; local tests run on the workstation.
- Use the name NullWire and an original black/green terminal-style icon.
- Document work in this checkout and publish the code in a public GitHub repository through the CLI.
- Migrate from Snap only after a working package and verified backup exist.

## Verified

- Current workstation: Ubuntu 26.04.1 amd64; installed Snap Telegram 7.4.0.
- Upstream stable release checked: Telegram Desktop 7.4.1.
- Upstream Linux archive SHA-256: `d845fea20988749617da7bd74d4144bd81e11c62dcf53e41681a980bf0413572`.
- Upstream full-source archive SHA-256: `b3d98d75961bf81c2752cec60bdd67a586960fbfca29e3ab473165e49de533d4`.
- OBS stable `home:dwolfF:telegram` exists with direct building disabled.
- OBS `home:dwolfF:telegram:staging` exists with publishing disabled.
- Historical binary repack `telegram-desktop 7.4.1-obs2` built successfully in staging after correcting Pango/Cairo build dependencies. It was not released.
- Source review identified upstream VA-API, VDPAU and CUDA selection, software fallback, and the disabled-by-default Linux video-decoding setting.
- A patch enabling the default on Linux applies to exact 7.4.1 source with `--fuzz=0`.
- Workstation Arc A770: `vainfo` initialized the Intel iHD driver successfully and reported video-decoding entrypoints. `glxinfo -B` reported direct, accelerated rendering. These are driver checks, not NullWire playback acceptance.
- Local browser access through Kimi WebBridge works. The user logged in to Telegram Core.
- NullWire's API-application form was filled. Telegram returned `Too many attempts. Please try again later.` on submission; API credentials have not been issued.

## Not complete

- Production API identity and its private build-time injection route.
- Source dependency packaging, complete native source compilation and OBS source build.
- Exact source-built deb installation, GUI, removal/reinstallation and GPU playback checks.
- Stable publication and APT installation on the workstation.
- Verified profile backup and migration. The initial archive verification failed after the Snap client was opened under its different executable name. The process guard now detects both names, with regression tests. The original Snap profile remains in place and no native profile was installed by that attempt. The archive is private and must not be treated as verified.
- Hourly trigger setup. No Telegram cron entry was installed.

The experimental server-side controller was stopped when the source-build scope changed. No source build or GUI verification may run there. The earlier preparation left a separate project directory and tagged verifier/controller images; this record does not describe them as a deployed production service.
