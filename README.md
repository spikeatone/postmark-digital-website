# Postmark Digital — website

A static one-page site for Postmark Digital (mobile game studio), hosted on
GitHub Pages at **https://postmarkdigital.com**.

## Files
- `index.html` — the page
- `styles.css` — styles; **all brand colors are CSS variables at the top** (swap for Figma tokens)
- `assets/favicon.svg` — placeholder mark (replace with the real logo)
- `CNAME` — custom domain for GitHub Pages (`postmarkdigital.com`)

## Editing the brand
1. Replace the color values in the `:root { ... }` block of `styles.css`.
2. Drop the Figma logo export into `assets/` and update the `<img>` in the header
   of `index.html` (and, optionally, the favicon).
3. Set the real registered legal entity name in the footer and add App Store links
   in the Games section when listings are live.

## Deploy (GitHub Pages)
1. Push this folder to a GitHub repo.
2. Settings → Pages → Source: "Deploy from a branch", Branch: `main`, Folder: `/ (root)`.
3. Settings → Pages → Custom domain: `postmarkdigital.com`.
4. At the domain registrar, add DNS records (see the deploy notes) and enable
   "Enforce HTTPS" once the certificate is issued.

## Local preview
Open `index.html` in a browser, or run a static server from this folder.
