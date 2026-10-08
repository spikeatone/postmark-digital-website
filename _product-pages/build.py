#!/usr/bin/env python3
"""Build the game product pages (postmarkdigital.com/<slug>/) and sitemap.xml.

    python3 _product-pages/build.py            # rebuild every page's HTML + sitemap.xml
    python3 _product-pages/build.py --images   # also re-export hero/OG/screenshot images

One template (template.html) + one content file per game (games/<slug>.json).
The HTML step is standard library only. --images needs Pillow with WebP support
(the macOS system python3 has it).

Generated files — edit the JSON/template, never these:
    <slug>/index.html, <slug>/img/*, sitemap.xml, games/<slug>.sizes.json
Folders starting with "_" are not published by GitHub Pages (Jekyll skips them).
"""
import html
import json
import os
import re
import sys

SITE = "https://postmarkdigital.com"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# App Store Connect ▸ Analytics ▸ "Campaign link" generator shows the provider token
# (pt). With it, every App Store link carries ct=<campaign> and App Analytics
# reports page → download. Empty = plain links (they still work, just untracked).
PROVIDER_TOKEN = "129166608"

# Hand-written pages that belong in the sitemap. Concept/client pages are left out on purpose.
STATIC_PAGES = ["/", "/fruition/support/", "/foundry/"]  # /fruition/ itself is generated

TITLE_MAX, DESC_MAX = 60, 160

# Per-language interface strings. A page's JSON may set "lang" (default "en"). A translation of a
# page is games/<slug>.<lang>.json with the SAME "slug"; it is published at /<lang>/<slug>/ and
# linked to its siblings with hreflang (x-default = the English page). "badge" is Apple's official
# badge for that language; if the file is missing, CTAs fall back to a text button in that language.
UI = {
    "en": {
        "badge": "/assets/badges/download-on-the-app-store.svg",
        "badge_alt": "Download %s on the App Store", "btn": "Download free on the App Store",
        "header_cta": "Get the game", "explore": "See how it plays",
        "related": "More from the Architect series", "faq": "%s FAQ", "stats_aria": "At a glance",
        "nav_features": "Features", "nav_price": "Price", "nav_faq": "FAQ",
        "home_aria": "Postmark Digital home", "links_aria": "%s links", "icon_alt": "%s app icon",
        "support": "Support", "privacy": "Privacy policy", "contact": "Contact",
        "legal": "&copy; 2026 Postmark Digital, LLC. All rights reserved. Apple, iPhone, iPad and App Store are trademarks of Apple Inc.",
        "og_locale": "en_US", "name": "English",
    },
    "de": {
        "badge": "/assets/badges/download-on-the-app-store-de.svg",
        "badge_alt": "%s im App Store laden", "btn": "Kostenlos im App Store laden",
        "header_cta": "Spiel laden", "explore": "So spielt es sich",
        "related": "Mehr aus der Architect-Reihe", "faq": "Häufige Fragen zu %s", "stats_aria": "Auf einen Blick",
        "nav_features": "Funktionen", "nav_price": "Preis", "nav_faq": "FAQ",
        "home_aria": "Startseite von Postmark Digital", "links_aria": "Links zu %s", "icon_alt": "App-Icon von %s",
        "support": "Support", "privacy": "Datenschutz", "contact": "Kontakt",
        "legal": "&copy; 2026 Postmark Digital, LLC. Alle Rechte vorbehalten. Apple, iPhone, iPad und App Store sind Marken von Apple Inc.",
        "og_locale": "de_DE", "name": "Deutsch",
    },
}


def lang(game):
    return game.get("lang", "en")


def ui(game):
    return UI[lang(game)]


def page_path(game):
    """/<slug>/ for English, /<lang>/<slug>/ for a translation."""
    return "/%s/" % game["slug"] if lang(game) == "en" else "/%s/%s/" % (lang(game), game["slug"])


def out_dir(game):
    return os.path.join(ROOT, page_path(game).strip("/"))


def e(text):
    return html.escape(str(text), quote=True)


def render(template, ctx):
    def sub(m):
        key = m.group(1)
        if key not in ctx:
            raise KeyError("template placeholder {{%s}} has no value" % key)
        return ctx[key]
    return re.sub(r"\{\{(\w+)\}\}", sub, template)


def app_store_link(game):
    url = game["appStoreUrl"]
    if PROVIDER_TOKEN:
        url += "?pt=%s&ct=%s&mt=8" % (PROVIDER_TOKEN, game["campaign"])
    return url


# ----------------------------------------------------------------- images

def export_images(game):
    from PIL import Image  # only needed for --images
    Image.MAX_IMAGE_PIXELS = None  # local studio art; some panoramas are ~100 MP

    out = os.path.join(out_dir(game), "img")
    os.makedirs(out, exist_ok=True)
    spec = game["images"]
    sizes = {}

    def src(path, box=None):
        # Optional "box": [left, top, right, bottom] in source pixels, e.g. a 16:9 window on a panorama.
        im = Image.open(os.path.expanduser(path))
        return (im.crop(tuple(box)) if box else im).convert("RGB")

    hero = src(spec["hero"]["src"], spec["hero"].get("box"))
    for w in spec["hero"]["widths"]:
        h = round(hero.height * w / hero.width)
        name = "hero-%d.webp" % w
        hero.resize((w, h), Image.LANCZOS).save(os.path.join(out, name), "WEBP",
                                                 quality=spec["hero"]["quality"], method=6)
        sizes[name] = [w, h]

    # Open Graph: centre-crop to 1200x630, saved as JPEG (every link-preview bot reads it).
    ow, oh = spec["og"]["crop"]
    og = src(spec["og"]["src"], spec["og"].get("box"))
    scale = max(ow / og.width, oh / og.height)
    og = og.resize((round(og.width * scale), round(og.height * scale)), Image.LANCZOS)
    left, top = (og.width - ow) // 2, (og.height - oh) // 2
    og.crop((left, top, left + ow, top + oh)).save(os.path.join(out, "og.jpg"), "JPEG",
                                                   quality=84, optimize=True, progressive=True)
    sizes["og.jpg"] = [ow, oh]

    for key, path in spec["shots"].items():
        # A shot is a path, or {"src": path, "box": [left, top, right, bottom]} to trim it first
        # (e.g. the iPad window-resize grabber in a corner).
        im = src(path["src"], path.get("box")) if isinstance(path, dict) else src(path)
        w = spec["ipadWidth"] if key == "ipad" else spec["shotWidth"]
        h = round(im.height * w / im.width)
        name = "shot-%s.webp" % key
        im.resize((w, h), Image.LANCZOS).save(os.path.join(out, name), "WEBP", quality=80, method=6)
        sizes[name] = [w, h]

    with open(sizes_path(game), "w") as f:
        json.dump(sizes, f, indent=2, sort_keys=True)
        f.write("\n")
    print("  images → %simg/ (%d files)" % (page_path(game).lstrip("/"), len(sizes)))


def sizes_path(game):
    suffix = "" if lang(game) == "en" else "." + lang(game)
    return os.path.join(HERE, "games", game["slug"] + suffix + ".sizes.json")


# --------------------------------------------------------------- fragments

def img(sizes, name, alt, cls="", lazy=True, extra=""):
    w, h = sizes[name]
    attrs = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high" decoding="async"'
    cls = ' class="%s"' % cls if cls else ""
    return '<img%s src="img/%s" width="%d" height="%d" alt="%s"%s%s>' % (cls, name, w, h, e(alt), attrs, extra)


def phone(sizes, shot, alt, lazy=True):
    return '<figure class="phone">%s</figure>' % img(sizes, "shot-%s.webp" % shot, alt, lazy=lazy)


def cta_button(game, where="hero"):
    href = e(app_store_link(game))
    badge = ui(game)["badge"]
    if os.path.exists(os.path.join(ROOT, badge.lstrip("/"))):
        return ('<a class="badge-link" href="%s" data-cta="%s"><img src="%s" width="162" height="54" '
                'alt="%s"></a>' % (href, where, badge, e(ui(game)["badge_alt"] % game["name"])))
    return '<a class="btn btn--cta" href="%s" data-cta="%s">%s</a>' % (href, where, e(ui(game)["btn"]))


def hero_block(game, sizes):
    h = game["hero"]
    srcset = ", ".join("img/%s %dw" % (n, sizes[n][0]) for n in sorted(sizes) if n.startswith("hero-"))
    first = sorted(n for n in sizes if n.startswith("hero-"))[0]
    w, hh = sizes[first]
    chips = "".join("<li>%s</li>" % e(c) for c in h["chips"])
    # The art sits on the right (object-position from the JSON keeps its subject clear of the copy).
    return """
<section class="hero">
  <div class="hero__media"><img class="hero__bg" src="img/{first}" srcset="{srcset}" sizes="(max-width: 960px) 100vw, 62vw" width="{w}" height="{hh}" alt="{alt}" style="object-position:{pos}" fetchpriority="high" decoding="async"></div>
  <div class="hero__inner">
    <div class="hero__copy">
      <img class="hero__icon" src="{icon}" width="88" height="88" alt="{icon_alt}">
      <h1 class="hero__title">{h1}<span>{sub}</span></h1>
      <p class="hero__lede">{lede}</p>
      <div class="hero__actions">{cta}<a class="btn btn--ghost" href="#features">{explore}</a></div>
      <ul class="chips">{chips}</ul>
    </div>
  </div>
</section>""".format(first=first, srcset=srcset, w=w, hh=hh, alt=e(h["imageAlt"]), pos=e(h.get("imagePosition", "50% 50%")),
                     icon=e(game["icon"]), icon_alt=e(ui(game)["icon_alt"] % game["name"]), h1=e(h["h1"]), sub=e(h["h1Sub"]),
                     lede=e(h["lede"]), cta=cta_button(game), chips=chips,
                     explore=e(game.get("exploreLabel", ui(game)["explore"])))


def stats_block(game):
    items = "".join('<li><strong>%s</strong><span>%s</span></li>' % (e(s["value"]), e(s["label"]))
                    for s in game.get("stats", []))
    return ('<section class="stats" aria-label="%s"><ul>%s</ul></section>' % (e(ui(game)["stats_aria"]), items)
            if items else "")


def intro_block(game):
    i = game.get("intro")
    if not i:
        return ""
    paras = "".join("<p>%s</p>" % e(p) for p in i["paragraphs"])
    return '<section class="intro wrap" id="features"><h2>%s</h2>%s</section>' % (e(i["h2"]), paras)


def highlights_block(game, sizes):
    rows = []
    for n, h in enumerate(game.get("highlights", [])):
        rows.append("""
  <article class="row{flip}">
    <div class="row__media">{phone}</div>
    <div class="row__copy">
      <p class="eyebrow">{eyebrow}</p>
      <h2>{h2}</h2>
      <p>{body}</p>
    </div>
  </article>""".format(flip=" row--flip" if n % 2 else "", phone=phone(sizes, h["shot"], h["alt"]),
                       eyebrow=e(h["eyebrow"]), h2=e(h["h2"]), body=e(h["body"])))
    return '<section class="rows wrap">%s\n</section>' % "".join(rows) if rows else ""


def details_block(game, sizes):
    d = game.get("details")
    if not d:
        return ""
    cards = "".join("""
    <article class="card card--shot">{phone}<div><h3>{h3}</h3><p>{body}</p></div></article>""".format(
        phone=phone(sizes, it["shot"], it["alt"]), h3=e(it["h3"]), body=e(it["body"])) for it in d["items"])
    return '<section class="details wrap"><h2>%s</h2><div class="grid grid--2">%s\n</div></section>' % (e(d["h2"]), cards)


def world_block(game):
    w = game.get("world")
    if not w:
        return ""
    cards = "".join('<article class="card"><h3>%s</h3><p>%s</p></article>' % (e(it["h3"]), e(it["body"]))
                    for it in w["items"])
    return '<section class="world wrap"><h2>%s</h2><div class="grid grid--2">%s</div></section>' % (e(w["h2"]), cards)


def devices_block(game, sizes):
    d = game.get("devices")
    if not d:
        return ""
    bullets = "".join("<li>%s</li>" % e(b) for b in d["bullets"])
    return """
<section class="devices wrap">
  <div class="devices__copy"><h2>{h2}</h2><p>{body}</p><ul class="ticks">{bullets}</ul></div>
  <figure class="tablet">{img}</figure>
</section>""".format(h2=e(d["h2"]), body=e(d["body"]), bullets=bullets,
                     img=img(sizes, "shot-%s.webp" % d["shot"], d["alt"]))


def pricing_block(game):
    p = game.get("pricing")
    if not p:
        return ""
    bullets = "".join("<li>%s</li>" % e(b) for b in p["bullets"])
    return """
<section class="pricing wrap" id="pricing">
  <div class="pricing__card">
    <h2>{h2}</h2><p>{body}</p><ul class="ticks">{bullets}</ul>{cta}
  </div>
</section>""".format(h2=e(p["h2"]), body=e(p["body"]), bullets=bullets, cta=cta_button(game, where="pricing"))


def faq_block(game):
    items = "".join('<details><summary><h3>%s</h3></summary><p>%s</p></details>' % (e(f["q"]), e(f["a"]))
                    for f in game.get("faq", []))
    if not items:
        return ""
    return '<section class="faq wrap" id="faq"><h2>%s</h2>%s</section>' % (e(ui(game)["faq"] % game["name"]), items)


def cta_block(game):
    c = game["cta"]
    return """
<section class="final">
  <div class="final__inner wrap"><h2>{h2}</h2><p>{body}</p>{cta}</div>
</section>""".format(h2=e(c["h2"]), body=e(c["body"]), cta=cta_button(game, where="final"))


def related_block(game):
    cards = "".join("""
    <a class="related__card" href="{url}"><img src="{icon}" width="64" height="64" alt="" loading="lazy"><span><strong>{name}</strong>{blurb}</span></a>""".format(
        url=e(r["url"]), icon=e(r["icon"]), name=e(r["name"]), blurb=e(r["blurb"])) for r in game.get("related", []))
    if not cards:
        return ""
    heading = game.get("relatedHeading", ui(game)["related"])
    return '<section class="related wrap"><h2>%s</h2><div class="grid grid--2">%s\n</div></section>' % (e(heading), cards)


# ------------------------------------------------------------- structured

def json_ld(game, sizes):
    page = SITE + page_path(game)
    org = {"@type": "Organization", "@id": SITE + "/#org", "name": "Postmark Digital",
           "url": SITE + "/", "logo": SITE + "/assets/logo.svg"}
    # Games are VideoGame + MobileApplication; a non-game app sets "schemaType" (e.g. "MobileApplication")
    # and "applicationCategory" (e.g. "LifestyleApplication") in its JSON.
    types = game.get("schemaType", ["VideoGame", "MobileApplication"])
    is_game = "VideoGame" in (types if isinstance(types, list) else [types])
    app = {
        "@type": types,
        "@id": page + "#app",
        "name": game["name"],
        "description": game["seo"]["description"],
        "url": page,
        "image": page + "img/og.jpg",
        "screenshot": [page + "img/shot-%s.webp" % h["shot"] for h in game["highlights"]],
        "operatingSystem": "iOS {v} or later, iPadOS {v} or later".format(v=game["minOS"]),
        "applicationCategory": game.get("applicationCategory", "GameApplication"),
        "genre": game["seo"]["genre"],
        **({"gamePlatform": ["iPhone", "iPad"], "playMode": "SinglePlayer"} if is_game else {}),
        "inLanguage": game["languages"],
        "installUrl": game["appStoreUrl"],
        "sameAs": [game["appStoreUrl"]],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD",
                   "availability": "https://schema.org/InStock", "url": game["appStoreUrl"]},
        "publisher": {"@id": SITE + "/#org"},
        "author": {"@id": SITE + "/#org"},
        # No aggregateRating on purpose: Google forbids marking up ratings collected
        # on another site (the App Store), and it can trigger a manual action.
    }
    crumbs = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Postmark Digital", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": game["name"], "item": page}]}
    webpage = {"@type": "WebPage", "@id": page, "url": page, "name": game["seo"]["title"],
               "description": game["seo"]["description"], "about": {"@id": page + "#app"},
               "breadcrumb": crumbs, "isPartOf": {"@type": "WebSite", "url": SITE + "/", "name": "Postmark Digital"}}
    if lang(game) != "en":
        webpage["inLanguage"] = lang(game)
    graph = [org, webpage, app]
    if game.get("faq"):
        graph.append({"@type": "FAQPage", "@id": page + "#faq", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
            for f in game["faq"]]})
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)
    return data.replace("</", "<\\/")


def theme_css(game):
    t = game["theme"]
    names = {"bg": "--bg", "bgAlt": "--bg-alt", "surface": "--surface", "border": "--border", "ink": "--ink",
             "inkSoft": "--ink-soft", "accent": "--accent", "cta": "--cta", "ctaInk": "--cta-ink", "ctaHover": "--cta-hover"}
    return ":root{%s}" % ";".join("%s:%s" % (names[k], v) for k, v in t.items())


# ------------------------------------------------------------------- build

def alternates_block(game, siblings):
    """hreflang links (+ og:locale) and footer language links for a page with translations."""
    if len(siblings) < 2:
        return "", ""
    head = ['  <link rel="alternate" hreflang="%s" href="%s%s">' % (l, SITE, path) for l, path in siblings]
    head.append('  <link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, dict(siblings)["en"]))
    head.append('  <meta property="og:locale" content="%s">' % UI[lang(game)]["og_locale"])
    head += ['  <meta property="og:locale:alternate" content="%s">' % UI[l]["og_locale"]
             for l, _ in siblings if l != lang(game)]
    links = "".join('\n      <a href="%s" hreflang="%s" lang="%s">%s</a>' % (path, l, l, UI[l]["name"])
                    for l, path in siblings if l != lang(game))
    return "\n" + "\n".join(head), links


def build_page(game, template, siblings=()):
    seo = game["seo"]
    for label, text, limit in (("title", seo["title"], TITLE_MAX), ("description", seo["description"], DESC_MAX)):
        if len(text) > limit:
            print("  ! %s is %d chars (Google truncates past ~%d): %s" % (label, len(text), limit, text))
    if not os.path.exists(sizes_path(game)):
        sys.exit("No image sizes for %s — run with --images first." % game["slug"])
    sizes = json.load(open(sizes_path(game)))
    page = SITE + page_path(game)
    u = ui(game)
    alternates, lang_links = alternates_block(game, list(siblings))
    ctx = {
        "lang": lang(game),
        "alternates": alternates,
        "lang_links": lang_links,
        "nav_features": e(u["nav_features"]), "nav_price": e(u["nav_price"]), "nav_faq": e(u["nav_faq"]),
        "home_aria": e(u["home_aria"]), "links_aria": e(u["links_aria"] % game["name"]),
        "support_label": e(u["support"]), "privacy_label": e(u["privacy"]), "contact_label": e(u["contact"]),
        "legal": u["legal"],
        "title": e(seo["title"]),
        "description": e(seo["description"]),
        "canonical": page,
        "og_image": page + "img/og.jpg",
        "og_image_alt": e(seo["ogImageAlt"]),
        "app_store_id": e(game["appStoreId"]),
        "icon": e(game["icon"]),
        "theme_color": e(game["theme"]["bg"]),
        "theme_css": theme_css(game),
        "json_ld": json_ld(game, sizes),
        "name": e(game["name"]),
        "header_cta": '<a class="btn btn--cta btn--small" href="%s" data-cta="header">%s</a>' % (
            e(app_store_link(game)), e(game.get("headerCtaLabel", u["header_cta"]))),
        "hero": hero_block(game, sizes),
        "stats": stats_block(game),
        "intro": intro_block(game),
        "highlights": highlights_block(game, sizes),
        "details": details_block(game, sizes),
        "world": world_block(game),
        "devices": devices_block(game, sizes),
        "pricing": pricing_block(game),
        "faq": faq_block(game),
        "final_cta": cta_block(game),
        "related": related_block(game),
        "support_url": e(game["supportUrl"]),
        "privacy_url": e(game["privacyUrl"]),
        "footer_note": (" " + e(game["footerNote"])) if game.get("footerNote") else "",
    }
    out = out_dir(game)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(render(template, ctx))
    print("  page   → %sindex.html" % page_path(game).lstrip("/"))
    return page_path(game)


def write_sitemap(paths):
    urls = "".join("  <url><loc>%s%s</loc></url>\n" % (SITE, p) for p in paths)
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls)
    print("  sitemap.xml (%d URLs)" % len(paths))


def main():
    with_images = "--images" in sys.argv[1:]
    template = open(os.path.join(HERE, "template.html")).read()
    games_dir = os.path.join(HERE, "games")
    paths = list(STATIC_PAGES)
    games = [json.load(open(os.path.join(games_dir, n))) for n in sorted(os.listdir(games_dir))
             if n.endswith(".json") and not n.endswith(".sizes.json")]
    # Translations of one page share a slug; each lists all of them (English first) for hreflang.
    family = {}
    for g in games:
        family.setdefault(g["slug"], []).append((lang(g), page_path(g)))
    for sibs in family.values():
        sibs.sort(key=lambda x: (x[0] != "en", x[0]))
    for game in games:
        print(game["name"] + ("" if lang(game) == "en" else " (%s)" % lang(game)))
        if with_images:
            export_images(game)
        paths.append(build_page(game, template, family[game["slug"]]))
    write_sitemap(paths)


if __name__ == "__main__":
    main()
