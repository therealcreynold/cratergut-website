#!/bin/bash
# Refuses to let a banned word reach the public website.
#
# Cratergut is its own game and owes nothing to anybody else's. Naming the thing it will
# inevitably be compared to — in prose, in a comment, in a file name, in an alt attribute —
# is how a clean-room product stops being one, and a web page is the worst place for it,
# because a web page is what a search engine reads and what a lawyer is shown.
#
# The game's own repository has a larger version of this check with an exemption for the App
# Store keyword field, where the bare word is a generic English noun in hidden metadata.
# There is no such exemption here. Nothing on this site has any business saying any of it.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TERMS_FILE="$ROOT/scripts/banned-terms.txt"
failed=0

if [ ! -f "$TERMS_FILE" ]; then
    echo "lint-legal: $TERMS_FILE is missing, so nothing was checked" >&2
    exit 1
fi

while IFS= read -r term; do
    case "$term" in ''|'#'*) continue ;; esac
    # File contents, including this script's own directory being skipped so the list of
    # words does not trip the check that reads it.
    while IFS= read -r hit; do
        case "$hit" in "$ROOT/scripts/"*|"$ROOT/.git/"*) continue ;; esac
        echo "${hit#"$ROOT/"}  <- banned term: $term" >&2
        failed=1
    done < <(grep -ril --exclude-dir=.git -- "$term" "$ROOT" 2>/dev/null)

    # And the names of the files themselves.
    while IFS= read -r hit; do
        case "$hit" in "$ROOT/scripts/"*|"$ROOT/.git/"*) continue ;; esac
        echo "${hit#"$ROOT/"}  <- banned term in the file name: $term" >&2
        failed=1
    done < <(find "$ROOT" -not -path '*/.git/*' -iname "*${term}*" 2>/dev/null)
done < "$TERMS_FILE"

if [ "$failed" -ne 0 ]; then
    echo "lint-legal: failed" >&2
    exit 1
fi
echo "lint-legal: clean"
