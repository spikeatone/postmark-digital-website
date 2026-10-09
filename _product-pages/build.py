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
    "es": {
        "badge": "/assets/badges/download-on-the-app-store-es.svg",
        "badge_alt": "Descarga %s en el App Store", "btn": "Descarga gratis en el App Store",
        "header_cta": "Descargar el juego", "explore": "Así se juega",
        "related": "Más de la serie Architect", "faq": "Preguntas frecuentes sobre %s", "stats_aria": "De un vistazo",
        "nav_features": "Funciones", "nav_price": "Precio", "nav_faq": "Preguntas",
        "home_aria": "Inicio de Postmark Digital", "links_aria": "Enlaces de %s", "icon_alt": "Icono de la app %s",
        "support": "Soporte", "privacy": "Privacidad", "contact": "Contacto",
        "legal": "&copy; 2026 Postmark Digital, LLC. Todos los derechos reservados. Apple, iPhone, iPad y App Store son marcas comerciales de Apple Inc.",
        "og_locale": "es_ES", "name": "Español",
    },
    "pt": {  # Brazilian Portuguese (the default for "pt")
        "badge": "/assets/badges/download-on-the-app-store-pt-br.svg",
        "badge_alt": "Baixe %s na App Store", "btn": "Baixe grátis na App Store",
        "header_cta": "Baixar o jogo", "explore": "Veja como se joga",
        "related": "Mais da série Architect", "faq": "Perguntas frequentes sobre %s", "stats_aria": "Em resumo",
        "nav_features": "Recursos", "nav_price": "Preço", "nav_faq": "Perguntas",
        "home_aria": "Página inicial da Postmark Digital", "links_aria": "Links de %s", "icon_alt": "Ícone do app %s",
        "support": "Suporte", "privacy": "Privacidade", "contact": "Contato",
        "legal": "&copy; 2026 Postmark Digital, LLC. Todos os direitos reservados. Apple, iPhone, iPad e App Store são marcas registradas da Apple Inc.",
        "og_locale": "pt_BR", "name": "Português",
    },
    "pt-PT": {  # European Portuguese: a page with "lang": "pt" picks it with "locale": "pt-PT"
        "badge": "/assets/badges/download-on-the-app-store-pt-pt.svg",
        "badge_alt": "Descarregue %s na App Store", "btn": "Descarregue grátis na App Store",
        "header_cta": "Obter o jogo", "explore": "Veja como se joga",
        "related": "Mais da série Architect", "faq": "Perguntas frequentes sobre %s", "stats_aria": "Em resumo",
        "nav_features": "Funcionalidades", "nav_price": "Preço", "nav_faq": "Perguntas",
        "home_aria": "Página inicial da Postmark Digital", "links_aria": "Ligações de %s", "icon_alt": "Ícone da app %s",
        "support": "Suporte", "privacy": "Privacidade", "contact": "Contacto",
        "legal": "&copy; 2026 Postmark Digital, LLC. Todos os direitos reservados. Apple, iPhone, iPad e App Store são marcas comerciais da Apple Inc.",
        "og_locale": "pt_PT", "name": "Português",
    },
    "fr": {
        "badge": "/assets/badges/download-on-the-app-store-fr.svg",
        "badge_alt": "Télécharger %s dans l'App Store", "btn": "Télécharger gratuitement dans l'App Store",
        "header_cta": "Obtenir le jeu", "explore": "Découvrir le jeu",
        "related": "Également dans la série Architect", "faq": "Questions fréquentes sur %s", "stats_aria": "En bref",
        "nav_features": "Fonctionnalités", "nav_price": "Prix", "nav_faq": "FAQ",
        "home_aria": "Accueil Postmark Digital", "links_aria": "Liens de %s", "icon_alt": "Icône de l'app %s",
        "support": "Assistance", "privacy": "Confidentialité", "contact": "Contact",
        "legal": "&copy; 2026 Postmark Digital, LLC. Tous droits réservés. Apple, iPhone, iPad et App Store sont des marques d'Apple Inc.",
        "og_locale": "fr_FR", "name": "Français",
    },
    "it": {
        "badge": "/assets/badges/download-on-the-app-store-it.svg",
        "badge_alt": "Scarica %s su App Store", "btn": "Scarica gratis su App Store",
        "header_cta": "Scarica il gioco", "explore": "Scopri come si gioca",
        "related": "Altri titoli della serie Architect", "faq": "Domande frequenti su %s", "stats_aria": "In breve",
        "nav_features": "Funzioni", "nav_price": "Prezzo", "nav_faq": "FAQ",
        "home_aria": "Home di Postmark Digital", "links_aria": "Link di %s", "icon_alt": "Icona dell'app %s",
        "support": "Assistenza", "privacy": "Privacy", "contact": "Contatti",
        "legal": "&copy; 2026 Postmark Digital, LLC. Tutti i diritti riservati. Apple, iPhone, iPad e App Store sono marchi di Apple Inc.",
        "og_locale": "it_IT", "name": "Italiano",
    },
    "nl": {
        "badge": "/assets/badges/download-on-the-app-store-nl.svg",
        "badge_alt": "Download %s in de App Store", "btn": "Gratis downloaden in de App Store",
        "header_cta": "Download de game", "explore": "Zo speel je het",
        "related": "Meer uit de Architect-serie", "faq": "Veelgestelde vragen over %s", "stats_aria": "In het kort",
        "nav_features": "Functies", "nav_price": "Prijs", "nav_faq": "FAQ",
        "home_aria": "Homepage van Postmark Digital", "links_aria": "Links van %s", "icon_alt": "App-icoon van %s",
        "support": "Support", "privacy": "Privacy", "contact": "Contact",
        "legal": "&copy; 2026 Postmark Digital, LLC. Alle rechten voorbehouden. Apple, iPhone, iPad en App Store zijn handelsmerken van Apple Inc.",
        "og_locale": "nl_NL", "name": "Nederlands",
    },
}


# Review-section strings, per UI language (added as each language gets reviews).
REVIEW_UI = {
    "en": {
        "h2": "What players say", "h2_app": "What people say",
        "note": "A selection of 4- and 5-star reviews from the App Store.",
        "out_of": "out of 5", "store": "%(n)s ratings on the App Store (%(cc)s), %(when)s",
        "see_all": "See all ratings and reviews on the App Store (%s)", "card_link": "Read it on the App Store (%s)",
        "stars": "%s out of 5 stars",
        "more": "Read more", "less": "Show less", "show_orig": "Show original", "hide_orig": "Hide original",
        "region": "Reviews", "prev": "Previous reviews", "next": "Next reviews", "decimal": ".",
        "translated": {"en": "Translated from English", "de": "Translated from German", "fr": "Translated from French",
                       "it": "Translated from Italian", "es": "Translated from Spanish", "pt": "Translated from Portuguese",
                       "nl": "Translated from Dutch"},
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "countries": {"US": "United States", "GB": "United Kingdom", "DE": "Germany", "FR": "France", "IT": "Italy",
                      "ES": "Spain", "PT": "Portugal", "NL": "Netherlands", "AU": "Australia", "CA": "Canada",
                      "BR": "Brazil", "MX": "Mexico"},
    },
    "de": {
        "h2": "Das sagen Spieler", "h2_app": "Das sagen Nutzer",
        "note": "Eine Auswahl von 4- und 5-Sterne-Bewertungen aus dem App Store.",
        "out_of": "von 5", "store": "%(n)s Bewertungen im App Store (%(cc)s), %(when)s",
        "see_all": "Alle Bewertungen im App Store (%s)", "card_link": "Im App Store lesen (%s)",
        "stars": "%s von 5 Sternen",
        "more": "Weiterlesen", "less": "Weniger anzeigen", "show_orig": "Original anzeigen", "hide_orig": "Original ausblenden",
        "region": "Bewertungen", "prev": "Vorherige Bewertungen", "next": "Nächste Bewertungen", "decimal": ",",
        "translated": {"en": "Aus dem Englischen übersetzt", "de": "Aus dem Deutschen übersetzt", "fr": "Aus dem Französischen übersetzt",
                       "it": "Aus dem Italienischen übersetzt", "es": "Aus dem Spanischen übersetzt", "pt": "Aus dem Portugiesischen übersetzt",
                       "nl": "Aus dem Niederländischen übersetzt"},
        "months": ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."],
        "countries": {"US": "USA", "GB": "Vereinigtes Königreich", "DE": "Deutschland", "FR": "Frankreich", "IT": "Italien",
                      "ES": "Spanien", "PT": "Portugal", "NL": "Niederlande", "AU": "Australien", "CA": "Kanada",
                      "BR": "Brasilien", "MX": "Mexiko"},
    },
    "es": {"h2": "Lo que dicen los jugadores", "h2_app": "Lo que dicen los usuarios", "note": "Una selección de reseñas de 4 y 5 estrellas del App Store.", "out_of": "de 5", "store": "%(n)s valoraciones en el App Store (%(cc)s), %(when)s", "see_all": "Ver todas las valoraciones y reseñas en el App Store (%s)", "card_link": "Leer en el App Store (%s)", "stars": "%s de 5 estrellas", "more": "Leer más", "less": "Mostrar menos", "show_orig": "Mostrar original", "hide_orig": "Ocultar original", "region": "Reseñas", "prev": "Reseñas anteriores", "next": "Reseñas siguientes", "decimal": ",", "translated": {"en": "Traducido del inglés", "de": "Traducido del alemán", "fr": "Traducido del francés", "it": "Traducido del italiano", "es": "Traducido del español", "pt": "Traducido del portugués", "nl": "Traducido del neerlandés"}, "months": ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sept.", "oct.", "nov.", "dic."], "countries": {"US": "Estados Unidos", "GB": "Reino Unido", "DE": "Alemania", "FR": "Francia", "IT": "Italia", "ES": "España", "PT": "Portugal", "NL": "Países Bajos", "AU": "Australia", "CA": "Canadá", "BR": "Brasil", "MX": "México"}},
    "fr": {"h2": "Ce qu'en disent les joueurs", "h2_app": "Ce qu'en disent les utilisateurs", "note": "Une sélection d'avis 4 et 5 étoiles issus de l'App Store.", "out_of": "sur 5", "store": "%(n)s notes sur l'App Store (%(cc)s), %(when)s", "see_all": "Voir toutes les notes et tous les avis sur l'App Store (%s)", "card_link": "Lire sur l'App Store (%s)", "stars": "%s étoiles sur 5", "more": "Lire la suite", "less": "Afficher moins", "show_orig": "Afficher l'original", "hide_orig": "Masquer l'original", "region": "Avis", "prev": "Avis précédents", "next": "Avis suivants", "decimal": ",", "translated": {"en": "Traduit de l'anglais", "de": "Traduit de l'allemand", "fr": "Traduit du français", "it": "Traduit de l'italien", "es": "Traduit de l'espagnol", "pt": "Traduit du portugais", "nl": "Traduit du néerlandais"}, "months": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."], "countries": {"US": "États-Unis", "GB": "Royaume-Uni", "DE": "Allemagne", "FR": "France", "IT": "Italie", "ES": "Espagne", "PT": "Portugal", "NL": "Pays-Bas", "AU": "Australie", "CA": "Canada", "BR": "Brésil", "MX": "Mexique"}},
    "it": {"h2": "Cosa dicono i giocatori", "h2_app": "Cosa dicono gli utenti", "note": "Una selezione di recensioni a 4 e 5 stelle tratte da App Store.", "out_of": "su 5", "store": "%(n)s valutazioni su App Store (%(cc)s), %(when)s", "see_all": "Vedi tutte le valutazioni e le recensioni su App Store (%s)", "card_link": "Leggila su App Store (%s)", "stars": "%s stelle su 5", "more": "Leggi tutto", "less": "Mostra meno", "show_orig": "Mostra originale", "hide_orig": "Nascondi originale", "region": "Recensioni", "prev": "Recensioni precedenti", "next": "Recensioni successive", "decimal": ",", "translated": {"en": "Tradotto dall'inglese", "de": "Tradotto dal tedesco", "fr": "Tradotto dal francese", "it": "Tradotto dall'italiano", "es": "Tradotto dallo spagnolo", "pt": "Tradotto dal portoghese", "nl": "Tradotto dall'olandese"}, "months": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"], "countries": {"US": "Stati Uniti", "GB": "Regno Unito", "DE": "Germania", "FR": "Francia", "IT": "Italia", "ES": "Spagna", "PT": "Portogallo", "NL": "Paesi Bassi", "AU": "Australia", "CA": "Canada", "BR": "Brasile", "MX": "Messico"}},
    "nl": {"h2": "Wat spelers zeggen", "h2_app": "Wat gebruikers zeggen", "note": "Een selectie van 4- en 5-sterrenbeoordelingen uit de App Store.", "out_of": "van 5", "store": "%(n)s beoordelingen in de App Store (%(cc)s), %(when)s", "see_all": "Bekijk alle beoordelingen en recensies in de App Store (%s)", "card_link": "Lees in de App Store (%s)", "stars": "%s van 5 sterren", "more": "Lees meer", "less": "Minder tonen", "show_orig": "Origineel tonen", "hide_orig": "Origineel verbergen", "region": "Recensies", "prev": "Vorige recensies", "next": "Volgende recensies", "decimal": ",", "translated": {"en": "Vertaald uit het Engels", "de": "Vertaald uit het Duits", "fr": "Vertaald uit het Frans", "it": "Vertaald uit het Italiaans", "es": "Vertaald uit het Spaans", "pt": "Vertaald uit het Portugees", "nl": "Vertaald uit het Nederlands"}, "months": ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"], "countries": {"US": "Verenigde Staten", "GB": "Verenigd Koninkrijk", "DE": "Duitsland", "FR": "Frankrijk", "IT": "Italië", "ES": "Spanje", "PT": "Portugal", "NL": "Nederland", "AU": "Australië", "CA": "Canada", "BR": "Brazilië", "MX": "Mexico"}},
    "pt-PT": {"h2": "O que dizem os jogadores", "h2_app": "O que dizem os utilizadores", "note": "Uma seleção de avaliações de 4 e 5 estrelas da App Store.", "out_of": "de 5", "store": "%(n)s classificações na App Store (%(cc)s), %(when)s", "see_all": "Ver todas as classificações e avaliações na App Store (%s)", "card_link": "Ler na App Store (%s)", "stars": "%s de 5 estrelas", "more": "Ler mais", "less": "Mostrar menos", "show_orig": "Mostrar original", "hide_orig": "Ocultar original", "region": "Avaliações", "prev": "Avaliações anteriores", "next": "Avaliações seguintes", "decimal": ",", "translated": {"en": "Traduzido do inglês", "de": "Traduzido do alemão", "fr": "Traduzido do francês", "it": "Traduzido do italiano", "es": "Traduzido do espanhol", "pt": "Traduzido do português", "nl": "Traduzido do neerlandês"}, "months": ["jan.", "fev.", "mar.", "abr.", "mai.", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."], "countries": {"US": "Estados Unidos", "GB": "Reino Unido", "DE": "Alemanha", "FR": "França", "IT": "Itália", "ES": "Espanha", "PT": "Portugal", "NL": "Países Baixos", "AU": "Austrália", "CA": "Canadá", "BR": "Brasil", "MX": "México"}},
}

# Which storefront's real rating a page shows by default, and the minimum count before an average is shown at all.
RATING_STOREFRONT = {"en": "US", "de": "DE", "fr": "FR", "it": "IT", "es": "ES", "pt": "BR", "pt-PT": "PT", "nl": "NL"}
MIN_RATINGS = 10


def lang(game):
    return game.get("lang", "en")


def ui_key(game):
    """Which UI table entry a page uses: its "locale" (e.g. "pt-PT") if set, else its "lang"."""
    return game.get("locale", lang(game))


def ui(game):
    return UI[ui_key(game)]


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


def badge_width(path, height=54):
    """Display width of a badge at `height` px, from its SVG viewBox (Apple's localized badges vary)."""
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', open(path).read())
    return round(float(m.group(1)) / float(m.group(2)) * height) if m else 162


def cta_button(game, where="hero"):
    href = e(app_store_link(game))
    badge = ui(game)["badge"]
    path = os.path.join(ROOT, badge.lstrip("/"))
    if os.path.exists(path):
        return ('<a class="badge-link" href="%s" data-cta="%s"><img src="%s" width="%d" height="54" '
                'alt="%s"></a>' % (href, where, badge, badge_width(path), e(ui(game)["badge_alt"] % game["name"])))
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


def load_reviews(game):
    path = os.path.join(HERE, "reviews", game["slug"] + ".json")
    return json.load(open(path)) if os.path.exists(path) else None


def flag(cc):
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in cc.upper())


def star_bar(value, label, cls="stars"):
    pct = max(0.0, min(100.0, value / 5 * 100))
    return ('<span class="%s" role="img" aria-label="%s"><span class="stars__fill" style="width:%.1f%%"></span></span>'
            % (cls, e(label), pct))


def reviews_block(game):
    """Selected 4-5 star App Store reviews + Apple's REAL rating for the page's storefront.

    Honesty rules, enforced here rather than trusted to the data file:
      * only 4- and 5-star reviews (a lower one fails the build);
      * the average shown is Apple's own figure for ONE storefront (never an average of the selection, never a
        home-made worldwide blend); with fewer than MIN_RATINGS ratings there, no average is shown at all;
      * a note always says these are selected, with a link to every review on the App Store;
      * each card links to its own storefront's reviews, so a quote can be checked where it was written.
    A review written in another language appears as a labelled translation with the original alongside.
    Renders nothing when no review exists in this page's language."""
    data = load_reviews(game)
    if not data:
        return ""
    page_lang, key = lang(game), ui_key(game)
    t = REVIEW_UI.get(key) or REVIEW_UI.get(page_lang)
    cards = []
    newest_first = sorted(data["reviews"], key=lambda r: r["date"], reverse=True)
    for r in sorted(newest_first, key=lambda r: -r["rating"]):  # 5 stars first, newest first within each
        if r["rating"] < 4:
            raise ValueError("review %s is %d stars; only 4- and 5-star reviews may be shown" % (r["id"], r["rating"]))
        tr = r.get("translations", {})
        if r["lang"] == page_lang:
            cards.append((r, r["title"], r["body"], False))
        elif key in tr or page_lang in tr:
            x = tr.get(key) or tr[page_lang]
            cards.append((r, x["title"], x["body"], True))
    if not cards:
        return ""
    if t is None:
        raise KeyError("REVIEW_UI has no strings for %s; add them before showing reviews on that page" % key)
    num = lambda v: ("%.1f" % v).replace(".", t["decimal"])
    m = re.search(r"/app/([^/]+)/id(\d+)", game["appStoreUrl"])
    store_url = lambda cc: "https://apps.apple.com/%s/app/%s/id%s?see-all=reviews" % (cc.lower(), m.group(1), m.group(2))

    cc = game.get("ratingStorefront") or RATING_STOREFRONT.get(key, RATING_STOREFRONT.get(page_lang, "US"))
    here = data["ratings"]["byCountry"].get(cc, {})
    rating_html = ""
    if here.get("count", 0) >= MIN_RATINGS:
        y, mo = data["ratings"]["asOf"][:4], int(data["ratings"]["asOf"][5:7])
        meta = t["store"] % {"n": here["count"], "cc": cc, "when": "%s %s" % (t["months"][mo - 1], y)}
        rating_html = ('<div class="rating"><span class="rating__value" aria-hidden="true">%s</span>'
                       '<span class="rating__outof" aria-hidden="true">%s</span>%s<span class="rating__meta">%s</span></div>'
                       % (num(here["average"]), e(t["out_of"]), star_bar(here["average"], t["stars"] % num(here["average"])), e(meta)))

    items = []
    for i, (r, title, body, translated) in enumerate(cards, 1):
        y, mo = r["date"][:4], int(r["date"][5:7])
        country = t["countries"].get(r["country"], r["country"])
        orig = ""
        if translated:
            if r["lang"] not in t["translated"]:
                raise KeyError("REVIEW_UI[%r]['translated'] has no label for source language %r" % (key, r["lang"]))
            # Without JS the original is simply shown; the script hides it behind the toggle.
            orig = ('<p class="review__translated">%s <button type="button" class="review__orig-toggle" hidden aria-expanded="false" '
                    'aria-controls="rv%d-o" data-show="%s" data-hide="%s">%s</button></p>'
                    '<div class="review__original" id="rv%d-o" lang="%s"><p class="review__title-orig">%s</p><p>%s</p></div>'
                    % (e(t["translated"][r["lang"]]), i, e(t["show_orig"]), e(t["hide_orig"]), e(t["show_orig"]),
                       i, e(r["lang"]), e(r["title"]), e(r["body"].strip())))
        items.append("""
      <li class="review">
        <h3 class="review__title" id="rv%(i)d-t">%(title)s</h3>
        %(stars)s
        <p class="review__body" id="rv%(i)d-b">%(body)s</p>
        <button type="button" class="review__more" hidden aria-expanded="false" aria-controls="rv%(i)d-b" aria-describedby="rv%(i)d-t" data-more="%(more)s" data-less="%(less)s">%(more)s</button>%(orig)s
        <p class="review__meta"><span>%(nick)s</span><span aria-hidden="true">·</span><a class="review__store" href="%(url)s" rel="noopener" aria-label="%(link)s">%(flag)s</a><span aria-hidden="true">·</span><span>%(when)s</span></p>
      </li>""" % {"i": i, "title": e(title), "stars": star_bar(r["rating"], t["stars"] % r["rating"], "stars stars--sm review__stars"),
                  "body": e(re.sub(r"[ \t]{2,}", " ", body.strip())), "more": e(t["more"]), "less": e(t["less"]), "orig": orig,
                  "nick": e(r["nickname"]), "url": e(store_url(r["country"])), "link": e(t["card_link"] % country),
                  "flag": flag(r["country"]), "when": "%s %s" % (t["months"][mo - 1], y)})
    heading = game.get("reviewsHeading", t["h2"] if "VideoGame" in str(game.get("schemaType", "VideoGame")) else t["h2_app"])
    return """
<section class="reviews" id="reviews" aria-labelledby="reviews-h">
  <div class="reviews__head wrap">
    <div><h2 id="reviews-h">{h2}</h2>{rating}</div>
    <div class="reviews__nav" hidden><button type="button" class="reviews__prev" aria-label="{prev}">&larr;</button><button type="button" class="reviews__next" aria-label="{next}">&rarr;</button></div>
    <p class="reviews__note">{note} <a href="{see_all_url}" rel="noopener">{see_all}</a></p>
  </div>
  <div class="reviews__scroller" role="group" aria-label="{region}" tabindex="0">
    <ul class="reviews__list" role="list">{items}
    </ul>
  </div>
  <script>
  (function () {{
    var root = document.getElementById("reviews"), scroller = root.querySelector(".reviews__scroller");
    var cards = [].slice.call(root.querySelectorAll(".review"));
    function measure() {{  // show "Read more" only on cards whose text is actually cut off at this width
      cards.forEach(function (card) {{
        var body = card.querySelector(".review__body"), more = card.querySelector(".review__more");
        if (more.getAttribute("aria-expanded") === "true") return;
        body.classList.add("is-clamped");
        var cut = body.scrollHeight > body.clientHeight + 2;
        if (!cut) body.classList.remove("is-clamped");
        more.hidden = !cut;
      }});
    }}
    cards.forEach(function (card) {{
      var body = card.querySelector(".review__body"), more = card.querySelector(".review__more");
      more.addEventListener("click", function () {{
        var open = more.getAttribute("aria-expanded") !== "true";
        body.classList.toggle("is-clamped", !open);
        more.textContent = open ? more.dataset.less : more.dataset.more;
        more.setAttribute("aria-expanded", open);
      }});
      var tg = card.querySelector(".review__orig-toggle"), og = card.querySelector(".review__original");
      if (tg && og) {{
        og.hidden = true; tg.hidden = false;
        tg.addEventListener("click", function () {{
          og.hidden = !og.hidden;
          tg.textContent = og.hidden ? tg.dataset.show : tg.dataset.hide;
          tg.setAttribute("aria-expanded", !og.hidden);
        }});
      }}
    }});
    measure();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
    var nav = root.querySelector(".reviews__nav");
    function arrows() {{ nav.hidden = scroller.scrollWidth <= scroller.clientWidth + 2; }}  // only when there is more to see
    arrows();
    var wait; window.addEventListener("resize", function () {{ clearTimeout(wait); wait = setTimeout(function () {{ measure(); arrows(); }}, 150); }});
    var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function step(d) {{ scroller.scrollBy({{ left: d * (cards[0].offsetWidth + 16), behavior: still ? "auto" : "smooth" }}); }}
    root.querySelector(".reviews__prev").addEventListener("click", function () {{ step(-1); }});
    root.querySelector(".reviews__next").addEventListener("click", function () {{ step(1); }});
  }})();
  </script>
</section>""".format(h2=e(heading), rating=rating_html, prev=e(t["prev"]), next=e(t["next"]), note=e(t["note"]),
                     see_all_url=e(store_url(cc)), see_all=e(t["see_all"] % cc), region=e(t["region"]), items="".join(items))


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
    head = ['  <link rel="alternate" hreflang="%s" href="%s%s">' % (l, SITE, path) for l, path, _ in siblings]
    head.append('  <link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, {l: p for l, p, _ in siblings}["en"]))
    head.append('  <meta property="og:locale" content="%s">' % ui(game)["og_locale"])
    head += ['  <meta property="og:locale:alternate" content="%s">' % UI[k]["og_locale"]
             for l, _, k in siblings if l != lang(game)]
    links = "".join('\n      <a href="%s" hreflang="%s" lang="%s">%s</a>' % (path, l, l, UI[k]["name"])
                    for l, path, k in siblings if l != lang(game))
    return "\n" + "\n".join(head), links


def asset_version(path):
    """Short content hash for cache-busting: GitHub Pages lets browsers cache assets for 10 minutes, so a page
    that changes with its CSS must point at a URL that changes too (else visitors get new HTML + old CSS)."""
    import hashlib
    return hashlib.md5(open(os.path.join(ROOT, path.lstrip("/")), "rb").read()).hexdigest()[:10]


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
        "css_href": "/assets/product.css?v=" + asset_version("/assets/product.css"),
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
        "reviews": reviews_block(game),
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
        family.setdefault(g["slug"], []).append((lang(g), page_path(g), ui_key(g)))
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
