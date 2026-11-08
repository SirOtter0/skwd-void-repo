# Redistribution review: coordinated legal revision4

Reviewed input: beta.26, public port466e95c608b37000491633bdbec6ca801a059714.
The four original projects are MIT; bundled dependencies/assets retain their own
licenses. This is evidence for this exact x86_64 glibc configuration, not a blanket
permission for optional SDKs, weights, drivers, other features or future versions.

## Notices completed

`repack-notices.py` adds LICENSE/LICENCE/NOTICE/COPYRIGHT/ATTRIBUTION files from
actual compiled crates and their nested native components, preserving original
bytes. Each package has NOTICE.txt and DEPENDENCIES.json with separate runtime
and build-only/proc-macro labels. Rust standard-library copyright/license notices
come from the authenticated matching builder package. Missing workspace notices
were obtained from immutable upstream source revisions, with URLs and SHA256.

| Component | Conservative runtime crates | Built-only/proc-macro crates |
|---|---:|---:|
| Wall | 251 | 38 |
| Deck | 224 | 44 |
| Lens | 95 | 27 |
| Paper | 185 | 54 |

These sets are traced from retained successful Cargo fingerprints and dep-info;
LTO can remove unused code, so this does not claim that every function survives.
They are narrower than the optional/platform lockfile inventory. Build-tool
notices are retained conservatively for generated material, without claiming their
machine code is in the runtime.

Specifically covered: webpki-roots CDLA-Permissive2.0, libloading ISC (including the
actual0.9.0 Lens dependency), Unicode/ICU and unicode-ident notices, option-ext MPL2.0
with exact-source offer, native Intel texture compressor copyright2017 Intel/MIT,
QuickJS/ring/SQLite and nested native notices where present. No ONNX runtime/model
pack or NVIDIA driver is bundled. Official Void dynamic dependencies are declared
and are not misrepresented as copied private libraries.

Wall's unmodified Symbols Nerd Font matches the official3.4.0 Git object exactly.
Roboto/Noto notices and individual Nerd glyph licenses/credits are included. Font
Awesome Extension's original LICENCE is MIT; Font Logos's LICENSE is the Unlicense.
Weather README attribution/CC BY3.0 is retained separately from its font OFL terms.
See legal/ASSETS.md, immutable notice manifests and font-match proof. Original
premerge Noto font-build versions are not recorded upstream; no font regeneration
claim is made. The exact distributed font bytes remain pinned and unchanged.

One old Deck LICENSING.md sentence says paper-scene retains GPL. For the actual
coordinated Paper inputs its specific root LICENSE is MIT, its workspace metadata
is MIT and paper-scene inherits it; the inspected Rust sources/manifests contain
no source-specific GPL override. We rely on that direct grant for this revision,
not on Deck relicensing Paper. The stale sentence is preserved in corresponding
source and explicitly recorded here rather than silently rewritten.

## Source/SDK delivery

The prepared archive includes exact patched sources/vendor/locks, native source,
public port recipes/security patches, source hashes and public infrastructure.
45,595 vendor-file hashes verified; full Cargo metadata resolution passed for all
four workspaces offline/frozen in bubblewrap with read-only source mounts and no
project compilation/execution. Original Rust code/locks and ELF bytes are unchanged.

Steamworks native lib/ is already empty in the authenticated coordinated suite;
neither Steam wrapper is in the core compiled closure. Exclusion count is therefore
zero, recorded explicitly. We do not infer Valve SDK rights from a wrapper license.
The helper records/excludes a future unused native SDK payload and refuses if core
builds require it. Windows import stubs retain their crate licenses;341 vcpkg .lib
fixtures are zero-byte placeholders, not copies of proprietary runtime libraries.
See review/foreign-target-inputs.json. Foreign-target inputs are not Linux runtime
contents.

## FFmpeg

Paper retains exact FFmpeg9.0.1 source tarball, LGPL text, original LICENSE.md and
native build recipe. New notices add IJG credit and original JPEG source headers,
exact configure invocation, an empty source-changes diff, and a description of
RUNPATH/patchelf modifications. No GPL/nonfree/version3 configure option was used.
Five shared libraries remain private under /usr/lib/skwd-paper. Interface-compatible
replacement and reverse engineering for debugging modifications are permitted;
there is no contradictory EULA. See legal/FFMPEG.md and the full source offer.

## Private rehearsal outcome

All four revision4 packages preserve the10 executable and5 private-library hashes.
Native XBPS imported only the independently checked disposable key; installed
signed revision3; simulated the four updates with an unchanged installed state;
installed revision4; verified package signatures, supplemental signed manifest,
index/source/payload hashes; rejected separately altered package and signature;
and removed all four packages plus lab config/trust. Services were unchanged and
xbps-pkgdb passed. A fixture downgrade also passed. No graphical test was repeated.

The key lived in guest /run tmpfs, disappeared when the VM stopped, and absence
was confirmed at cleanup. No private key was exported to Git, disk artifacts or
logs. Both guests use private UNIX-stream Ethernet, no gateway/DNS/host shares.
No production key, public binary release, Pages deployment or upstream PR exists.

## Decision boundary

The identified notice/source obligations are addressed for the reviewed revision.
Technical evidence is ready for owner review of definitive-key creation and the
first testing release. Publication remains disabled. Approve the exact production
candidate/provenance, key identity/backup ceremony and public endpoint before any
real signing/publication. The private rehearsal identity is not production trust.
