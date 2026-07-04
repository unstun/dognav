---
paths: ["2_experiment/**", "**/*.tex", "**/*.py", "**/*.ipynb", "**/*environ*", "**/*conda*"]
---
# ============================================================
# 本地实验踩坑
# ============================================================

- `conda run` 不会自动 cd，必须 `--cwd <绝对路径>`。
- 远端 `~/.bashrc` 的 conda init 块必须放在 interactive guard (`case $- in`) 之前。
- LaTeX：`xelatex` 支持中文注释，提交版用 `pdflatex`，缺包 `sudo tlmgr install <pkg>`。
- Apple Silicon Mac 上 PyTorch 使用 MPS 后端，部分 op 不支持，训练建议用 CPU 或远程 GPU。
