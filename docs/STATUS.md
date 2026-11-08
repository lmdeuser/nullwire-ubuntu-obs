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
- Patches enabling the Linux default and changing the application name apply to exact 7.4.1 source with `--fuzz=0`. The source check fails on the original disabled default and passes on the patched source.
- Original NullWire artwork was rendered and applied to 19 application image resources in the scratch source tree.
- Upstream-pinned tg_owt (including submodules), TD E2E, tlottie, wallet-engine and RNNoise sources were fetched. Offline Rust resolution covered 225 packages. Rust 1.96.1 compiler, standard library and Cargo archives were checked against the official release manifest. Build preparation is local; compilation belongs in OBS.
- Public repository created through `gh` CLI: https://github.com/lmdeuser/nullwire-ubuntu-obs (public, main branch).
- Current local suite: 22 passing tests. The source-clean regression uses the real Debian cleanup target and checks that vendor checksums survive while ordinary temporary files are removed.
- Workstation Arc A770: `vainfo` initialized the Intel iHD driver successfully and reported video-decoding entrypoints. `glxinfo -B` reported direct, accelerated rendering. These are driver checks, not NullWire playback acceptance.
- Local browser access through Kimi WebBridge works. The user logged in to Telegram Core.
- NullWire's API-application form was filled. Telegram returned `Too many attempts. Please try again later.` on submission; API credentials have not been issued. A second submission was made only after the user explicitly requested refilling the form, with the public GitHub URL; it returned the same limit. Registration is now paused; no further automatic attempts. The portal has not supplied a cooldown duration. The user later reported that a separate browser agent also received the same error after one submission, without retries or network changes; no API identity was obtained.

## Not complete

- Production API identity and its private build-time injection route.
- Complete native source compilation and the isolated OBS build test. The offline source bundle and build-test recipe were assembled; `dpkg-source -x` unpacked the complete package and applied both patches, and the patched-source check passed. The build-test launcher isolates its profile under the user cache directory; it must not use a migrated production profile.
- Source test `7.4.1-obs3.test2` failed before Rust compilation: Debian cleanup removed checksummed `Cargo.toml.orig` vendor inputs. The issue was reproduced locally and fixed by excluding dependency sources from that cleanup.
- Isolated source package `nullwire 7.4.1-obs3.test3` was submitted to OBS staging package `nullwire-buildtest`, source revision `4b1a0d1633f3e91af5bc0b51c70eb33b`. Native compilation is not yet verified.
- The first solver result was ambiguous between the ordinary and extra FFmpeg runtime variants. Dedicated staging build preferences now select `libavcodec62`, `libavfilter11` and `libavformat62`, preserving other project configuration.
- Source-build test inputs and results are recorded in `.state/source-buildtest/submission.json`; this package cannot be released to stable.
- Exact source-built deb installation, GUI, removal/reinstallation and GPU playback checks.
- Stable publication and APT installation on the workstation.
- Verified profile backup and migration. The initial archive verification failed after the Snap client was opened under its different executable name. The process guard now detects both names, with regression tests. The original Snap profile remains in place and no native profile was installed by that attempt. The archive is private and must not be treated as verified.
- Hourly trigger setup. No Telegram cron entry was installed.

The experimental server-side controller was stopped when the source-build scope changed. No source build or GUI verification may run there. The earlier preparation left a separate project directory and tagged verifier/controller images; this record does not describe them as a deployed production service.
