---
paths: ["2_experiment/**", "**/*.tex", "**/*.py", "**/*.ipynb", "**/*environ*", "**/*conda*"]
---
# ============================================================
# Local Experiment Gotchas
# ============================================================

- `conda run` does not automatically `cd`; always pass `--cwd <absolute-path>`.
- On remote machines, the conda init block in `~/.bashrc` must appear before the interactive guard (`case $- in`).
- LaTeX: `xelatex` supports Chinese comments; submission builds use `pdflatex`; for missing packages, run `sudo tlmgr install <pkg>`.
- On Apple Silicon Macs, PyTorch uses the MPS backend, but some ops are unsupported. Prefer CPU or remote GPU for training.
