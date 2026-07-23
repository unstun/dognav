# Implementation Plan: Navigation Project Harness Migration

1. Initialize Trellis 0.6.7 with Codex, Claude Code, and Cursor adapters using
   skip-existing mode.
2. Configure manual commit behavior and add the Trellis block to `AGENTS.md`.
3. Adapt common research and repository rules for `machine-dog-nav`.
4. Merge generic project hooks and selected Codex agent roles.
5. Add fresh `.pipeline/` and `bigmemory/` structures.
6. Copy and adapt the curated project skills without replacing existing
   third-party symlinks.
7. Update `.gitignore` so project-owned harness files are tracked while
   upstream clones and generated runtime state remain ignored.
8. Validate:
   - Trellis version, task validation, and package context
   - TOML, JSON, YAML, Python, and shell syntax
   - hook smoke tests
   - skill discovery and hard-coded source-path scan
   - staged path audit excluding `docs/research/`
9. Update the new project state, commit the verified harness migration, and
   leave the navigation source survey for a separate task.
