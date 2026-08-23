# cratergut.com

The website for Cratergut, served by GitHub Pages. Four pages, one stylesheet, no build step
and no framework: everything here is the file that gets served.

This is also the **only** copy. It used to live in the game's own repository under `site/`,
and the two would have drifted the first time either was edited — which matters more than
usual here, because two of these files are things Apple and Google read and hold you to.

## Why the pages are directories

`privacy/index.html` rather than `privacy.html`, because the game links to
`https://cratergut.com/privacy` with no extension and that string is compiled into the
binary. A directory with an `index.html` serves at that URL on every static host there is.
Extensionless serving of `privacy.html` is a per-host behaviour, and this is not a thing to
be clever about: if these URLs 404, the app ships with three dead links in Settings, which is
a guideline 2.1 rejection.

## The two files that are not decoration

**`app-ads.txt`** is how advertising networks confirm that whoever is selling advertising
inside the game is allowed to. It must be served from the root of the domain, as
`text/plain`, HTTP 200, with no redirect to another domain. Google crawls it by following the
Marketing URL on the App Store listing, so verification cannot even begin until both the
listing and this site are live. Allow about 24 hours after that.

Until it verifies, the game's ad inventory is unverified, and most programmatic demand
discounts it or refuses to bid. It is the single biggest lever on launch-week revenue and it
is not code.

Add a line only when a network is genuinely enabled, and paste what that network's dashboard
generates rather than typing it. A wrong line is worse than a missing one, because it looks
verified and is not.

**`privacy/index.html`** describes what the game actually does today. It named AppLovin until
2026-08-23 and was wrong: the game ships on Google AdMob alone with no mediation. If the
advertising ever changes, this page changes first.

## The check that runs here

    scripts/lint-legal.sh

Cratergut is its own game and owes nothing to anybody else's. Naming the thing it will
inevitably be compared to — in prose, in a comment, in a file name, in an alt attribute — is
how a clean-room product stops being one, and a public web page is the worst place for it,
because a web page is what a search engine reads and what a lawyer is shown.

The game's repository has run this check over its own files for a long time, and it used to
scan the website too, back when the website lived inside it. Moving the site out would have
quietly dropped that coverage from the one place it matters most, so the check came with it.
`scripts/banned-terms.txt` is a copy of the game's list; the game's version has one exemption,
for a generic English noun in a hidden App Store metadata field, and this one has none.

Run it before pushing anything with words in it.

## Setting it up

1. **Settings → Pages** in this repository: source `Deploy from a branch`, branch `main`,
   folder `/ (root)`.
2. **Settings → Pages → Custom domain**: `cratergut.com`. GitHub writes a `CNAME` file; one
   is already committed here, so it should simply agree.
3. **DNS**, at whoever holds cratergut.com. An apex domain needs A records rather than a
   CNAME:

   | Type | Name | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | AAAA | @ | 2606:50c0:8000::153 |
   | AAAA | @ | 2606:50c0:8001::153 |
   | AAAA | @ | 2606:50c0:8002::153 |
   | AAAA | @ | 2606:50c0:8003::153 |
   | CNAME | www | therealcreynold.github.io |

4. **Enforce HTTPS**, back in Settings → Pages. GitHub has to issue a certificate first, so
   the checkbox can take up to 24 hours to become available. Apple will not accept a plain
   HTTP privacy policy URL.

`.nojekyll` is committed deliberately. Without it GitHub runs Jekyll over the repository,
which processes and skips files by rules nobody here has asked for.

## Checking it actually works

Once DNS has propagated, all four of these must return 200 and the last must be `text/plain`:

    curl -sSI https://cratergut.com/
    curl -sSI https://cratergut.com/privacy
    curl -sSI https://cratergut.com/terms
    curl -sSI https://cratergut.com/support
    curl -sS  https://cratergut.com/app-ads.txt

The three page URLs are the ones the game links to from Settings, and the same three go into
App Store Connect as the Privacy Policy, Support and Marketing URLs.
