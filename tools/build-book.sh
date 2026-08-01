#!/usr/bin/env bash
# Build the mdBook rendering of the repository.
#
# mdBook wants a dedicated source directory; pointing it at the repo root would make
# it copy everything (including the ~490 MB data/ tree) into the output. So this
# script stages the git-TRACKED markdown files — preserving relative paths, which
# keeps every inter-document link working — plus tools/ (linked from the README as
# raw files), into book-src/, then builds into book/. Both are gitignored.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v mdbook >/dev/null || { echo "mdbook not found (cargo install mdbook)" >&2; exit 1; }

rm -rf book-src
mkdir book-src
git ls-files '*.md' | while read -r f; do
  mkdir -p "book-src/$(dirname "$f")"
  cp "$f" "book-src/$f"
done
cp SUMMARY.md book-src/   # explicitly: must exist even if not yet tracked
mkdir -p book-src/tools
cp tools/*.py tools/*.sh book-src/tools/

# Every staged chapter must be listed in SUMMARY.md: mdBook rewrites .md links to
# .html unconditionally, so an unlisted file would 404 after rewriting.
python3 - <<'PY'
import pathlib, re
staged = {str(p.relative_to('book-src')) for p in pathlib.Path('book-src').rglob('*.md')}
staged -= {'SUMMARY.md'}
listed = set(re.findall(r'\]\(([^)]+\.md)\)', pathlib.Path('SUMMARY.md').read_text()))
missing = staged - listed
if missing:
    raise SystemExit('not in SUMMARY.md: ' + ', '.join(sorted(missing)))
ghosts = listed - staged
if ghosts:
    raise SystemExit('in SUMMARY.md but not staged: ' + ', '.join(sorted(ghosts)))
print(f'SUMMARY covers all {len(staged)} chapters')
PY

mdbook build
echo "book/ built — open book/index.html"
