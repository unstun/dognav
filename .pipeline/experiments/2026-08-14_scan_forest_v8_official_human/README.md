# V8 R2 Official Isaac Human

This directory preserves the official-human visual preflight and later V8 R2
qualification evidence. NVIDIA character, texture, skeleton, and animation
content is referenced from the versioned Isaac Sim 5.1 asset root and is not
vendored in this repository.

`visual_preflight04` and `visual_preflight05` prove that the official character
can be referenced, rendered, moved with the hidden proxy, and recorded beside
the Lite3/forest runtime. The character remains in its T-pose, so these are
negative/incomplete evidence and cannot satisfy AC40--AC44.

The official People graph was then tested with the pinned Isaac Lab runtime.
Direct-GPU PhysX attempts reproduced CUDA illegal-access failures; an isolated
CPU-physics attempt completed but moved the character out of the review view
and reported animation-variable type mismatches. Those attempts are not review
candidates. The current safe code path therefore references the official model
without claiming animation; the next implementation must bake or cache the
official NVIDIA animation outside the Direct-GPU physics loop.
