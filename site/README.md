# Baked on 8th — Cake O'Clock demo site

Static, 5-page demo redesign built from bakedon8th.com (researched 2026-10-29). Open `index.html` in a browser, or serve the folder:

```bash
python -m http.server 5508 --directory .
```

## Pages
| Page | What it does |
|---|---|
| `index.html` | Live same-day countdown cake (Nashville time; after the cutoff the logo's mascot takes over), three ways to order, cake rail, seasonals, weddings teaser, gallery, hours (with upcoming holiday closures)/map |
| `menu.html` | All 10 cakes as cards that start as a drawing and turn into the real photo once in view (Drawing / Photo switch; mouse hover peeks at the drawing), seasonals, cookies, bars & treats, custom gallery, allergen note |
| `order.html` | Same-day (Square), walk-in rules, custom cake planner (flavor → frosting → size → starting price → call) |
| `weddings.html` | Pricing, tastings, delivery, a few wedding photos, validated inquiry the visitor sends from their email app or copies into any email, gallery |
| `events.html` | Events auto-sorted into upcoming/past by date; with nothing scheduled it leads with the last event |

Owner questions (`data-note`) and fact sources (`data-source`) stay in the templates and content for review, but the build strips them from the pages; they're collected in `pitch/review-notes.md`.

## Editing
Owner content (cakes, seasonals, menu lists, custom-cake menu, events, hours and closures, wedding prices) is in `content/*.json`, edited through the form-based editor at `/admin` (Decap CMS): see `content/README.md`.
Pages are generated: edit `tools/pages/*.html` for page wording, then run `python tools/build.py` (needs Pillow; `--watch` rebuilds on every save).
Illustrations: `python tools/draw_cakes.py assets/illustrations`. Link check: `python tools/check_links.py`.

## Responsive QA
Serve the folder and open `tools/matrix.html`: it loads all 5 pages at 15 screen sizes (320px phones to 2560px monitors, portrait and landscape) and reports horizontal overflow, off-screen or clipped text, tap targets under 44px, distorted/broken images and fixed bars covering content. `tools/qa.js` runs the same check on any open page.

## Assets
All photos and the logo come from bakedon8th.com (Squarespace CDN). Source URL for each file is in `../assets/asset-manifest.json`; full-size originals are in `../assets/original-downloads/`. Used here for a pitch demo only; delete if the owners decline.
Cake illustrations (`assets/illustrations/`) are SVGs drawn by `tools/draw_cakes.py` from the real cake photos.

## Not connected
- Wedding inquiries are sent by the visitor (email app or copy and paste). No form service is configured, and the page says so; Netlify Forms plugs in once hosted.
- The `/admin` editor saves only on this computer (`npx decap-server`). Going live with logins is described in `content/README.md`, not set up.
- Same-day ordering links to the existing Square site: https://bakedon8th.square.site/
