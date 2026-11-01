# Website content (what the owners can change themselves)

Everything Baked on 8th changes from month to month lives in this folder, one file per kind of thing.
The pages are built from these files by `tools/build.py`, so nobody has to touch the HTML.

| File | What it holds | Editor section |
|---|---|---|
| `seasonal.json` | The monthly seasonal menu: months label, intro sentences, items (name, description, photo, GF, homepage spot) | Menu → Seasonal menu |
| `cakes.json` | Same-day sizes and prices; every cake card (layers, photo, everyday / seasonal / custom only, GF on custom order, homepage spot) | Menu → Everyday cakes |
| `menu-lists.json` | Cookies; bars, pop tarts and treats (name, tag, description) | Menu → Cookies, bars & treats |
| `custom-cakes.json` | The custom cake planner: flavors, frostings, sizes and starting prices (flavors also feed the wedding form) | Menu → Custom cake menu |
| `hours.json` | Opening hours, online cutoffs, holiday closures. The open/closed sign, the cake clock and the "Order for today" buttons follow it | Shop → Hours & holiday closures |
| `weddings.json` | Price per serving, delivery from, consultation days and hours | Shop → Wedding prices |
| `events.json` | Markets and pop-ups; each moves from Upcoming to Past on its own | Events |

Photos uploaded in the editor go to `assets/uploads/`. The build makes 800px and 1400px WebP copies of each
(rotated the right way up), so a photo straight from a phone is fine.

A new cake has no drawing yet, so its card shows the photo only. To give it a drawing, run
`python tools/draw_cakes.py` for that cake and keep the file name `assets/illustrations/cake-<short name>.svg`.

## Demo on this computer

From the folder that holds `site/` (the project folder), in three terminals:

```
npx decap-server                       # the editor's local file bridge, port 8081
python -m http.server 5508 -d site     # the website
python site/tools/build.py --watch     # rebuilds the pages on every save
```

Open http://127.0.0.1:5508/admin/, change something, press **Publish → Publish now**, then reload the page
that shows it. (`local_backend: true` in `admin/config.yml` makes the editor save straight to these files,
with no login.)

## What the owners need (and who owns what)
- **Accounts:** a free GitHub account for each person who edits (that's the editor login), plus a hosting
  account. Both are created under the bakery's own email; the developer gets collaborator access only.
- **Costs:** the domain they already pay for, plus hosting. Netlify's free plan is 300 credits a month; each
  publish (every editor save) uses 15 and visitors use some too, and when credits run out every site on the
  account is paused until the month resets. Recommend Netlify Personal (about $9/month, 1,000 credits) or
  Cloudflare Pages (free plan doesn't meter visitors; the wedding form would then need a form service).
  Check current pricing before quoting.
- **Unchanged:** Square ordering, Google Workspace email (keep the MX and SPF records when pointing the domain).
- The owner-facing version of this is `../pitch/how-to-update.md`.

## Going live (when the owners say yes; not set up yet)

1. **Repository.** Create a private GitHub repository (e.g. `baked-on-8th-site`) containing the `site/` folder,
   and set `repo:` in `admin/config.yml` to it. Leave `local_backend: true`; it is ignored on the live site.
2. **Hosting.** Connect the repository to Netlify:
   - Build command: `pip install pillow && python site/tools/build.py`
   - Publish directory: `site`
   - Python version: 3.12 (`PYTHON_VERSION` environment variable)
3. **Owner login.** Decap's GitHub backend needs an OAuth app: create one in GitHub (Settings → Developer
   settings → OAuth Apps, callback `https://api.netlify.com/auth/done`) and add its client ID and secret in
   Netlify (Site configuration → Access & security → OAuth → GitHub). Invite each person who will edit as a
   collaborator on the repository; they sign in at `bakedon8th.com/admin` with their GitHub account.
4. **Domain.** Point `bakedon8th.com` at Netlify (Domain management → Add a domain) only after the owners approve
   the new site, then remove `noindex` from `head()` in `tools/build.py` and delete `robots.txt`'s block.
5. **Forms.** The wedding inquiry currently opens the visitor's email app. Netlify Forms can receive it directly;
   see the comment in `tools/pages/weddings.html`.

Every save in the editor becomes a commit in the repository and Netlify redeploys in about a minute, so any
change can be undone from the repository history.

## Guards that keep the site safe
- Opening hours need at least one row (`min: 1` in `admin/config.yml`); `build.py` also refuses to build with
  no hours, so the last good pages stay live, and `site.js` hides the open/closed sign if hours are missing.
- Hours labels ("Monday – Saturday") are generated from the days picked; events store a date plus start and
  end times and the build writes the display line, so a page can't show two different dates.
- `admin/index.html` reloads when the editor jumps straight from one entry to another, which otherwise could
  show the new entry with empty fields.

## What stays in the templates

Wording that rarely changes (page intros, how-to-order steps, the allergen statement) stays in
`tools/pages/*.html`. Fixed links (Square, phone, Electric Mixer) are at the top of `tools/build.py`.
