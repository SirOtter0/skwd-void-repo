# Intel texture compressor provenance

The actual Deck dependency closure includes intel_tex_2 0.5.0. Its immutable
crate VCS revision is Traverse-Research/intel-tex-rs-2
9a05fb8926d635014fddfcadb02ffd5c84822688; its vendor submodule points to
GameTechDev/ISPCTextureCompressor 14d998c02b71c356ff3a1ec1adc9243a517bbf38.
Intel's native code is MIT, Copyright 2017 Intel Corporation, retained here along
with the wrapper's copyright/licenses. Source/vendor hashes identify the packaged
x86_64 ISPC static inputs. Upstream ships these pregenerated inputs; this port
has not claimed to regenerate every native object from source. Public source and
upstream kernel build recipe are identified; the existing verified inputs remain
unchanged. Native objects for other platforms are not evidence of runtime use.
