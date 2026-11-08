# Native and toolchain components

The per-crate notice trees retain nested native LICENSE/NOTICE/COPYRIGHT files as
well as Rust notices (including ring's third-party implementations, QuickJS,
SQLite, texture encoders and other bundled code where present in the actual build).
Rust 1.99.0 standard-library LICENSE-MIT, LICENSE-APACHE and COPYRIGHT are copied
from the matching builder's authenticated Rust package, not inferred from Skwd MIT.

The runtime crate set is a conservative closure of retained successful Cargo
fingerprints. Dead-code elimination may remove parts of a crate; listing it is
not a claim that all its functions are distributed. Build-only/proc-macro notices
are labelled separately and retained conservatively for generated material; their
machine code is not automatically described as part of the shipped runtime.

Dynamic libraries supplied by official Void packages are dependencies, not copied
into these archives: glibc/libgcc, fontconfig, Wayland/xkbcommon/GL/Vulkan loaders,
ALSA, shaderc, libva/libdrm/libdav1d/libyuv/zlib as declared per package. Their own
packages supply their licenses. NVIDIA drivers, ONNX Runtime and model packs are
not bundled or relicensed here. Five private FFmpeg libraries ARE shipped by Paper;
see FFMPEG.md and its complete source/build files.
