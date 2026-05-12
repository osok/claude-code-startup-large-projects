#!/usr/bin/env bash
#
# build_docs_archive.sh — Package documentation into a distributable zip archive
#
# Invoked by .claude/skills/doc-archive.md. Creates a timestamped zip file
# containing dev-docs/, project-docs/, requirement-docs/, design-docs/, and a
# generated top-level README.md with section index and archive stats.
#
# Usage:
#   .claude/scripts/build_docs_archive.sh                # output to project root
#   .claude/scripts/build_docs_archive.sh /path/to/dir   # output to custom dir

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# .claude/scripts/ -> .claude/ -> project root
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

OUTPUT_DIR="${1:-$PROJECT_ROOT}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_NAME="documentation-${TIMESTAMP}.zip"
ARCHIVE_PATH="$OUTPUT_DIR/$ARCHIVE_NAME"

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

echo "Building documentation archive..."
echo "  Project root: $PROJECT_ROOT"
echo "  Output:       $ARCHIVE_PATH"
echo ""

DOC_DIRS=("dev-docs" "project-docs" "requirement-docs" "design-docs")

for dir in "${DOC_DIRS[@]}"; do
    src="$PROJECT_ROOT/$dir"
    if [ -d "$src" ]; then
        echo "  Copying $dir/ ..."
        rsync -a \
            --include='*/' \
            --include='*.md' \
            --include='*.json' \
            --include='*.yaml' \
            --include='*.yml' \
            --include='*.sql' \
            --include='*.png' \
            --include='*.jpg' \
            --include='*.svg' \
            --exclude='__pycache__/' \
            --exclude='*.pyc' \
            --exclude='node_modules/' \
            --exclude='*' \
            "$src/" "$STAGING_DIR/$dir/"
    else
        echo "  WARNING: $dir/ not found, skipping"
    fi
done

count_files() {
    find "$STAGING_DIR/$1" -type f 2>/dev/null | wc -l
}

DEV_COUNT=$(count_files "dev-docs")
PROJECT_COUNT=$(count_files "project-docs")
REQ_COUNT=$(count_files "requirement-docs")
DESIGN_COUNT=$(count_files "design-docs")
TOTAL=$((DEV_COUNT + PROJECT_COUNT + REQ_COUNT + DESIGN_COUNT))

PROJECT_NAME="$(basename "$PROJECT_ROOT")"
cat > "$STAGING_DIR/README.md" << HEREDOC
# ${PROJECT_NAME} Documentation Archive

This archive contains the documentation set for the project.

## Contents

| Directory | Description | Index |
|-----------|-------------|-------|
| [dev-docs/](dev-docs/) | Developer reference documentation | [dev-docs/README.md](dev-docs/README.md) |
| [project-docs/](project-docs/) | Architecture, test plans, code reviews, ADRs | [project-docs/README.md](project-docs/README.md) |
| [requirement-docs/](requirement-docs/) | ISO 29148 requirements specifications | [requirement-docs/README.md](requirement-docs/README.md) |
| [design-docs/](design-docs/) | Component and system design documents | [design-docs/README.md](design-docs/README.md) |

## Document Conventions

- Design documents use numbered prefixes by type:
  - \`01-\` UI/UX foundation, \`02-\` Data, \`03-\` Security
  - \`10-\` Libraries, \`20-\` Backend, \`30-\` Frontend
  - \`40-\` Agents, \`50-\` Integration, \`60-\` Infrastructure, \`90-\` UI/UX screens
- Requirements follow **ISO/IEC/IEEE 29148:2018**
- ADRs follow Context / Decision / Status / Consequences

## Archive Statistics

| Directory | Files |
|-----------|-------|
| dev-docs/ | $DEV_COUNT |
| project-docs/ | $PROJECT_COUNT |
| requirement-docs/ | $REQ_COUNT |
| design-docs/ | $DESIGN_COUNT |
| **Total** | **$TOTAL** |

*Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")*
HEREDOC

echo ""
echo "  Creating zip archive..."
(cd "$STAGING_DIR" && zip -rq "$ARCHIVE_PATH" .)

ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)

echo ""
echo "Archive created successfully!"
echo "  File:  $ARCHIVE_PATH"
echo "  Size:  $ARCHIVE_SIZE"
echo "  Files: $TOTAL documents"
echo ""
echo "  dev-docs:         $DEV_COUNT files"
echo "  project-docs:     $PROJECT_COUNT files"
echo "  requirement-docs: $REQ_COUNT files"
echo "  design-docs:      $DESIGN_COUNT files"
