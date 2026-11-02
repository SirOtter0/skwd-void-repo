# Distribution review — not yet cleared

Review target: coordinated beta.26 / packages 1.0.0beta26_3, port commit
466e95c608b37000491633bdbec6ca801a059714, Void x86_64 glibc only.
The fact that local use/builds passed does not clear public redistribution.
`policy/release.json` deliberately blocks signing and channel promotion.

## Findings

| Component | Project license | Distribution status |
|---|---|---|
| Wall | MIT, copyright liixini 2025–2026 | Hold: complete per-dependency copyright/notice and embedded asset attribution inventory |
| Deck | MIT, same holder | Hold: includes TLS root data; CDLA-Permissive-2.0 text is missing from current binary notices; complete ISC/Apache/MIT notices |
| Lens | MIT, same holder | Hold: complete crate/asset notices; no model weights or ONNX Runtime are included or cleared by this review |
| Paper | MIT, same holder | Hold: complete native/Rust notices, including IJG credit; maintain corresponding FFmpeg source/configuration and relink rights |

MIT permits distribution with its copyright and permission notice. The root
project LICENSE files are already packaged. A single generic MIT/Apache text does
not preserve every dependency's own required copyright/NOTICE. A generated
lockfile inventory is an overapproximation: optional, build-only and foreign-target
crates are not automatically present in the distributed executable.

Concrete examples from the inspected source/package pair:

* `webpki-roots` 1.0.10 ships CDLA-Permissive-2.0 LICENSE and requires that text with
  shared data. Current Deck/Paper binary notices do not include it.
* `libloading` 0.8.9 ships ISC permission/copyright; current general notice lists
  do not provide the per-crate copyright collection.
* `unicode-ident` 1.0.24 and ICU data have Unicode-3.0 notices requiring retention;
  this license is not covered by a generic MIT license file.
* `option-ext` 0.2.0 is MPL-2.0; Wall/Deck already include its license and a source
  pointer. Retain accessible corresponding source for that exact version; source
  mirroring must not remove its notices.
* Font/SVG/image assets may require OFL/CC-BY credit independent of Rust licenses.
  Confirm original creators, links, modifications and any reserved font names.
* `intel_tex_2` contains upstream prebuilt ISPC inputs. Its wrapper is permissively
  licensed, but retain Intel ISPC texture-compressor/native notices and identify
  exact source/build provenance before mirroring the full source bundle.
* The lockfile also contains optional `steamworks-sys`. The Rust wrapper's
  MIT/Apache declaration does NOT grant rights to Valve SDK files bundled with it.
  No Steam API shared library is included in the inspected XBPS payload. Still
  review/remove unused SDK files from a public source mirror in a documented,
  build-equivalent way, or establish their redistribution permission first.

These are incomplete compliance deliverables, not a finding that the four MIT
projects prohibit binary redistribution. Do not publish the affected archives
until the deliverables are complete and checked against the actual linked graph.

## FFmpeg

The actual private libavutil configuration embedded in the new independent build
was inspected without loading the library. It enables shared/PIC, disables static,
autodetection, network, programs, filters, encoders/muxers, and enables zlib, VAAPI,
Vulkan, DRM and dav1d. It does not enable `gpl`, `nonfree` or `version3`.
FFmpeg's LGPLv2.1-or-later configuration is compatible with distribution under its
conditions; this is not a patent-clearance assertion for every codec/jurisdiction.

Already supplied by the Paper package:

* Five private shared libraries, relative RUNPATHs; no system FFmpeg replacement.
* Exact FFmpeg 9.0.1 source tarball SHA256
  cf38e0e28c7e5605942c4a77755349b0145804a397af37eb1fb4c77cb237f635.
* COPYING.LGPLv2.1, LICENSE.md, source URL/hash and build recipe.

Still required before publication:

* Add the Independent JPEG Group attribution. The build logs confirm jfdctfst.o,
  jfdctint.o and jrevdct.o were compiled; FFmpeg LICENSE.md calls out this credit.
* Preserve the exact configure invocation and describe the source changes (none
  identified in those JPEG source files) and the downstream RUNPATH/patchelf change.
* Supply/rehost the corresponding source, patches and build scripts alongside the
  binaries, without requiring access to the author's workstation/private server.
* Permit interface-compatible replacement of the LGPL libraries and reverse
  engineering for debugging those modifications; do not impose a contradictory EULA.
* Verify all linked native notice obligations, including dependencies supplied by
  official Void packages versus libraries incorporated into the binary.

## Sources and closure

The official suite URL/hash, four source revisions, patched lockfiles, crate
checksums and FFmpeg source hash are public in the pinned port. Preparation and
all four clean builds were demonstrated from those public inputs. HTTPS/pinned
hash verification is not an independently authenticated detached upstream signature.

For each published release retain exact patched sources/vendor, native sources,
patches, recipe commit, tool/package inventory, notice bundle and signed manifest.
Do not rely only on upstream URLs remaining available. Source-only artifacts also
need redistribution review (notably optional SDK content).

Run `scripts/license-inventory.py PREPARED-SUITE NEW.json` to reproduce the
machine-readable review. It is not a legal approval engine. After completing
notices, rebuild/repackage with a new coordinated XBPS revision if an already
published revision would change. Test installation/removal, bind approval to the
exact new candidate.json SHA256, and only then clear the policy blockers.

References:

* [FFmpeg exact-version licensing](https://github.com/FFmpeg/FFmpeg/blob/n9.0.1/LICENSE.md)
* [FFmpeg distribution checklist](https://ffmpeg.org/legal.html)
* [LGPL 2.1 text](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
* [MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/)
* Per-crate LICENSE/NOTICE and Cargo manifests in the verified suite are the primary
  evidence for the specific dependency versions.
