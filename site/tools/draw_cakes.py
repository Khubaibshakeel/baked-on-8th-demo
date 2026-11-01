"""Draw the Baked on 8th cake illustrations as SVG, one per cake, from notes taken off the real photos.

Each spec below records what the photo shows: buttercream colour and texture, rosettes, drip,
sprinkle colours and toppers. The style (linework, shading, grain, framing) is shared so the set reads as one family.
Framing matches the 3:4 product photos: cake centred, board at ~78% height, faint white-brick backdrop.

Usage: python draw_cakes.py <out_dir> [name ...]
"""
import math, random, sys
from pathlib import Path

W, H = 600, 800
INK = "#4A2C2A"
RAINBOW = ["#F25C78", "#F6B93B", "#4FB3E8", "#7BCB6B", "#B57BE0", "#FF8F4F", "#FFFFFF"]
RED_WHITE = ["#D7263D", "#D7263D", "#FFFFFF", "#F2F2F2"]

CAKES = {
    "confetti": dict(body="#F4A9BB", shade="#D97C93", light="#FCD3DD", top="#F7B9C8", comb=True,
                     speckle=RAINBOW, rosette="#FFF4DF", rosette_shade="#E7D2AC", n_ros=9,
                     sprinkles=RAINBOW, pearls=["#F7B9C8", "#9ED9C3", "#FFFFFF"]),
    "classic": dict(body="#8B5636", shade="#653B22", light="#AE754F", top="#94603F", comb=True,
                    rosette="#7F4C2F", rosette_shade="#5A3320", n_ros=9, sprinkles=RAINBOW,
                    pearls=["#9ED9C3", "#F7B9C8", "#FFFFFF"]),
    "chocolate-ganache": dict(body="#7E4C30", shade="#5B331F", light="#9E6646", top="#7B472B", comb=False,
                              drip="#3B2015", rosette="#7A472C", rosette_shade="#55301D", n_ros=11,
                              center_swirl=True, sprinkles=RAINBOW),
    "strawberry": dict(body="#F3DCCB", shade="#D9B9A3", light="#FBEDE2", top="#F5E0D1", comb=True,
                       speckle=["#E05A6B", "#F08B98"], rosette="#F9E6D6", rosette_shade="#E2C2AC", n_ros=9,
                       sprinkles=RAINBOW),
    "cookies-and-cream": dict(body="#D2CBC4", shade="#ABA29A", light="#E8E2DC", top="#D9D1C9", comb=False,
                              speckle=["#2F2928", "#4A4240"], drip="#3A1F14", crumbs=True,
                              rosette="#FFF7EA", rosette_shade="#E3D6BE", n_ros=10, sprinkles=RAINBOW),
    "peanut-butter-ganache": dict(body="#D8B68E", shade="#B58F66", light="#E9CFAE", top="#DDBE98", comb=False,
                                  drip="#3D2116", rosette="#7A472C", rosette_shade="#55301D", n_ros=9,
                                  sprinkles=RAINBOW),
    "vanilla-almond": dict(body="#FBF3E2", shade="#E3D3B4", light="#FFFBF3", top="#FCF6E9", comb=True,
                           rosette="#FFF9EE", rosette_shade="#E6D4B2", n_ros=9, sprinkles=RAINBOW, sparse=True),
    "carrot": dict(body="#FBF2DF", shade="#E2D0AE", light="#FFFAF0", top="#FCF4E6", comb=True,
                   rosette="#FFF8EA", rosette_shade="#E4D0AC", n_ros=9, sprinkles=RAINBOW, carrot=True),
    "red-velvet": dict(body="#FBF2E0", shade="#E2D1B0", light="#FFFAF1", top="#FCF5E7", comb=True,
                       rosette="#FFF8EB", rosette_shade="#E4D1AE", n_ros=9, sprinkles=RED_WHITE),
    "pumpkin-spice": dict(body="#E2C6A8", shade="#C29E7A", light="#F0DCC6", top="#E8D0B6", comb=True,
                          speckle=["#9A6A44", "#B07E57"], rosette="#FFF6E4", rosette_shade="#E5D2B0", n_ros=12,
                          sprinkles=[], pearls=["#FFFFFF", "#FFFFFF", "#F4ECDF"], tall=True, pumpkins=True),
}


def f(v):
    return f"{v:.1f}"


def rosette(x, y, k, col, shade, phase):
    """A piped star-tip rosette seen from slightly above: lobed base, rising spiral ridge, curled peak."""
    sq = .58      # vertical squash of the base (viewing angle)
    lift = .68 * k  # height of the swirl; the shop's rosettes are low and wide
    # lobed outline: base ring + upper silhouette of the dome
    pts = []
    for i in range(49):
        th = i / 48 * 2 * math.pi
        r = k * (1 + .07 * math.sin(8 * th + phase))
        px = x + math.cos(th) * r
        py = y + math.sin(th) * r * sq
        if math.sin(th) < 0:  # back half of the outline rises into a dome
            py -= lift * .55 * (-math.sin(th)) ** 1.4
        pts.append((px, py))
    outline = "M" + " L".join(f"{f(a)},{f(b)}" for a, b in pts) + "Z"
    # spiral ridge climbing to the peak
    sp = []
    for i in range(56):
        t = i / 55
        th = phase + t * 2.8 * math.pi
        r = k * (0.86 - 0.8 * t)
        sp.append((x + math.cos(th) * r, y + math.sin(th) * r * sq - lift * (0.12 + 0.62 * t)))
    spiral = "M" + " L".join(f"{f(a)},{f(b)}" for a, b in sp)
    hx, hy = sp[-1]
    return (f'<path d="{outline}" fill="{col}" stroke="{INK}" stroke-width="3.4" stroke-linejoin="round"/>'
            f'<path d="{spiral}" fill="none" stroke="{shade}" stroke-width="{f(k*.13)}" stroke-linecap="round" opacity=".9"/>'
            f'<path d="{spiral}" fill="none" stroke="#FFFFFF" stroke-width="{f(k*.05)}" stroke-linecap="round" opacity=".55" transform="translate({f(-k*.06)},{f(-k*.07)})"/>'
            f'<path d="M{f(hx)},{f(hy)} q{f(k*.08)},{f(-k*.22)} {f(-k*.1)},{f(-k*.3)}" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')


def draw(name, s, bare=False):
    """bare=True drops the backdrop and grain and crops tight, for small decorative use."""
    rnd = random.Random(name)
    cx = W / 2
    # Photos are shot slightly from above with the cake filling ~3/4 of the frame width
    R, Ry = (170, 50) if s.get("tall") else (232, 66)
    T, B = (270, 526) if s.get("tall") else (292, 486)
    out = []
    a = out.append

    def yfront(x):
        u = (x - cx) / R
        return T + Ry * math.sqrt(max(0.0, 1 - u * u))

    # ---------- defs: shading, grain, hand-drawn wobble ----------
    a(f"""<defs>
<linearGradient id="body" x1="0" x2="1"><stop offset="0" stop-color="{s['shade']}"/><stop offset=".22" stop-color="{s['body']}"/><stop offset=".42" stop-color="{s['light']}"/><stop offset=".7" stop-color="{s['body']}"/><stop offset="1" stop-color="{s['shade']}"/></linearGradient>
<radialGradient id="topg" cx=".42" cy=".38" r=".7"><stop offset="0" stop-color="{s['light']}"/><stop offset="1" stop-color="{s['top']}"/></radialGradient>
<filter id="wob" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="4"/><feDisplacementMap in="SourceGraphic" scale="3.2"/></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7"/><feColorMatrix values="0 0 0 0 .29  0 0 0 0 .17  0 0 0 0 .16  0 0 0 .55 -.2"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<clipPath id="bodyclip"><path d="M{f(cx-R)},{T} L{f(cx-R)},{B} A{R},{Ry} 0 0 0 {f(cx+R)},{B} L{f(cx+R)},{T} Z"/></clipPath>
</defs>""")

    # ---------- backdrop: cream with faint white brick, like the shop wall in the photos ----------
    if not bare:
        a(f'<rect width="{W}" height="{H}" fill="#FBF1E8"/>')
        bricks = []
        for row, y in enumerate(range(0, H, 46)):
            bricks.append(f"M0,{y}H{W}")
            off = 0 if row % 2 else 70
            for x in range(off, W, 140):
                bricks.append(f"M{x},{y}v46")
        a(f'<path d="{" ".join(bricks)}" stroke="#EADCCF" stroke-width="3" fill="none" opacity=".75"/>')

    g = []  # the cake, drawn inside the wobble filter
    p = g.append

    # board + soft floor shadow
    p(f'<ellipse cx="{cx}" cy="{B+14}" rx="{R+52}" ry="{Ry*0.62+14}" fill="#7A4E3E" opacity=".12"/>')
    p(f'<ellipse cx="{cx}" cy="{B+4}" rx="{R+38}" ry="{Ry*0.62+12}" fill="#FFFFFF" stroke="{INK}" stroke-width="4"/>')
    p(f'<path d="M{f(cx-R-38)},{B+4} a{R+38},{f(Ry*0.62+12)} 0 0 0 {2*(R+38)},0" fill="none" stroke="#D9D2CC" stroke-width="6" opacity=".7"/>')

    # pumpkins sit on the board, behind the cake's lower edge only at the back
    # body
    p(f'<path d="M{f(cx-R)},{T} L{f(cx-R)},{B} A{R},{Ry} 0 0 0 {f(cx+R)},{B} L{f(cx+R)},{T} Z" fill="url(#body)"/>')
    clip = []
    if s.get("comb"):
        for y in range(T + 22, B - 4, 19):
            clip.append(f'<path d="M{f(cx-R)},{y} A{R},{Ry} 0 0 0 {f(cx+R)},{y}" fill="none" stroke="{s["shade"]}" stroke-width="3" opacity=".42"/>')
            clip.append(f'<path d="M{f(cx-R)},{y+5} A{R},{Ry} 0 0 0 {f(cx+R)},{y+5}" fill="none" stroke="{s["light"]}" stroke-width="2" opacity=".55"/>')
    for col in s.get("speckle", []):
        dots = []
        for _ in range(170 // max(1, len(s["speckle"]) // 2 + 1)):
            x = rnd.uniform(cx - R + 6, cx + R - 6)
            y = rnd.uniform(T + 8, B + Ry * 0.8)
            dots.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rnd.uniform(1.4, 2.8))}"/>')
        clip.append(f'<g fill="{col}" opacity=".85">{"".join(dots)}</g>')
    p(f'<g clip-path="url(#bodyclip)">{"".join(clip)}</g>')
    p(f'<path d="M{f(cx-R)},{T} L{f(cx-R)},{B} A{R},{Ry} 0 0 0 {f(cx+R)},{B} L{f(cx+R)},{T}" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linejoin="round"/>')

    # top surface (+ ganache rim when the cake has a drip)
    if s.get("drip"):
        p(f'<ellipse cx="{cx}" cy="{T}" rx="{R}" ry="{Ry}" fill="{s["drip"]}" stroke="{INK}" stroke-width="4.5"/>')
        p(f'<ellipse cx="{cx}" cy="{T-1}" rx="{R-14}" ry="{Ry-6}" fill="url(#topg)"/>')
    else:
        p(f'<ellipse cx="{cx}" cy="{T}" rx="{R}" ry="{Ry}" fill="url(#topg)" stroke="{INK}" stroke-width="4.5"/>')

    if s.get("crumbs"):
        cr = []
        for _ in range(140):
            ang = rnd.uniform(0, 2 * math.pi); rr = math.sqrt(rnd.random())
            cr.append(f'<circle cx="{f(cx + math.cos(ang) * (R-18) * rr)}" cy="{f(T + math.sin(ang) * (Ry-8) * rr)}" r="{f(rnd.uniform(1.5, 3.4))}"/>')
        p(f'<g fill="#3A302E" opacity=".8">{"".join(cr)}</g>')

    # drip: one outline whose lower edge is a sum of rounded drips, so there are no internal seams
    if s.get("drip"):
        drips = []
        x = cx - R + 10
        while x < cx + R - 8:
            drips.append((x, rnd.uniform(6.5, 11), rnd.choice([rnd.uniform(16, 34), rnd.uniform(34, 78)])))
            x += rnd.uniform(20, 34)
        xs = [cx - R + i for i in range(0, 2 * R + 1, 2)]
        top_pts = [(xx, yfront(xx) - 3) for xx in xs]
        bot = []
        for xx in reversed(xs):
            extra = 0.0
            for (dc, dw, dl) in drips:
                u = (xx - dc) / dw
                if abs(u) < 1:
                    extra = max(extra, dl * math.sqrt(1 - u * u) ** 0.6)
            bot.append((xx, yfront(xx) + 12 + extra))
        pts = top_pts + bot
        d = "M" + " L".join(f"{f(px)},{f(py)}" for px, py in pts) + " Z"
        p(f'<path d="{d}" fill="{s["drip"]}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
        # gloss
        p(f'<path d="M{f(cx-R*0.62)},{f(yfront(cx-R*0.62)+6)} Q{f(cx-R*0.35)},{f(yfront(cx-R*0.35)+12)} {f(cx-R*0.12)},{f(yfront(cx-R*0.12)+9)}" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" opacity=".35"/>')

    if s.get("center_swirl"):
        sw = []
        for k in range(4):
            sw.append(f'<ellipse cx="{cx}" cy="{T-2}" rx="{f(46 - k*11)}" ry="{f(12 - k*2.8)}"/>')
        p(f'<g fill="none" stroke="#4A2817" stroke-width="5">{"".join(sw)}</g>')
        p(f'<ellipse cx="{cx}" cy="{T-2}" rx="52" ry="14" fill="none" stroke="{INK}" stroke-width="2.5" opacity=".5"/>')

    if s.get("carrot"):
        p(f'<g transform="translate({cx-6},{T-8}) rotate(-12)"><path d="M-30,0 Q-26,-9 0,-8 Q26,-6 30,0 Q26,6 0,8 Q-26,9 -30,0Z" fill="#F07A2B" stroke="{INK}" stroke-width="3"/>'
          f'<path d="M-18,-4v8M-6,-6v12M8,-6v12" stroke="#C85A17" stroke-width="2"/>'
          f'<path d="M30,0 l14,-10 M30,0 l16,0 M30,0 l14,10" stroke="#4E9A3F" stroke-width="5" stroke-linecap="round"/></g>')

    # rosettes in a ring, back row first so the front ones overlap
    n = s["n_ros"]
    rr = 0.78 if not s.get("tall") else 0.84
    size = 50 if not s.get("tall") else 28
    ros = []
    for i in range(n):
        ang = (i / n) * 2 * math.pi + 0.18
        ros.append((cx + math.cos(ang) * R * rr, T + math.sin(ang) * Ry * rr - 4))
    ros.sort(key=lambda q: q[1])
    for (x, y) in ros:
        k = size * (0.9 + 0.2 * (y - (T - Ry)) / (2 * Ry))
        p(rosette(x, y, k, s["rosette"], s["rosette_shade"], rnd.uniform(0, 6.28)))

    if s.get("tall"):  # pumpkin cake: dollop collar has a centre well like the photo
        p(f'<ellipse cx="{cx}" cy="{T-2}" rx="{R*0.52}" ry="{Ry*0.42}" fill="{s["top"]}" stroke="{INK}" stroke-width="2.5" opacity=".9"/>')

    # sprinkles + pearls scattered over the top and rosettes
    spr = []
    pal = s.get("sprinkles", [])
    count = 40 if s.get("sparse") else 95
    for i in range(count if pal else 0):
        ang = rnd.uniform(0, 2 * math.pi); r2 = math.sqrt(rnd.random())
        x = cx + math.cos(ang) * (R - 12) * r2
        y = T + math.sin(ang) * (Ry - 4) * r2 - rnd.uniform(0, size * .8)
        col = pal[i % len(pal)]
        spr.append(f'<rect x="{f(x-5)}" y="{f(y-1.8)}" width="10" height="3.6" rx="1.8" fill="{col}" stroke="{INK}" stroke-width=".8" transform="rotate({rnd.randint(0,179)} {f(x)} {f(y)})"/>')
    for i in range(10 if s.get("pearls") else 0):
        ang = rnd.uniform(0, 2 * math.pi); r2 = rnd.uniform(.55, .95)
        x = cx + math.cos(ang) * R * r2; y = T + math.sin(ang) * Ry * r2 - rnd.uniform(6, 24)
        col = s["pearls"][i % len(s["pearls"])]
        spr.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="5.2" fill="{col}" stroke="{INK}" stroke-width="1.6"/><circle cx="{f(x-1.6)}" cy="{f(y-1.8)}" r="1.6" fill="#fff"/>')
    p("".join(spr))

    # pumpkins round the base of the pumpkin spice cake (orange, tan and one white, as photographed)
    if s.get("pumpkins"):
        cols = ["#E89A55", "#D9B183", "#F2F0EA", "#E3A86A", "#C99A66", "#E89A55", "#D9B183"]
        for i, t in enumerate([-0.92, -0.62, -0.3, 0.0, 0.3, 0.62, 0.92]):
            x = cx + t * R
            y = B + Ry * math.sqrt(max(0, 1 - t * t)) - 6
            pw, ph = 26, 24
            p(f'<g><ellipse cx="{f(x)}" cy="{f(y)}" rx="{pw}" ry="{ph}" fill="{cols[i]}" stroke="{INK}" stroke-width="3.2"/>'
              f'<path d="M{f(x)},{f(y-ph)} Q{f(x-12)},{f(y)} {f(x)},{f(y+ph)} M{f(x)},{f(y-ph)} Q{f(x+12)},{f(y)} {f(x)},{f(y+ph)}" fill="none" stroke="{INK}" stroke-width="2" opacity=".55"/>'
              f'<path d="M{f(x)},{f(y-ph)} q2,-9 8,-11" fill="none" stroke="#6B8F3A" stroke-width="4" stroke-linecap="round"/></g>')

    a(f'<g filter="url(#wob)">{"".join(g)}</g>')
    if bare:
        vb = f"{cx-R-50} {T-Ry-70} {2*R+100} {B-T+Ry*2+90}"
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" aria-hidden="true">{"".join(out)}</svg>'
    a(f'<rect width="{W}" height="{H}" fill="#fff" filter="url(#grain)" opacity=".16" style="mix-blend-mode:multiply"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">{"".join(out)}</svg>'


if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    names = sys.argv[2:] or list(CAKES)
    for n in names:
        (out / f"cake-{n}.svg").write_text(draw(n, CAKES[n]), encoding="utf-8")
        (out / f"cake-{n}-bare.svg").write_text(draw(n, CAKES[n], bare=True), encoding="utf-8")
        print(n, round((out / f"cake-{n}.svg").stat().st_size / 1024, 1), "KB")
