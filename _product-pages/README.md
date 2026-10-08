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
