#!/usr/bin/env python3
"""HANDOFF §7 checks for every built page (product pages, drafts and the hand-written pages):
one <h1>, no em dashes, every <img> has alt, JSON-LD parses, title <= 60 and description <= 160,
every hreflang sibling lists the same set, and internal links and images exist on disk.

    /usr/bin/python3 _product-pages/check.py            # every page
    /usr/bin/python3 _product-pages/check.py fess       # only paths containing "fess"

Prints OK/BAD per page and "problems: N". Standard library only. The phone-width check
(scrollWidth at 375 and 320 px) still needs a browser.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.ld, self.title = [], [], ""
        self._ld = self._title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "script" and a.get("type") == "application/ld+json":
            self._ld = True
            self.ld.append("")
        self._title = self._title or tag == "title"

    def handle_endtag(self, tag):
        if tag == "script":
            self._ld = False
        if tag == "title":
            self._title = False

    def handle_data(self, data):
        if self._ld:
            self.ld[-1] += data
        if self._title:
            self.title += data


def pages():
    found = []
    for dirpath, dirnames, files in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        if rel == ".":
            continue
        hidden = rel.startswith(".") or "/." in rel
        unpublished = rel.startswith("_") and not ("_product-pages/drafts".startswith(rel) or rel.startswith("_product-pages/drafts"))
        if hidden or unpublished:
            dirnames[:] = []
            continue
        if "index.html" in files and rel != ".":
            found.append(rel)
    return sorted(found)


def check(rel):
    base = os.path.join(ROOT, rel)
    html = open(os.path.join(base, "index.html"), encoding="utf-8").read()
    p = Page()
    p.feed(html)
    errs = []
    if html.count("<h1") != 1:
        errs.append("h1 count %d" % html.count("<h1"))
    if "—" in html:
        errs.append("em dash x%d" % html.count("—"))
    for tag, a in p.tags:
        if tag == "img" and "alt" not in a:
            errs.append("img without alt: %s" % a.get("src"))
    for block in p.ld:
        try:
            json.loads(block)
        except ValueError as ex:
            errs.append("bad JSON-LD: %s" % ex)
    if len(p.title) > 60:
        errs.append("title %d chars" % len(p.title))
    desc = [a.get("content", "") for t, a in p.tags if t == "meta" and a.get("name") == "description"]
    if desc and len(desc[0]) > 160:
        errs.append("description %d chars" % len(desc[0]))
    for tag, a in p.tags:
        for attr in ("src", "href", "srcset"):
            value = a.get(attr)
            if not value or (tag == "link" and a.get("rel") in ("canonical", "alternate")):
                continue
            for url in ([u.strip().split(" ")[0] for u in value.split(",")] if attr == "srcset" else [value]):
                if re.match(r"^(https?:|mailto:|#|data:|//)", url):
                    continue
                url = url.split("#")[0].split("?")[0]
                if not url:
                    continue
                path = os.path.join(ROOT, url.lstrip("/")) if url.startswith("/") else os.path.join(base, url)
                if not (os.path.isfile(path) or os.path.isfile(os.path.join(path, "index.html"))):
                    errs.append("missing %s %s" % (attr, url))
    langs = tuple(sorted(a["hreflang"] for t, a in p.tags
                         if t == "link" and a.get("rel") == "alternate" and a.get("hreflang")))
    return sorted(set(errs)), langs


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    problems, by_slug = 0, {}
    for rel in pages():
        if only not in rel:
            continue
        errs, langs = check(rel)
        print(("OK  " if not errs else "BAD ") + rel + ("" if not errs else ": " + "; ".join(errs)))
        problems += bool(errs)
        if langs:
            by_slug.setdefault(rel.split("/")[-1], set()).add(langs)
    for slug, sets in by_slug.items():
        if len(sets) > 1:
            problems += 1
            print("BAD hreflang sets differ between the %s pages" % slug)
    print("problems:", problems)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
