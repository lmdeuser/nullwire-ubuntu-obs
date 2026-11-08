# TDD policy and verification evidence

The user made TDD a project requirement on 2026-11-09. It applies to executable packaging, controller, source-preparation, verification and migration behavior. Tests must exercise an observable result or a material guard. Documentation and original static artwork use review and visual QA.

## Workflow

1. Define the expected behavior and the acceptance boundary.
2. Add or update a relevant test. Run it and observe a failure caused by the missing behavior or defect.
3. Implement the smallest change that passes that test.
4. Run the focused checks and the required project suite. Refactor while keeping them green.
5. Record meaningful Red/Green evidence for bug fixes and consequential guards. Do not label after-the-fact coverage as a historical TDD cycle.

Existing code requires characterization coverage before further modification. An import error alone does not establish that the intended behavior was tested. Real OBS failures can identify a defect; reproduce it in a focused automated check locally when practical before changing the recipe.

## Current evidence

- Binding-generator working directory: the build-command fixture invokes real Cargo metadata. It failed with the same missing `Cargo.toml` error as OBS when run from the package root. Running the binding command from the Rust workspace makes the metadata probe pass. The fixture stops before unrelated compilation; actual binding generation remains an OBS integration check.

- Debian vendor cleanup: `test_actual_clean_target_preserves_vendor_checksums` ran the real `debian/rules clean` against a fixture containing a Cargo checksummed `.orig` file. It failed because the source file disappeared. Adding `dh_clean -Xdeps/` made it pass while a temporary `.orig` outside dependencies was still removed. This is a confirmed behavioral Red/Green cycle.
- Linux video default: the source check failed on the original 7.4.1 settings and passed after applying the Linux-default patch. It checks preprocessed Linux behavior and the preserved upstream backend/fallback source. This is source-level evidence, not GPU playback acceptance.
- Snap executable detection: tests cover both the Snap `telegram-desktop` executable and upstream `Telegram`, including a replaced/deleted executable. The tests failed before the detector was added.
- Existing release, archive-safety and historical repack tests protect inspected boundaries. This record does not claim every original packaging change was developed with strict TDD.

## Coverage to complete before release

- Production source preparation and publication need behavioral checks for immutable source inputs, private identity injection and exact-artifact gating. The historical repack path is disabled.
- Migration characterization now covers existing-profile refusal, active clients, source and destination symlinks, a backup mismatch and a small successful verified copy, using synthetic profiles only. Real migration remains gated on a working production package and a verified closed profile.
- The isolated source-built deb must pass actual installation, dependency, visible-window and remove/reinstall tests. Driver checks and source checks do not substitute for these.
- GPU decoding requires an actual client playback test on available hardware. Intel, AMD and NVIDIA support must be reported according to evidence; one machine cannot validate every configuration.

## Commands and boundaries

```sh
export TMPDIR=/srv/temp/telegram
mkdir -p "$TMPDIR"
python3 -m unittest discover -s tests -v
bash -n tools/*.sh packaging/source/debian/build-deps.sh
```

Run tests before each source upload. Compile the application and dependencies in OBS, never on the mini-PC. Run local tests with disk-backed scratch. Never use production sessions, real messages or API secrets as fixtures. Test-only API identities and sample build artifacts cannot be released or used for migration.
