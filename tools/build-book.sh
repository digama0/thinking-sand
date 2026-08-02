#!/usr/bin/env bash
# Build the mdBook rendering (sources live in src/, the conventional layout).
#
# Two jobs beyond `mdbook build`:
#  - check SUMMARY.md covers every chapter in src/ (mdBook rewrites .md links to
#    .html unconditionally, so a file present but unlisted would 404), and vice versa;
#  - copy tools/ into the output: the book links these as raw files, tools/ stays at
#    the repo root (its scripts compute the repo root as tools/..), and only book/
#    is deployed to Pages.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v mdbook >/dev/null || { echo "mdbook not found (cargo install mdbook)" >&2; exit 1; }

# Regenerate the scoreboard appendix from this working tree: the published book
# carries the checker verdicts of the same commit that built it. A FAIL in a
# checker must be visible in the page, not block the book -- hence || true.
# (Without data/ the page honestly shows the checks failing on missing files;
# run tools/fetch-data.sh checks first.)
python3 tools/check-all.py --md > src/scoreboard.md || true

python3 - <<'PY'
import pathlib, re
present = {str(p.relative_to('src')) for p in pathlib.Path('src').rglob('*.md')}
present -= {'SUMMARY.md'}
listed = set(re.findall(r'\]\(([^)]+\.md)\)', pathlib.Path('src/SUMMARY.md').read_text()))
missing = present - listed
if missing:
    raise SystemExit('not in SUMMARY.md: ' + ', '.join(sorted(missing)))
ghosts = listed - present
if ghosts:
    raise SystemExit('in SUMMARY.md but not in src/: ' + ', '.join(sorted(ghosts)))
print(f'SUMMARY covers all {len(present)} chapters')
PY

mdbook build
mkdir -p book/tools
cp tools/*.py tools/*.sh book/tools/
echo "book/ built — open book/index.html"
