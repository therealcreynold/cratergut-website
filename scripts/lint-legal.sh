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
#
# THE LIST IS BASE64 AND THAT IS THE WHOLE POINT.
#
# GitHub Pages deploys every file in this repository, so until 2026-09-03 the word list was
# served as prose at https://cratergut.com/scripts/banned-terms.txt -- HTTP 200, text/plain,
# on the domain the App Store listing points at, under a heading naming those words as the
# reference game's marks. The check written to keep another company's trademarks off this
# site was the one thing on it publishing them, and the paragraph five lines above says
# exactly why that is the worst possible place for them: a web page is what a search engine
# reads and what a lawyer is shown.
#
# Encoding is not concealment and is not meant to be -- anyone who wants the list can decode
# it in one command, and git history still holds the plaintext. It removes the thing that
# actually did harm, which is a readable, indexable page of somebody else's marks.
#
# The right fix is to stop deploying this directory at all, with a Jekyll `exclude:`. That
# swaps out the serving mechanism of a live site whose privacy-policy URL App Review is
# reading right now, so it is written down in README.md and waits until 1.1 clears.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TERMS_FILE="$ROOT/scripts/banned-terms.b64"
failed=0

if [ ! -f "$TERMS_FILE" ]; then
    echo "lint-legal: $TERMS_FILE is missing, so nothing was checked" >&2
    exit 1
fi

# Decoded once into a variable rather than a temporary file, so the plaintext never touches
# the working tree -- where the next run of this very check would find it and, correctly,
# fail.
TERMS="$(base64 -d < "$TERMS_FILE")" || {
    echo "lint-legal: $TERMS_FILE could not be decoded, so nothing was checked" >&2
    exit 1
}

if [ -z "$TERMS" ]; then
    echo "lint-legal: the decoded term list is empty, so nothing was checked" >&2
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
done <<< "$TERMS"

if [ "$failed" -ne 0 ]; then
    echo "lint-legal: failed" >&2
    exit 1
fi
echo "lint-legal: clean"
