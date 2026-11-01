"""Assemble the static pages: shared head/header/footer, cake cards and owner content, from tools/pages/*.html.

Everything the owners change (cakes, seasonals, menu lists, events, hours and closures, wedding and custom-cake
prices) lives in content/*.json, which the /admin editor writes. Page templates use:
  <!--@head Title|Description-->  <!--@header key-->  <!--@footer-->  <!--@cakes all|home-->  <!--@seasonal home|menu-->
  <!--@list cookies|treats-->  <!--@events-->  <!--@hours-->  <!--@planner flavors|frostings|sizes|wedding-flavors-->
  {{TOKENS}} for single values (see tokens()).
Run: python tools/build.py            (from the site folder or anywhere)
     python tools/build.py --watch    (rebuild on every save, for the editor demo)
"""
import html, json, re, sys, time
from pathlib import Path
from PIL import Image, ImageOps

SITE = Path(__file__).resolve().parent.parent
CONTENT = SITE / "content"
SQUARE = "https://bakedon8th.square.site/"
TEL = "tel:+16159331100"
MAPS = "https://www.google.com/maps/search/?api=1&query=Baked+on+8th+1512+8th+Ave+S+Nashville+TN+37203"
ELECTRIC_MIXER = "https://theelectricmixer.myshopify.com/"

ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "bag": '<path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "pencil": '<path d="M4 20l4-1 11-11-3-3L5 16l-1 4z"/><path d="M14 6l3 3"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "insta": '<rect x="4" y="4" width="16" height="16" rx="5"/><circle cx="12" cy="12" r="3.6"/><circle cx="17" cy="7" r=".6"/>',
    "fb": '<path d="M14 8h3V4h-3a4 4 0 0 0-4 4v3H7v4h3v6h4v-6h3l1-4h-4V8z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "tag": '<path d="M3 12V4h8l10 10-8 8L3 12z"/><circle cx="7.5" cy="8.5" r="1.5"/>',
    "slice": '<path d="M3 19h18L18 9 3 13z"/><path d="M3 16h18"/><path d="M9 11.5V7.5"/><path d="M9 5.5v.01"/>',
    "truck": '<path d="M2 6h11v10H2zM13 9h4l4 4v3h-8z"/><circle cx="6" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
}


def icon(n, cls="", w=18):
    return f'<svg class="{cls}" viewBox="0 0 24 24" width="{w}" height="{w}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[n]}</svg>'


def esc(s):
    return html.escape(str(s), quote=True)


def hm(t):
    """'18:30' -> '6:30pm', '08:00' -> '8am'"""
    h, m = (int(x) for x in t.split(":"))
    return f"{h % 12 or 12}{f':{m:02d}' if m else ''}{'am' if h < 12 else 'pm'}"


NAV = [("menu", "menu.html", "Menu"), ("order", "order.html", "How to order"), ("weddings", "weddings.html", "Weddings"),
       ("events", "events.html", "Events"), ("visit", "index.html#visit", "Visit")]


def ver(rel):
    """cache-busting version: the file's modification time, so browsers fetch each new build"""
    return int((SITE / rel).stat().st_mtime)


def head(title, desc):
    # noindex: concept demo stays out of search engines until the owners approve it.
    # The inline "js" class lets the CSS hide reveal-on-scroll content only when the script can show it again.
    return f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="theme-color" content="#FFFFFF">
<meta name="robots" content="noindex, nofollow">
<script>document.documentElement.classList.add('js');setTimeout(function(){{if(!window.BO8)document.documentElement.classList.remove('js')}},3000)</script>
<link rel="icon" type="image/png" href="assets/img/logo-96.png">
<link rel="apple-touch-icon" href="assets/img/logo-96.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Concert+One&family=Figtree:wght@400;500;600;700&family=Shrikhand&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/site.css?v={ver("assets/css/site.css")}">
<script src="assets/js/site.js?v={ver("assets/js/site.js")}" defer></script>'''


def action_bar(active):
    # phone bar: the main thing to do on this page first
    call = f'<a class="call" href="{TEL}">{icon("phone")} Call</a>'
    directions = f'<a href="{MAPS}">{icon("pin")} Directions</a>'
    if active == "weddings":
        return f'<a class="primary" href="#inquire" data-form-cta="{TEL}">{icon("mail")} Start your inquiry</a>\n  {call}\n  {directions}'
    if active == "order":
        # becomes "Call to order" while the custom cake planner is on screen (site.js)
        return (f'<a class="primary" href="{SQUARE}" data-cta="sameday" data-planner-cta="{TEL}">{icon("bag")} <span data-cta-label>Order for today</span></a>\n'
                f'  {call}\n  {directions}')
    return f'<a class="primary" href="{SQUARE}" data-cta="sameday">{icon("bag")} <span data-cta-label>Order for today</span></a>\n  {call}\n  {directions}'


def header(active, shop="{}"):
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if k == active else ""}>{t}</a>' for k, h, t in NAV)
    mlinks = '<a href="index.html">Home</a>' + "".join(f'<a href="{h}">{t}</a>' for k, h, t in NAV)
    return f'''<a class="skip" href="#main">Skip to content</a>
<p class="concept-bar">Concept redesign for review. Not the official Baked on 8th website. <a href="https://www.bakedon8th.com/">Visit bakedon8th.com</a></p>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html" aria-label="Baked on 8th, home"><img src="assets/img/logo-160.webp" width="160" height="172" alt=""><span>Baked on 8th</span></a>
    <nav class="nav" aria-label="Main">{links}</nav>
    <div class="header-actions">
      <a class="btn btn-sm" href="{SQUARE}" data-cta="sameday"><span data-cta-label>Order for today</span> {icon("arrow", "arrow")}</a>
      <button class="menu-btn" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-nav">{icon("menu", w=22)}</button>
    </div>
  </div>
</header>
<div class="mobile-nav" id="mobile-nav" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Site menu">
  <div class="top"><img src="assets/img/logo-160.webp" width="56" height="60" alt="Baked on 8th" style="filter:brightness(0) invert(1)"><button class="close" type="button" aria-label="Close menu">{icon("x", w=22)}</button></div>
  <nav aria-label="Mobile">{mlinks}</nav>
  <p class="meta">1512 8th Ave S, Nashville · <a href="{TEL}">615-933-1100</a></p>
</div>
<div class="action-bar" aria-label="Quick actions">
  {action_bar(active)}
</div>
<p id="sr-live" class="sr-only" aria-live="polite"></p>
<script type="application/json" id="shop-hours">{shop}</script>'''


def footer(hours):
    rows = "".join(f'<li>{esc(day_labels(r["days"])[1])} · {hm(r["opens"])}–{hm(r["closes"])}</li>' for r in hours["rows"])
    first, *rest = hours["rows"]
    cut = hm(first["online_cutoff"]) + "".join(f' ({esc(day_labels(r["days"])[1])} {hm(r["online_cutoff"])})' for r in rest)
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <p class="footer-big">Life can be sweet.<br>Come get a slice.</p>
        <p>A classic Southern bakery on 8th Avenue South, baking something new every day.</p>
        <p class="social"><a href="https://www.instagram.com/bakedon8th" aria-label="Instagram">{icon("insta", w=24)}</a><a href="https://www.facebook.com/bakedon8th" aria-label="Facebook">{icon("fb", w=24)}</a></p>
      </div>
      <div><h4>Visit</h4><ul><li>1512 8th Ave S<br>Nashville, TN 37203</li><li><a href="{MAPS}">Get directions</a></li><li><a href="{TEL}">615-933-1100</a></li><li><a href="mailto:info@bakedon8th.com">info@bakedon8th.com</a></li></ul></div>
      <div><h4>Hours</h4><ul>{rows}<li class="small" style="opacity:.75">Order online by {cut} for same-day pickup</li></ul></div>
      <div><h4>Explore</h4><ul><li><a href="menu.html">Menu &amp; flavors</a></li><li><a href="order.html">How to order</a></li><li><a href="weddings.html">Wedding cakes</a></li><li><a href="events.html">Events</a></li><li><a href="menu.html#allergens">Allergen information</a></li><li><a href="{ELECTRIC_MIXER}">Electric Mixer party shop</a></li></ul></div>
    </div>
    <div class="footer-base"><span>© Baked on 8th · Nashville, TN</span><span>Demo redesign for review. Photos and logo © Baked on 8th.</span></div>
  </div>
</footer>'''


# ---------- Owner-editable content (content/*.json) ----------
def load(name):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def photo(path):
    """A content image -> (src, srcset, width, height), or None.
    Built-in photos are NAME-800.webp with a NAME-1400.webp sibling. Anything uploaded through the editor
    (a phone JPG, a PNG...) gets 800px and 1400px WebP copies made next to it, remade when the upload changes."""
    if not path:
        return None
    path = path.lstrip("/")
    p = SITE / path
    if not p.exists():
        print("  missing image:", path)
        return None
    m = re.match(r"(.+)-800\.webp$", path)
    if m and (SITE / f"{m[1]}-1400.webp").exists():
        with Image.open(p) as im:
            return path, f"{path} 800w, {m[1]}-1400.webp 1400w", im.width, im.height
    base = path.rsplit(".", 1)[0]
    out = {}
    for w in (800, 1400):
        rel = f"{base}-{w}.webp"
        dst = SITE / rel
        if not dst.exists() or dst.stat().st_mtime < p.stat().st_mtime:
            with Image.open(p) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")  # phone photos carry their rotation in EXIF
                if im.width > w:
                    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
                im.save(dst, "WEBP", quality=82, method=6)
            print("  made", rel)
        with Image.open(dst) as im:
            out[w] = (rel, im.width, im.height)
    (s8, w8, h8), (s14, w14, _) = out[800], out[1400]
    return s8, f"{s8} {w8}w, {s14} {w14}w", w8, h8


# ---------- Cakes: text from /cakeflavors + Square; illustrations drawn from each photo ----------
def cake_card(c, sizes, i=0):
    """A cake card: the real photo, with its drawing underneath only as a placeholder while the photo loads."""
    t = esc(c["title"])
    tag = ""
    if c["status"] == "seasonal":
        tag = f'<span class="tag hot">{esc(c.get("seasonal_label") or "Seasonal")}</span>'
    elif c["status"] == "custom":
        tag = '<span class="tag">Custom order only</span>'
    price = (f'<p class="price">{" · ".join(esc(s["size"]) + " $" + format(s["price"], "g") for s in sizes)}</p>' if c["status"] != "custom" else "")
    # the allergen tag sits with the price, well away from the order button
    gf = '<p class="cake-gf"><span class="tag gf">Gluten-friendly: custom order only</span></p>' if c.get("gluten_free_on_custom") else ""
    order = (f'<a class="cake-order" href="{SQUARE}" data-cta="sameday"><span data-cta-label>Order for today</span> {icon("arrow", w=15)}</a>' if c["status"] != "custom"
             else f'<a class="cake-order" href="order.html#custom">Plan a custom cake {icon("arrow", w=15)}</a>')
    ph = photo(c.get("photo"))
    alt = esc(c.get("photo_description", ""))
    sizes_attr = 'sizes="(max-width: 760px) 50vw, (max-width: 1100px) 33vw, 25vw"'
    sticker = (SITE / "assets" / "illustrations" / f"cake-{c['id']}-bare.svg").exists()
    media = ""
    if sticker:
        # the drawing is a small sticker on the photo (decorative); with no photo it fills the card and speaks for it
        media += (f'<img class="cake-sticker" src="assets/illustrations/cake-{c["id"]}-bare.svg" width="564" height="416" decoding="async" '
                  + (f'alt="" aria-hidden="true">' if ph else f'alt="{t} cake (drawing): {alt}">'))
    if ph:
        media += f'\n    <img class="v-photo" src="{ph[0]}" srcset="{ph[1]}" {sizes_attr} width="{ph[2]}" height="{ph[3]}" loading="lazy" decoding="async" alt="A {t} cake from the shop: {alt}">'
    return f'''<article class="cake-card reveal{"" if ph else " no-photo"}" style="--d:{(i % 4) * .08:.2f}s">
  <div class="cake-media">
    {tag}
    {media}
  </div>
  <div class="cake-body">
    <h3>{t}</h3>
    {price}{gf}
    <p class="layers">{esc(c['layers'])}</p>
    {order}
  </div>
</article>'''


def on_home(items):
    return sorted((x for x in items if x.get("homepage_position")), key=lambda x: x["homepage_position"])


def cakes_block(which, data):
    cakes = data["cakes"] if which == "all" else on_home(data["cakes"])
    return "\n".join(cake_card(c, data["same_day_sizes"], i) for i, c in enumerate(cakes))


def seasonal_block(which, data):
    gf = '<span class="tag gf">Gluten-friendly</span>'
    out = []
    items = on_home(data["items"]) if which == "home" else data["items"]
    for i, it in enumerate(items):
        ph = photo(it["photo"])
        img = f'<img src="{ph[0]}" width="{ph[2]}" height="{ph[3]}" alt="{esc(it["photo_description"])}" loading="lazy">' if ph else ""
        tag = gf if it["gluten_free"] else ""
        if which == "home":
            d = f' style="--d:{i * .08:.2f}s"' if i else ""
            out.append(f'<a class="card reveal"{d} href="menu.html#seasonal"><div class="frame zoom ratio-45">{tag}{img}</div><h3>{esc(it["name"])}</h3><p>{esc(it.get("short") or it["description"])}</p></a>')
        else:
            d = f' style="--d:{(i % 4) * .06:.2f}s"' if i % 4 else ""
            out.append(f'<article class="card reveal"{d}><div class="frame ratio-45">{tag}{img}</div><h3>{esc(it["name"])}</h3><p>{esc(it["description"])}</p></article>')
    return "\n        ".join(out)


def list_item(x):
    return f'<li><b>{esc(x["name"])}{" <em>" + esc(x["tag"]) + "</em>" if x.get("tag") else ""}</b><span>{esc(x["description"])}</span></li>'


def list_block(which, data):
    items = data[which]
    if which != "treats":
        return "\n        ".join(list_item(x) for x in items)
    # treats come in small labelled groups; on phones site.js closes all but the first
    groups = {}
    for x in items:
        groups.setdefault(x.get("group") or "Other treats", []).append(x)
    return "\n        ".join(
        f'<details class="menu-group" open><summary><span>{esc(g)}</span> <small>{len(xs)}</small></summary><ul class="menu-list">{"".join(list_item(x) for x in xs)}</ul></details>'
        for g, xs in groups.items())


def todays_case(d):
    """A dated photo of today's case, posted from the editor; site.js hides it once it is more than 3 days old."""
    ph = photo(d.get("photo"))
    if not ph or not d.get("date"):
        return ""
    day = d["date"][:10]
    y, m, dd = day.split("-")
    label = f'{MONTHS[int(m) - 1]} {int(dd)}'
    return f'''<section class="todays-case" data-case-date="{esc(day)}" aria-labelledby="case-h">
    <div class="wrap case-inner">
      <div class="frame ratio-43 case-photo"><img src="{ph[0]}" srcset="{ph[1]}" sizes="(max-width: 900px) 90vw, 50vw" width="{ph[2]}" height="{ph[3]}" alt="Today’s case at Baked on 8th{": " + esc(d["caption"]) if d.get("caption") else ""}"></div>
      <div>
        <p class="case-date">Updated <time datetime="{esc(day)}">{label}</time></p>
        <h2 id="case-h">In the case today</h2>
        {f'<p class="lede">{esc(d["caption"])}</p>' if d.get("caption") else ""}
        <p class="small muted">It changes through the day. Whole cakes for today are on our <a class="link" href="{SQUARE}">ordering site</a>.</p>
      </div>
    </div>
  </section>'''


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def events_block(data):
    out = []
    for e in data["events"]:
        y, mo, d = e["date"][:10].split("-")
        ph = photo(e.get("image"))
        poster = f'\n          <div class="poster"><img src="{ph[0]}" width="{ph[2]}" height="{ph[3]}" alt="{esc(e.get("image_description", ""))}" loading="lazy"></div>' if ph else ""
        n1 = f' data-note="{esc(e["note_on_date"])}"' if e.get("note_on_date") else ""
        wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][__import__("datetime").date(int(y), int(mo), int(d)).weekday()]
        span = hm(e["start_time"]) + (f'–{hm(e["end_time"])}' if e.get("end_time") else "")
        when = f'{wd}, {MONTHS[int(mo) - 1]} {int(d)} · {span}'
        n2 = f' data-note="{esc(e["note_on_description"])}"' if e.get("note_on_description") else ""
        link = f'\n            <p style="margin-top:12px"><a class="link" href="{esc(e["link"])}">Event details</a></p>' if e.get("link") else ""
        out.append(f'''<article class="event" data-event-date="{esc(e['date'][:10])}">
          <div class="date"><b>{int(d)}</b><span>{MONTHS[int(mo) - 1]} {y}</span></div>
          <div>
            <span class="tag when-label">Event</span>
            <h3 style="margin-top:10px">{esc(e['title'])}</h3>
            <p{n1}><b>{when}</b> · {esc(e['where'])}</p>
            <p{n2}>{esc(e['description'])}</p>{link}
          </div>{poster}
        </article>''')
    return "\n        ".join(out)


WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
LONG = dict(zip(WEEK, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]))


def day_labels(days):
    """['Mon',...,'Sat'] -> ('Monday – Saturday', 'Mon–Sat'): labels always match the days picked in the editor"""
    idx = sorted(WEEK.index(d) for d in days)
    runs, start = [], idx[0]
    for a, b in zip(idx, idx[1:] + [None]):
        if b != a + 1:
            runs.append((WEEK[start], WEEK[a])); start = b
    long = ", ".join(LONG[a] if a == b else f"{LONG[a]} – {LONG[b]}" for a, b in runs)
    short = ", ".join(a if a == b else f"{a}–{b}" for a, b in runs)
    return long, short


def hours_rows(data):
    rows = []
    for r in data["rows"]:
        n = f' data-note="{esc(r["note"])}"' if r.get("note") else ""
        rows.append(f'<li data-day="{",".join(r["days"])}"><span>{esc(day_labels(r["days"])[0])}</span><b{n}>{hm(r["opens"])} – {hm(r["closes"])}</b></li>')
    first, *rest = data["rows"]
    cut = " · ".join([hm(first["online_cutoff"])] + [f'{esc(day_labels(r["days"])[1])} {hm(r["online_cutoff"])}' for r in rest])
    rows.append(f'<li data-day="-"><span>Online same-day cutoff</span><b>{cut}</b></li>')
    # holiday closures: site.js shows the ones in the next six weeks and keeps the rest hidden
    for c in data["closures"]:
        n = f' data-note="{esc(c["note"])}"' if c.get("note") else ""
        rows.append(f'<li data-day="-" data-closure="{esc(c["date"][:10])}" hidden><span></span><b{n}>Closed · {esc(c["message"])}</b></li>')
    return "\n          ".join(rows)


def planner(which, data):
    c = data["custom"]
    if which == "flavors":
        return "\n              ".join(f'<div class="chip"><input type="radio" name="flavor" id="f{i}" value="{esc(f["name"])}"{" data-gf=\"1\"" if f["gluten_free"] else ""}><label for="f{i}">{esc(f["name"])}{" <small>gluten-friendly</small>" if f["gluten_free"] else ""}</label></div>' for i, f in enumerate(c["flavors"], 1))
    if which == "frostings":
        return "\n              ".join(f'<div class="chip"><input type="radio" name="frosting" id="r{i}" value="{esc(f["name"])}"{" data-dye=\"1\"" if f["can_be_dyed"] else ""}><label for="r{i}">{esc(f["name"])}</label></div>' for i, f in enumerate(c["frostings"], 1))
    if which == "sizes":
        return "\n              ".join(f'<div class="chip size"><input type="radio" name="size" id="s{i}" value="{esc(s["name"])}" data-feeds="{esc(s["feeds"])}" data-price="{s["from_price"]:g}"><label for="s{i}"><b>{esc(s["button"])}</b><span>Feeds {esc(s["feeds"])} · from ${s["from_price"]:g}</span></label></div>' for i, s in enumerate(c["sizes"], 1))
    if which == "wedding-flavors":
        return "\n              ".join(f'<div class="chip"><input type="checkbox" name="flavors" id="wf{i}" value="{esc(f["name"])}"><label for="wf{i}">{esc(f["name"])}</label></div>' for i, f in enumerate(c["flavors"], 1))
    raise KeyError(which)


def tokens(data):
    cakes, hours, wed, custom, seas = data["cakes"], data["hours"], data["weddings"], data["custom"], data["seasonal"]
    names = [esc(c["title"].lower()) for c in cakes["cakes"] if c["status"] == "everyday"]
    seasonal = [esc(c["title"].lower()) for c in cakes["cakes"] if c["status"] == "seasonal"]
    flav = ", ".join(names) + (f", and this season’s {' and '.join(seasonal)}" if seasonal else "")
    gf = [f["name"].lower() for f in custom["flavors"] if f["gluten_free"]]
    t = {
        "EVERYDAY_COUNT": str(len(names)),
        # planner: which flavor + frosting + size is a same-day cake on Square
        "SAMEDAY_MATCHES": esc(json.dumps({"sizes": [s["size"] for s in cakes["same_day_sizes"]],
                                           "cakes": [{"flavor": c["planner_flavor"], "frosting": c["planner_frosting"], "name": c["title"]}
                                                     for c in cakes["cakes"] if c["status"] != "custom" and c.get("planner_flavor") and c.get("planner_frosting")]},
                                          ensure_ascii=False)),
        "SAMEDAY_FLAVORS": flav[:1].upper() + flav[1:],
        "GF_FLAVORS": esc(", ".join(gf[:-1]) + " and " + gf[-1] if len(gf) > 1 else "".join(gf)),
        "SEASON_LABEL": esc(seas["month_label"]), "SEASON_HOME_INTRO": esc(seas["homepage_intro"]), "SEASON_MENU_INTRO": esc(seas["menu_intro"]),
        "WED_PRICE": f"${wed['price_per_serving']:g}", "WED_PRICE2": f"${wed['price_per_serving']:.2f}", "WED_PRICE_NUM": f"{wed['price_per_serving']:g}",
        "WED_DELIVERY": f"${wed['delivery_from']:g}", "WED_DELIVERY_NUM": f"{wed['delivery_from']:g}",
        "WED_DAYS": esc(wed["consultation_days"]), "WED_DAYS_SHORT": esc(wed["consultation_days_short"]), "WED_HOURS": esc(wed["consultation_hours"]),
    }
    for i, s in enumerate(cakes["same_day_sizes"][:2], 1):
        t.update({f"SD{i}_SIZE": esc(s["size"]), f"SD{i}_PRICE": f"${s['price']:g}", f"SD{i}_FEEDS": esc(s["feeds"])})
    for i, row in enumerate(hours["rows"][:2], 1):
        long, short = day_labels(row["days"])
        t.update({f"CUT{i}": hm(row["online_cutoff"]), f"DAYS{i}": esc(long).replace(" – ", "–"), f"DAYS{i}_SHORT": esc(short)})
    return t


S_STORY = ("Nashville Scene, Belmont News, Nashville Lifestyles and Nfocus profiles (business-dossier.md, sources S09 to S13); "
           "ratings from listings checked 28 Oct 2026 (S07, S08)")


def about_block(a):
    """Their story: one wide photo of the two of them (with a taped cake sticker), then the story in two columns.
    Third person, only facts from the press profiles in the dossier (content/about.json)."""
    ph = photo(a.get("photo"))
    st = photo(a.get("sticker_photo"))
    img = (f'<img src="{ph[0]}" srcset="{ph[1]}" sizes="(max-width: 1100px) 92vw, 1100px" width="{ph[2]}" height="{ph[3]}" alt="{esc(a.get("photo_description", ""))}" loading="lazy">' if ph else "")
    note = f' data-note="{esc(a["photo_note"])}"' if a.get("photo_note") else ""
    label = f'<span class="ph-label">{esc(a["placeholder_label"])}</span>' if a.get("placeholder_label") else ""
    sticker = (f'<div class="booth" aria-hidden="true"><img src="{st[0]}" width="{st[2]}" height="{st[3]}" alt="" loading="lazy">'
               f'<b>{esc(a.get("sticker_caption", ""))}</b></div>' if st else "")
    paras = [esc(p) for p in a["paragraphs"]]
    lead, last = paras[:-1], paras[-1] if paras else ""
    rating = lambda r: f'<a href="{esc(r["link"])}">{esc(r["text"])}</a>' if r.get("link") else esc(r["text"])
    ratings = " · ".join(rating(r) for r in a.get("ratings", []))
    press = ", ".join(f'<a href="{esc(p["link"])}">{esc(p["name"])}</a>' for p in a.get("press", []))
    q = a.get("quote") or {}
    quote = (f'<blockquote class="about-quote"><p>“{esc(q["text"])}”</p><cite><a href="{esc(q["link"])}">{esc(q["source"])}</a></cite></blockquote>' if q.get("text") else "")
    return f'''<section class="section band-blush about about-wide" aria-labelledby="about-title">
    <div class="wrap" data-source="{S_STORY}">
      <h2 id="about-title" class="reveal">{esc(a["heading"])}</h2>
      <figure class="owners reveal">
        <div class="frame"{note}>{img}</div>
        {label}
        {sticker}
      </figure>
      <div class="story">
        <div class="about-text reveal">{"".join(f"<p>{p}</p>" for p in lead)}</div>
        <div class="side reveal" style="--d:.1s">
          {f'<p class="strawberry">{last}</p>' if last else ""}
          {quote}
          <ul class="proof">
            {f'<li data-note="Confirm you’re happy for us to show your ratings (they change often; checked 28 Oct 2026).">{ratings}</li>' if ratings else ""}
            {f'<li>Featured in {press}</li>' if press else ""}
          </ul>
        </div>
      </div>
    </div>
  </section>'''


def load_all():
    return {"cakes": load("cakes.json"), "seasonal": load("seasonal.json"), "lists": load("menu-lists.json"), "events": load("events.json"),
            "hours": load("hours.json"), "weddings": load("weddings.json"), "custom": load("custom-cakes.json"), "about": load("about.json"), "case": load("todays-case.json")}


def build():
    data = load_all()
    if not data["hours"].get("rows") or not all(r.get("days") for r in data["hours"]["rows"]):
        # never publish a site that says "Closed" forever: stop, and the last good pages stay live
        raise SystemExit("content/hours.json has no opening hours; the site was not rebuilt.")
    shop = json.dumps({"rows": [{k: r[k] for k in ("days", "opens", "closes", "online_cutoff")} for r in data["hours"]["rows"]],
                       "closures": [{"date": c["date"][:10], "message": c["message"]} for c in data["hours"]["closures"]]},
                      ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tok = tokens(data)
    for page in sorted((SITE / "tools" / "pages").glob("*.html")):
        t = page.read_text(encoding="utf-8")
        t = re.sub(r"<!--@head (.+?)\|(.+?)-->", lambda m: head(m.group(1), m.group(2)), t)
        t = re.sub(r"<!--@header (\w*)-->", lambda m: header(m.group(1), shop), t)
        t = t.replace("<!--@footer-->", footer(data["hours"]))
        t = re.sub(r"<!--@cakes (all|home)-->", lambda m: cakes_block(m.group(1), data["cakes"]), t)
        t = re.sub(r"<!--@seasonal (home|menu)-->", lambda m: seasonal_block(m.group(1), data["seasonal"]), t)
        t = re.sub(r"<!--@list (cookies|treats)-->", lambda m: list_block(m.group(1), data["lists"]), t)
        t = t.replace("<!--@events-->", events_block(data["events"]))
        t = t.replace("<!--@hours-->", hours_rows(data["hours"]))
        t = t.replace("<!--@about-->", about_block(data["about"]))
        t = t.replace("<!--@todays-case-->", todays_case(data["case"]))
        t = re.sub(r"<!--@planner ([\w-]+)-->", lambda m: planner(m.group(1), data), t)
        t = re.sub(r"<!--@icon (\w+)-->", lambda m: icon(m.group(1), w=20), t)
        t = t.replace("{{SQUARE}}", SQUARE).replace("{{TEL}}", TEL).replace("{{MAPS}}", MAPS).replace("{{ELECTRIC_MIXER}}", ELECTRIC_MIXER)
        t = re.sub(r"\{\{(\w+)\}\}", lambda m: tok[m.group(1)], t)
        (SITE / page.name).write_text(t, encoding="utf-8")
        print("built", page.name)


def watch():
    """Rebuild whenever a content file, page template or upload changes (for the editor demo)."""
    def stamp():
        files = [*CONTENT.glob("*.json"), *(SITE / "tools" / "pages").glob("*.html"), *(SITE / "assets" / "uploads").glob("*")]
        return {f: f.stat().st_mtime for f in files}
    last = stamp()
    print("watching content/ for changes (Ctrl+C to stop)")
    while True:
        time.sleep(1)
        now = stamp()
        if now != last:
            time.sleep(.3)  # let the editor finish writing
            try:
                build()
            except Exception as e:  # a half-saved file: report it and keep watching
                print("build failed:", e)
            last = stamp()


if __name__ == "__main__":
    build()
    if "--watch" in sys.argv:
        watch()
