# Verification status

Updated: 2026-11-09, Asia/Yekaterinburg.

## Accepted scope

TDD is mandatory for executable changes; see `TESTING.md`, `AGENTS.md` and `.cursor/rules/tdd.mdc`. Existing migration boundaries now have synthetic characterization tests before further changes.

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
- Current local suite: 40 passing tests. The source-clean regression uses the real Debian cleanup target and checks that vendor checksums survive while ordinary temporary files are removed.
- Workstation Arc A770: `vainfo` initialized the Intel iHD driver successfully and reported video-decoding entrypoints. `glxinfo -B` reported direct, accelerated rendering. These are driver checks, not NullWire playback acceptance.
- Local browser access through Kimi WebBridge works. The user logged in to Telegram Core.
- NullWire's API-application form was filled. Telegram returned `Too many attempts. Please try again later.` on submission; API credentials have not been issued. A second submission was made only after the user explicitly requested refilling the form, with the public GitHub URL; it returned the same limit. Registration is now paused; no further automatic attempts. The portal has not supplied a cooldown duration. The user later reported that a separate browser agent also received the same error after one submission, without retries or network changes; no API identity was obtained.
- Isolated OBS source build `7.4.1-obs3.test10` succeeded at source revision `2c1100f5c8355efc1748fc2c235c5f33`, expanded build revision `ed8cb5685c0de537d48429e0c27042d3`. Earlier Red/Green fixes cover dependency cleanup, binding generation, gperf, QSB, Qt 6.10 accessibility, disabled Thanos renderer, LTO and debug-section size.
- Exact artifact `nullwire-buildtest_7.4.1-obs3.test10_amd64.deb` has SHA-256 `bc988fc54c28a60eda7aca111e73fb664498ee1fea258df2176236a803569ca8`. In a clean Ubuntu 26.04 container it installed with dependencies, passed desktop/link checks, opened an 818x642 viewable offline window with an isolated profile and no GPU, then removed and reinstalled successfully. Its hash was unchanged after verification.

## Not complete

- Production API identity and its private build-time injection route.
- Source-build test inputs and results are recorded in `.state/source-buildtest/submission.json`; this package uses a limited test identity and cannot be released to stable, used for login or used for migration.
- The first solver result was ambiguous between the ordinary and extra FFmpeg runtime variants. Dedicated staging build preferences now select `libavcodec62`, `libavfilter11` and `libavformat62`, preserving other project configuration.
- Actual GPU video playback and authenticated Telegram functionality. The successful offline window check proves neither hardware decoding nor authenticated operation.
- Stable publication and production APT installation on the workstation.
- Verified profile backup and migration. The initial archive verification failed after the Snap client was opened under its different executable name. The process guard now detects both names, with regression tests. The original Snap profile remains in place and no native profile was installed by that attempt. The archive is private and must not be treated as verified.
- Hourly trigger setup. No Telegram cron entry was installed.

The experimental server-side controller was stopped when the source-build scope changed. No source build or GUI verification may run there. The earlier preparation left a separate project directory and tagged verifier/controller images; this record does not describe them as a deployed production service.
