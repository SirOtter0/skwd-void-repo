# Controlled builders

Use a disposable dedicated Void x86_64 glibc/runit VM. Never install development
prerequisites on a user's unrelated desktop. No signing key, publishing token,
SSH credential or personal HOME belongs on the builder. No public PR code runs on
this runner. Pin and record the VM/base input digest and refresh it deliberately.

The immediately preceding independent validation built all four components twice
from fresh public sources in a newly copied pre-port VM, with separate source,
Cargo-home and target directories. Another clean VM without a compiler installed,
ran and removed the four generated packages. Those results can be reused; do not
repeat them merely to rename the distribution repository. See the port's public
[clean-build report](https://github.com/SirOtter0/skwd-wall/blob/466e95c608b37000491633bdbec6ca801a059714/packaging/void/INDEPENDENT-VALIDATION.md).

For future release builds, provision the disposable VM using the prerequisite
transaction in that exact port commit's packaging/void/README.md, reviewing the
XBPS simulation first. It includes base-devel, git/curl/Python, Rust/Cargo 1.99.0,
bubblewrap, patch, CMake, NASM, patchelf, pkg-config, shaderc, Vulkan-Headers,
vulkan-loader-devel, libva/ALSA/PulseAudio/libyuv development packages,
clang19/libclang19/clang19-headers, fontconfig/libxkbcommon/Wayland/libdrm/libglvnd/
libdav1d/zlib development packages. Python 3.14+ is required by the repository
verifier for native zstd-compressed XBPS archives. No systemd/Nix required.

As a normal, unprivileged account with an empty HOME:

```
scripts/build-candidate.sh /absolute/new/private/work
```

The script pins the port commit, obtains/verifies the official suite, exact missing
crates and FFmpeg source during preparation, then invokes the published offline
bubblewrap builds. It installs nothing. No old binary/Cargo cache is an input.
It records installed packages/tool versions, performs static package checks,
prepares corresponding source and a LOCAL unsigned candidate. Full logs stay local;
only sanitized provenance is eligible for distribution. Sources/notices need the
separate licensing approval even when the build succeeds.

A future build may stop if rolling Void has a different toolchain/provider version.
Review the change; do not silently downgrade/update the policy or source lockfiles.
Record package versions, source/preparer/patch hashes and SOURCE_DATE_EPOCH for each
release. Two earlier independent builds produced identical ELF and normalized XBPS
bytes in their recorded environment; no general cross-toolchain guarantee is made.

## Clean runtime acceptance

Before signing, install all four newly built packages in another disposable clean
Void VM using a local repository. Record the dry-run and real transaction, run
xbps-pkgdb, inspect ELF dependencies/RUNPATH, check service/autostart state, and
remove all four again. Verify all owned files are removed. Do not automatically
remove personal data or unrelated dependencies.

In a minimal Labwc/Pixman + seatd session with VirtIO 2D and explicit x86_64
Lavapipe ICD: test Deck IPC/catalogue/thumbnail, Wall winit catalogue display,
Paper static synthetic image and surface removal, Lens empty pack listing.
Capture only the VM framebuffer. No models or network content are needed.
Keep real Niri/NVIDIA coverage distinct from software-rendered VM coverage.

## CI status

The hosted PR workflow tests infrastructure only, with a read-only token and no
secrets. The manual build workflow is disabled unless ENABLE_BINARY_BUILD=true
and runs only on an owner-provisioned ephemeral Void VM label. Configure a protected
build-review environment and runner-group restrictions to the main workflow before
turning it on. Destroy each runner/working disk after exporting reviewed evidence.
Do not expose a general persistent self-hosted runner to public PRs.

No binary upload step is enabled: an Actions artifact can be accessible to others
and is still redistribution. Obtain explicit release approval before adding an
approved unsigned candidate-transfer job. The build VM never receives the signing key.

## Legal revision4

The pipeline first builds the original revision3 payload from the validated port,
then records the actual Cargo fingerprint dependency closure and reassembles all
four archives as revision4. `repack-notices.py` adds per-crate/native/asset notices
and exact companion dependencies, and refuses any change to ELF bytes. Existing
validated input archives use pinned hashes; a fresh controlled build supplies the
original packager inventory with --build-inventory. No old binary cache is required
by that fresh-build path.

`prepare-public-source.py` retains exact sources/locks/vendor, the validated public
port recipes, patches and public infrastructure snapshot. Its SDK plan records
that the original Steam SDK directory is empty and unused by core packages. It
refuses automatic SDK exclusions if the actual core build uses those wrappers.
An actual source module named src/wayland/target is retained; it is not a Cargo
cache. Corresponding-source checks resolved all four workspaces offline/frozen,
with read-only sources, and verified45,595 vendored files. No compilation was
repeated for the notice-only repack.

The revised individual steps and private signing/install/removal path were tested.
The newly composed fresh CI orchestration has not been run as another complete
Rust build; the earlier two independent clean builds remain its compiler evidence.
The binary build and publication workflows remain disabled.
