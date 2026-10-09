# HANDOFF: SEO product pages (start here)

> **New session? Read this first.** It is the current state and what to do next for Postmark Digital's SEO
> product pages. How the system works is in [`README.md`](./README.md) (same folder). This `_` folder is never
> published by GitHub Pages; the repo's ROOT `README.md` *is* public (postmarkdigital.com/README.md), so keep
> anything internal out of the root. **Commit this file with your changes and update §3/§5 in the same commit.**

**Last updated:** 2026-10-08 (late), by the "SEO pages for app store traffic" session, which took over from the
"AA product page SEO strategy" session on 2026-10-07.

**Start the session in `~/Architect Universe/~App Marketing`**: the preview config (`.claude/launch.json`) and the
project memory (`seo-product-pages.md`, `fc-league-logos-accepted-risk.md`) live there. Work on the website by
absolute path.

---

## 1. What this is

One SEO landing page per app at `postmarkdigital.com/<slug>/`, plus `/<lang>/<slug>/` translations. Their **only
job is Google traffic → App Store downloads.** Every App Store link carries `?pt=129166608&ct=pmd-web-<slug>[-<lang>]&mt=8`,
so web-driven downloads show in App Store Connect ▸ Analytics ▸ Acquisition ▸ Campaigns (needs ≥5 accounts to display).

## 2. Where it lives

| | |
|---|---|
| Repo | `spikeatone/postmark-digital-website` (GitHub Pages from `main`, custom domain via `CNAME`; deploys ~40-80 s after a push) |
| Working copy | `~/Architect Universe/Postmark Digital/website-airline-architect`: a **git worktree** of the main checkout (shared `.git`), branch **`product-pages-va-fc`** tracking `origin/main`. On 8 Oct it was level with `origin/main` at `500e83e`. `git status -sb` showing "ahead N" means the designer still has to push |
| Main checkout | `~/Architect Universe/Postmark Digital/website` is BEHIND and has an untracked `assets/logo-on-dark.png` that is **not ours**: don't commit, stash, clean or delete it |
| Push rule | Claude's push to the website repo's `main` was blocked as a production deploy. **Commit locally, then hand the designer:** `git -C ~/"Architect Universe/Postmark Digital/website-airline-architect" push origin product-pages-va-fc:main`. Don't try the push yourself |
| Support/privacy sites | `spikeatone/airline-architect`, `fc-architect`, `vineyard-architect` (github.io). Pushes there went through when the designer asked. Airline's has a hand-kept local copy at `~/Architect Universe/Airline Architect/Website/` that must stay identical; Vineyard's is a clone at `~/Architect Universe/Vineyard Architect/Website/` |
| Preview | `.claude/launch.json` in `~App Marketing` → `product-pages` (python http.server on **8790**, serving the worktree). Port 8765 is the Apple Ads server: don't use it |
| Hand-edited files | The homepage `/index.html`, and in `/fruition/` the files `privacy.html` and `support/`. **Only `/fruition/index.html` and `/fruition/img/` are generated.** Never regenerate or delete the others |

**The change loop:** `git fetch && git rebase origin/main` (a session elsewhere may have pushed) → edit JSON,
template or CSS → build → `git status --short` shows only the pages you meant (build.py rewrites every page +
`sitemap.xml`; English-only pages should be byte-identical after template changes, so diff them) → preview on 8790 →
run the checks in §7 → commit, with this HANDOFF updated → give the designer the push command → after the push,
confirm the live pages with `curl`.

## 3. Live pages (8 Oct 2026)

| App | Pages | Notes |
|---|---|---|
| Airline Architect `6790569697` | `/airline-architect/`, `/de/airline-architect/` | Reviews: 8, **4.2/5 from 17 US ratings** on English; same 8 translated on German (no average: DE has 4 ratings) |
| FC Architect `6798026159` | `/fc-architect/` + `/de/ /fr/ /it/ /es/ /pt/ /nl/fc-architect/` | pt = **European** Portuguese (`"locale": "pt-PT"`). 2 reviews (US, 5★) translated on every page; no average (no storefront has 10+). **Copy reflects 1.9; 1.10 is now live (see §5.1)** |
| Vineyard Architect `6794776474` | `/vineyard-architect/` | English only (the app is English only). No written reviews yet |
| Fruition `6794896515` | `/fruition/`, `/es/fruition/` (Latin American), `/pt/fruition/` (Brazilian) | Non-game (`schemaType`, `applicationCategory`, own CTA labels). Support moved to `/fruition/support/`; `/fruition/` itself stays the ASC support URL (all 9 locales) until the next version; `/fruition/privacy.html` is hard-coded in the app (`PaywallView.swift:31`) |

Sitemap: 16 URLs (3 hand-written + 13 product pages). Homepage cards link each app's page. Pages link
`/assets/product.css?v=<content hash>` (since `500e83e`), so new HTML never meets a cached old stylesheet.

**Known, deliberate:** hreflang uses the bare language (`pt`, `es`) even where the content is regional (FC pt =
pt-PT; Fruition pt = pt-BR, es = LatAm with `og:locale` es_ES). That's fine while each slug has one variant per
language; revisit only before adding a second variant.

## 4. Scheduled tasks

Sidebar ▸ Scheduled. They run only while the Claude app is open; a missed run fires at the next launch. The prompts
are in `~/.claude/scheduled-tasks/<name>/SKILL.md`. Read results there (or with the scheduled-tasks `list_task_runs`
tool); if a run never happened, run it again (`run_scheduled_task`) or follow its SKILL.md by hand.

1. **`gsc-index-pt-fruition`**, 9 Oct 9:00 MDT: requests Google indexing for `/pt/fruition/` and `/de/airline-architect/`.
   Both missed the 8 Oct daily quota, which is about 10 requests a day per property.
2. **`gsc-recheck-product-pages`**, 10 Oct 9:00 MDT: read-only Search Console check of all 13 pages and the sitemap.
   The sitemap still read "Couldn't fetch" after the 7 Oct resubmit, though it serves 200 `application/xml`.

Search Console property: `sc-domain:postmarkdigital.com`. Use **Claude in Chrome** (the designer's signed-in Chrome);
the built-in browser pane is not signed in to Google, and never enter a password.

## 5. Next actions, ranked

1. **FC 1.10 is live (8 Oct, 06:49 UTC)**, with rival-player bids and scout levels. The FC pages still describe 1.9.
   Re-check FC's facts against the 1.10 code (`~/Architect Universe/FC Architect/FCArchitect`, read-only; another
   session owns it) and the live listing. Then add the features to `fc-architect.json` and its 6 translations
   (translator + native reviewer per language), update `_comment_facts`, rebuild and verify. The live 1.10 listing
   uses a "Buying a player" screenshot (`App Store/iPhone 6.9-inch/17-rival-bid.png`) that may now be shown.
2. **Read the 9 Oct and 10 Oct task results** and act on them. Re-request anything that failed (respect the quota),
   and check Google picked each translation's own canonical, not the English page.
3. **ASC marketing URLs.** They can't be edited on a READY_FOR_SALE version (HTTP 409).
   - **Target (confirm with the designer):** each locale's `marketingUrl` = that language's page if one exists,
     else the English page.
   - **FC:** en-US is set on 1.10 (ASC appStoreVersion `2b48a958-d02c-45d1-90ec-3a9139b5e13b`). de-DE, fr-FR, it,
     es-ES, nl-NL and pt-PT are empty: set them to the `/de/`… `/pt/fc-architect/` pages on FC's next version,
     through the FC session.
   - **Airline:** handed to the "AA 1.13.1 and 1.14" session (rides 1.13.1). Confirm, and ask for de-DE → `/de/airline-architect/`.
   - **Vineyard and Fruition:** set on each app's next version. Fruition's **supportUrl** should become
     `https://postmarkdigital.com/fruition/support/` then too.
   - **Reaching the sessions:** use ListAgents/SendMessage by name. If they aren't running, check the field
     yourself: `cd ~/Architect\ Universe/~PostmarkOps/ASCTools && python3 asc.py GET "/v1/apps/<id>/appStoreVersions?limit=3"`,
     then that version's `appStoreVersionLocalizations`.
4. **Native-speaker reads** of the translated pages and reviews (de, fr, it, es, pt-PT, nl, LatAm es, pt-BR) **before
   pointing ads, ASC marketing URLs or other links at them**. They're already live and indexed. Agents wrote and
   reviewed them; no human has. Who does the reads is the designer's call; don't commission anything.
5. **Refresh reviews** about monthly, and after each release. New 4-5★ reviews appear, and an average turns on once a
   storefront reaches 10 ratings. Recipe in §7.
6. **Measure before adding more** (around 5 Nov 2026): compare Search Console ▸ Performance for the translations
   against their English twins. Candidates:
   - **Fruition in French and Simplified Chinese** (the app ships both). zh-Hans also needs a `zh-Hans` UI entry,
     Apple's Chinese badge (download needs the designer's OK) and a folder choice (`/zh-hans/`).
   - **Airline in more languages:** the app ships English and German only, so the listing language would lag.
   - **Long-tail guide pages,** e.g. "leasing vs buying aircraft".

**Whenever any app ships a version:** re-check that page's `_comment_facts` numbers against the new code and live
listing; refresh screenshots if the listing changed; refresh reviews; confirm the marketing URL.

## 6. Decisions and rules (keep unless the designer changes them)

- **Facts come from the app's CODE and the LIVE listing.** Record sources in each JSON's `_comment_facts`. Docs drift:
  Airline's docs said 380/447 airports, but the code and listing said 469. Don't advertise features that are merged
  but not shipped: FC 1.10's bids and scouts were left out until 1.10 went live on 8 Oct.
- **SEO:**
  - full-brand slug URLs on the studio domain;
  - raw (unframed) screenshots, with alt text describing what's actually on screen;
  - Organization + WebPage + VideoGame/MobileApplication + FAQPage JSON-LD;
  - **never aggregateRating or Review markup** (the ratings come from the App Store, and Google forbids that).
- **Copy:**
  - plain, specific, no em dashes;
  - real aircraft names are approved; club and league names are for identification only;
  - keep top-flight league trademarks (Premier League, Bundesliga, LaLiga, Serie A, Ligue 1, Eredivisie, Liga Portugal) out of titles and headings;
  - never show league logos. FC ships real league logos in the app, and the designer accepted that risk on 7 Oct.
    Don't re-raise it unless there's a complaint, an App Review 5.2.1 note, or a new FC release that touches the
    welcome map or league picker.
- **Fruition:**
  - no health, wellness or therapy claims, and no weight or sleep examples;
  - don't lead with AI (the owner's call, 24 Aug), but the FAQ discloses Claude honestly;
  - prices appear in USD on the English page only.
- **Reviews section.** `build.py` enforces:
  - 4-5★ only (a lower rating fails the build);
  - the average is Apple's real figure for the page's storefront, shown only with 10+ ratings: never an average of the selection, never a blended worldwide figure;
  - the "a selection of 4- and 5-star reviews" note and the all-reviews link always show with the section (US FTC rule, 16 CFR 465);
  - translations are labelled, with the original alongside.

  **Curation rules** (yours; the code can't check them):
  - only clearly positive reviews about the app as it is now;
  - text verbatim from App Store Connect (the build only collapses runs of spaces);
  - each `reviews/<slug>.json` `_comment` lists the excluded reviews and why;
  - the designer accepted leaving out FC's two French 4★ reviews, which mainly object to the €6.99 price.
- **Privacy pages and App Privacy labels match the code (7-8 Oct).**
  - The Airline, FC, Vineyard and Fruition policies disclose TelemetryDeck (all default SDK fields), MetricKit
    crash/hang reports where the app has them (FC doesn't), Game Center, etc.
  - Vineyard's and Fruition's App Store labels also declare Diagnostics (Crash Data + Performance Data, App
    Functionality, not linked).
  - Never write "no analytics".

## 7. How to (the non-obvious bits)

- **Build:** `/usr/bin/python3 _product-pages/build.py`. Add `--images` when art or screenshots change. System
  python is 3.9, so no 3.10+ syntax. **After editing `/assets/product.css`, always rebuild:** pages link
  `product.css?v=<content hash>`, and the hash only changes on a build.
- **Checks (not automated; run them by hand before committing):**
  - `grep -c '<h1'` = 1 per page and `grep -c '—'` = 0;
  - every `<img>` has `alt`;
  - parse each `application/ld+json` with `json.loads`;
  - title ≤60 and description ≤160 (build.py warns);
  - every sibling lists every hreflang;
  - internal links and image paths exist;
  - at **375 px and 320 px**, `document.documentElement.scrollWidth <= innerWidth`. The browser pane's "mobile"
    preset renders **408 px**, so use an exact `resize_window` 375×812 or an off-screen iframe, and cache-bust the
    CSS in the preview.
- **Translate a page** (also see README "Translate a page"):
  1. Add `games/<slug>.<lang>.json` with the same slug and `"lang"`, plus `"locale"` (e.g. `pt-PT`) when the
     regional variant differs from build.py's default.
  2. A new language needs `UI`, and if the app has reviews also `REVIEW_UI` and `RATING_STOREFRONT` entries, in
     `build.py`, plus Apple's localized badge in `/assets/badges/`. Downloads need the designer's OK.
  3. If the app has reviews, add `translations.<locale or lang>` to every review in `reviews/<slug>.json`. Otherwise
     the new page silently shows no reviews.

  On 8 Oct this was done, with the user's OK, as a Workflow: one translator plus one native-reviewer agent per page,
  each writing only its own JSON, then a single build. The script wasn't saved; recreate it, or use two subagents.
  Workflows need the user's opt-in.
- **Refresh reviews:**
  1. `cd ~/Architect\ Universe/~PostmarkOps/ASCTools && python3 asc.py GET "/v1/apps/<id>/customerReviews?limit=200&sort=-createdDate" --all`.
  2. Ratings: `https://itunes.apple.com/lookup?id=<id>&country=<cc>` for at least every storefront a page shows
     (US DE FR IT ES BR PT NL). A full 175-territory sweep is optional: ASC `/v1/territories` lists ISO3, while
     lookup wants ISO2, so map them.
  3. Curate into `reviews/<slug>.json` (`country` as ISO2). Update `ratings.asOf` and the `_comment` (date and
     exclusions), and flag price-quoting reviews `priceSensitive`.
  4. Translate new ones (translator + verifier per language), then rebuild.
- **Search Console:**
  - The "Inspect any URL" box is flaky: click it by coordinates (twice if a popup is open), zoom to confirm the
    text, then press Return.
  - Click "REQUEST INDEXING" by **coordinates**: `find` refs can point at stale hidden copies.
  - Direct `/inspect?id=` URLs return 404.
- **App Store Connect writes** (privacy labels, metadata) were done in Chrome at the designer's request. ASC API
  calls through ASCTools are read-only here. Never print the `.p8`.
- **Keep other docs in step** when state changes: project memory `seo-product-pages.md`, and PostmarkOps
  `PORTFOLIO.md`'s product-pages lines (commit only; never push PostmarkOps, see §8).

## 8. Open items owned by other sessions (FYI)

- **Airline de-DE listing** (sent to "AA 1.13.1 and 1.14" for 1.13.1): "25-Fache" → 100×, and "20 Millionen Dollar"
  (the game shows €). Also sent as FYIs: the promo says "every US route"; an untranslated "36 of 37 types" in the
  German route planner.
- **Fruition app:** coach tone and reminder-window labels are hard-coded English in every locale (`CoachTone.swift`).
- **PostmarkOps:** `PORTFOLIO.md` has a local, **unpushed** commit (`5ee94eb`, the product-pages lines) sitting on two
  other sessions' unpushed commits. Whoever owns those pushes them together. It predates the translations and reviews.
