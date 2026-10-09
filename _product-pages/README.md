# Game product pages

SEO landing pages for the Architect games, one per game, at
`postmarkdigital.com/<slug>/` (e.g. `/airline-architect/`). Their job is to rank in
Google and send people to the App Store.

**One template, one content file per game.** Nothing in `/<slug>/` is hand-edited.

| File | What it is |
|---|---|
| `games/<slug>.json` | Everything game-specific: copy, colors, FAQ, screenshots, image sources |
| `template.html` | The page skeleton (head, SEO tags, header, footer) shared by every game |
| `build.py` | Writes `/<slug>/index.html`, `/<slug>/img/*` and `/sitemap.xml` |
| `/assets/product.css` | Shared styles; each game supplies its own colors via `"theme"` |
| `games/<slug>.sizes.json` | Generated image dimensions (written by `--images`) |

This folder starts with `_`, so GitHub Pages doesn't publish it.

## Build

```bash
python3 _product-pages/build.py --images   # first time, or when screenshots/hero change
python3 _product-pages/build.py            # copy or template changes only
```

`--images` needs Pillow with WebP (the macOS system `python3` has it). It reads the
source PNGs straight from the `~/Architect Universe/...` paths in the JSON, so it only
runs on the studio Mac. The HTML step is standard library only.

## Add a game (Vineyard, FC, …)

1. Copy `games/airline-architect.json` to `games/<new-slug>.json`.
2. Change `slug`, `name`, `appStoreId`, `appStoreUrl`, `campaign`, support/privacy URLs, `icon`,
   `minOS` (the app's deployment target), `languages` (what it ships in, for the structured data) and
   `footerNote` (the game's own "names are used for identification only" line; omit if none).
3. Set `theme` to the game's palette (dark backgrounds work best with the device frames).
4. Rewrite the copy. Any section you delete from the JSON simply isn't rendered.
5. Point `images` at that game's hero art and raw (unframed) App Store captures. For a panorama or
   oversized art, add `"box": [left, top, right, bottom]` (source pixels) to `hero` / `og` to crop first.
6. Run `build.py --images`, preview, then link the game's homepage card to `/<slug>/`.

## Translate a page (e.g. German)

1. Copy `games/<slug>.json` to `games/<slug>.<lang>.json`; keep the same `slug`, add `"lang": "<lang>"`.
2. Translate every string; keep the facts identical. Point `appStoreUrl` at that storefront
   (`apps.apple.com/<cc>/app/...`), give it its own `campaign` (`pmd-web-<slug>-<lang>`), and use that
   language's raw screenshots (they usually show a career in that country).
3. Add the language to `UI` in `build.py` (nav, buttons, footer, legal line, `og_locale`) if it's new, and
   drop Apple's localized badge at `/assets/badges/download-on-the-app-store-<lang>.svg`
   (without it, CTAs fall back to a text button in that language).
4. Build. The page lands at `/<lang>/<slug>/`; every sibling gets reciprocal `hreflang` links
   (x-default = English) and a footer language link, and the sitemap lists it. English-only pages are unchanged.
5. Have a native speaker read it before relying on it.

## App Store reviews section

`reviews/<slug>.json` (optional) adds a "What players say" row above the price card on every page of that app:
selected reviews plus Apple's real rating. `build.py` enforces the rules; the file's `_comment` explains them.

- Only 4- and 5-star reviews that are clearly positive about the app as it is now; a lower rating fails the build.
  Text is verbatim from App Store Connect (`customerReviews`); never edit it.
- A review written in another language shows on other-language pages as a labelled translation with the original
  alongside: add `translations.<lang or locale> = {title, body}`. A page shows nothing if no review exists in its language.
- The average is Apple's own figure for the page's storefront (`ratings.byCountry`, from itunes.apple.com/lookup),
  never an average of the selection and never a blended worldwide figure; below 10 ratings no average is shown.
- The page always says the reviews are a selection and links to all reviews on the App Store (US FTC review rule);
  each card links to its own storefront's reviews. No Review/AggregateRating structured data (Google policy).
- Reviews flagged `priceSensitive` quote a price: re-check them when the price changes.

## SEO rules baked into the template

- **Facts must be checked against the code or the live App Store listing.** The JSON's
  `_comment_facts` says where each number came from. Re-check before reusing a number.
- **No `aggregateRating` in structured data.** Google forbids marking up ratings collected
  on another site (the App Store), and it can trigger a manual penalty.
- **Use raw screenshots, not the framed App Store ones.** Text baked into images isn't
  indexed; the page's HTML carries the words.
- **Title ≤ 60 chars, description ≤ 160.** `build.py` warns when either runs long.
- **Smart App Banner** (`apple-itunes-app`) is on every page, so Safari on iPhone offers the app.
- **Campaign tracking:** set `PROVIDER_TOKEN` in `build.py` (App Store Connect ▸ Analytics ▸
  campaign link generator). Every App Store link then carries `ct=<campaign>` and App
  Analytics shows page → download.
- **Official badge:** Apple's "Download on the App Store" SVG (toolbox.marketingtools.apple.com) lives at
  `/assets/badges/download-on-the-app-store.svg` and every CTA uses it; delete it to fall back to the green button.
