# Webcraft Studio

Marketing website for Webcraft Studio — freelance web design, development, and SEO services for small businesses and startups.

**Live site:** _add your GitHub Pages / custom domain URL here once deployed_

## Pages

| Page | File |
|---|---|
| Home | `index.html` |
| About | `about.html` |
| Services | `services.html` |
| Portfolio | `portfolio.html` |
| Contact | `contact.html` |

## Stack

Plain HTML, CSS, and vanilla JavaScript — no build step, no framework, no dependencies. Fonts are loaded from Google Fonts (Playfair Display, Inter).

- `style.css` — all styling, CSS custom properties for the color/type system
- `script.js` — mobile nav toggle, scroll-reveal animations, sticky header shadow, contact form feedback
- `logo.svg` — brand mark (source of truth); `brand-assets/` has PNG exports for social profiles
- `robots.txt` — search engine crawl rules

## Running locally

No build tools required. Serve the folder with any static file server, e.g.:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Deploying to GitHub Pages

1. Push this repo to GitHub.
2. In the repo settings, go to **Pages** → set source to the `main` branch, root folder.
3. The site will be live at `https://<username>.github.io/<repo-name>/`.

## Contact

webcraftstudio28@gmail.com
