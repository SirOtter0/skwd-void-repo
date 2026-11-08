# Private FFmpeg 9.0.1 distribution

This software uses libraries from the FFmpeg project under LGPLv2.1-or-later.
This software is based in part on the work of the Independent JPEG Group.

Exact source: ffmpeg-9.0.1.tar.xz, SHA256
cf38e0e28c7e5605942c4a77755349b0145804a397af37eb1fb4c77cb237f635,
https://ffmpeg.org/releases/ffmpeg-9.0.1.tar.xz.
The complete tarball, COPYING.LGPLv2.1, LICENSE.md, SHA256, SOURCE and build-recipe.sh
are in the adjacent ../ffmpeg directory. The corresponding-source release archive
also supplies the exact suite, patches and link/build scripts.

The complete configure command is in ffmpeg-configure.txt, checked against the
string embedded in the validated libavutil. No --enable-gpl, --enable-nonfree or
--enable-version3 was used. ffmpeg-source-changes.diff is empty: no source patch
was applied. Configure-generated files and compilation are normal build outputs.
The downstream runtime recipe applies patchelf --set-rpath '$ORIGIN' to the shared
libraries; linked clients use '$ORIGIN/../lib/skwd-paper'. Those are binary loader
path changes, not edits to FFmpeg source files. Retain the script and original
source so these steps can be repeated. JPEG source notices are reproduced in
JPEG-SOURCE-NOTICES.txt; the three identified IJG source files are unmodified.

The five libraries live privately under /usr/lib/skwd-paper. They are dynamically
linked and do not replace Void's system FFmpeg. You may modify and rebuild them
and replace the private libraries with ABI-compatible versions. Preserve SONAMEs,
architecture and relative library lookup; do so in a disposable test root first.
No signature check is embedded in the application to prohibit replacement. XBPS
package-integrity checks may correctly report your local replacements as changes;
they do not revoke your LGPL modification rights. You may reverse engineer the
combined program as needed to debug such modifications. There is no additional
EULA restricting those rights. Do not replace unrelated system libraries.
