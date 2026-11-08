# Architecture and decisions

## Product

NullWire is an unofficial Telegram API client built from Telegram Desktop source. The first supported target is Ubuntu 26.04 amd64. Broader OS or CPU support has not been established. The product should remain compatible with Telegram's normal messaging, privacy and sponsored-message behavior.

The user chose a source build after learning that upstream Linux defaults hardware video decoding to off. A binary repack therefore no longer meets acceptance. The new default must not overwrite an existing user's deliberate opt-out.

## Hardware acceleration

Upstream 7.4.1 implements VA-API, VDPAU and CUDA hardware-device selection in `Telegram/SourceFiles/ffmpeg/ffmpeg_utility.cpp`. Availability depends on built codec support, runtime libraries, drivers, display-session access and codec/profile support. The upstream fallback must remain intact. No launcher should force a particular vendor, software rendering or an X11-only path on every installation.

Both a Linux desktop session and an offline test environment without a GPU must remain usable. Local tests should distinguish accelerated UI rendering, hardware video decoding and video-call encoding; none implies the others.

## Packaging and secrets

Publish packaging, patches, the original icon, source provenance and documentation. Do not publish `.state`, browser or OBS sessions, API identity values, or user profiles. The production build must inject its application identity privately. Telegram's sample identity is only suitable for build tests and cannot pass the release gate.

Upstream 7.4.1 also needs substantial build dependencies beyond Qt and FFmpeg, including tg_owt, TD E2E and the combined Rust bindings used by tlottie and wallet-engine. Their versions must be derived from the exact upstream release's build configuration, not current branch heads. Complete offline sources and license notices must be supplied for any bundled components.

## Responsibilities

OBS compiles. The lightweight external trigger checks metadata and starts builds. The workstation performs installation and real desktop/GPU acceptance. Stable receives only the exact tested staging artifact. A failed or incomplete gate leaves stable unchanged.

The historical repack pipeline remains for audit, with its CLI disabled and an additional release guard rejecting repacks, test API identities and an unenabled hardware-decoding default. Its old server-side Docker verifier route is superseded and must not be scheduled.

## Migration

Close all client processes, including the Snap executable's actual process name. Validate source and destination paths, refuse symlink escapes and an existing native profile, create a private backup, verify it, copy the profile and verify the copy. Preserve the source profile and rollback path. Only disable the old installation after the new client has passed acceptance.
