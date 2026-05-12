---
name: doc-archive
description: Regenerate doc overview READMEs across all documentation directories, then build a timestamped zip archive of all docs.
---

# Doc Archive

Regenerates documentation overview READMEs and packages all docs into a distributable zip.

1. **Regenerate overview READMEs** in each of these directories (create the README if missing, update the index if present):
   - `dev-docs/README.md` — developer reference documentation index
   - `project-docs/README.md` — architecture, ADRs, test plans, reviews
   - `requirement-docs/README.md` — ISO 29148 requirement specs
   - `design-docs/README.md` — component and system design documents

   Each README must list every markdown file in its directory (recursively) with a one-line summary derived from the file's first heading or front-matter description.

2. **Update top-level `README.md`** with links to each of the four doc-section READMEs above.

3. **Run the archive script:** `.claude/scripts/build_docs_archive.sh`
   - Output: timestamped zip at project root (`documentation-YYYYMMDD_HHMMSS.zip`)
   - Contents: `dev-docs/`, `project-docs/`, `requirement-docs/`, `design-docs/`, `README.md`
   - Skips: `__pycache__/`, `*.pyc`, `node_modules/`

4. **Report** the archive path to the user.

**Prerequisite:** `.claude/scripts/build_docs_archive.sh` must exist and be executable. If missing, surface this and stop — do NOT attempt to regenerate it inline.
