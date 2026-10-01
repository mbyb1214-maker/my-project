import skia, math, numpy as np
from gfx import *

rs = np.random.default_rng(11)
# ---------- stars (world-space, with parallax layers) ----------
STAR_L = []
for p, dens, sz in ((0.25, 1/4200, 1.2), (0.45, 1/5200, 1.6), (0.7, 1/7000, 2.2)):
    lo, hi = -700, 5400 * p + 900
    n = int(1500 * (hi - lo) * dens)
    STAR_L.append(dict(p=p, x=rs.uniform(-200, 1480, n), alt=rs.uniform(lo, hi, n),
                       s=rs.uniform(0.6, 1.0, n) * sz, ph=rs.uniform(0, 6.28, n), sp=rs.uniform(0.8, 3.0, n),
                       tint=rs.choice(['#ffffff', '#cfe0ff', '#ffe9c4', '#e6d4ff'], n)))

def sky(cv, alt, mode='night'):
    if mode == 'dawn':
        top, mid, bot = '#4d4a9e', '#f08fb0', '#ffd8a0'
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=lin(0, 0, 0, H, [top, mid, bot], [0, .62, 1])))
        return
    keys = [(0, '#080d33', '#1b2a7a', '#6a4fa0'), (1500, '#060a2a', '#16226e', '#3b3a8c'),
            (3200, '#04081f', '#0f1d5c', '#0e4a6e'), (5300, '#050a26', '#17307a', '#2a2f8f')]
    for i in range(len(keys) - 1):
        if keys[i][0] <= alt <= keys[i + 1][0] or i == len(keys) - 2:
            a = keys[i]; b = keys[i + 1]; t = clamp((alt - a[0]) / (b[0] - a[0])); break
    cols = [mix(a[k], b[k], t) for k in (1, 2, 3)]
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=lin(0, 0, 0, H, cols, [0, .55, 1])))

def stars(cv, cy, cx, Z, t, alt, mode='night'):
    vis = 0.28 + 0.72 * sstep(0, 2600, alt)
    if mode == 'dawn': vis = 0.12
    for L in STAR_L:
        p = L['p']
        sy = H / 2 + (-L['alt'] - cy * p) * Z
        sx = W / 2 + (L['x'] - cx * p * 0.3 - 640) * Z * 1.0
        m = (sy > -10) & (sy < H + 10) & (sx > -10) & (sx < W + 10)
        for i in np.nonzero(m)[0]:
            tw = 0.55 + 0.45 * math.sin(t * L['sp'][i] + L['ph'][i])
            a = vis * tw
            r = L['s'][i] * (1 if Z < 1.3 else 1.3)
            cv.drawCircle(float(sx[i]), float(sy[i]), float(r), paint(L['tint'][i], a))
            if L['s'][i] > 2.0 and a > 0.5:
                glow(cv, float(sx[i]), float(sy[i]), float(r * 5), L['tint'][i], a * .35)

def moon(cv, cy, cx, Z, t, mode='night'):
    if mode == 'dawn': return
    p = 0.35
    x = W / 2 + (960 - cx * p * 0.3 - 640) * Z; y = H / 2 + (-250 - cy * p) * Z; r = 82 * Z
    if y < -r * 3: return
    glow(cv, x, y, r * 3.6, '#ffe9a8', 0.30)
    glow(cv, x, y, r * 1.8, '#fff3c8', 0.30)
    cv.drawCircle(x, y, r, paint(shader=rad(x - r * .3, y - r * .3, r * 1.4, ['#fffbe8', '#ffe9b0', '#e8c987'], [0, .6, 1])))
    for dx, dy, rr in ((-.3, -.1, .22), (.25, .25, .17), (.1, -.38, .12), (-.1, .38, .1)):
        cv.drawCircle(x + dx * r, y + dy * r, rr * r, paint('#d9b878', .35))

# ---------- city ----------
def _mk_city(seed, n, hmin, hmax, wmin, wmax):
    r = np.random.default_rng(seed); x = -250; out = []
    while x < 1600:
        w = r.uniform(wmin, wmax); h = r.uniform(hmin, hmax)
        wins = []
        for wy in range(int(h // 22)):
            for wx in range(int(w // 16)):
                if r.random() < 0.55: wins.append((wx, wy, r.random(), r.uniform(0, 6.28), r.uniform(10, 40)))
        out.append(dict(x=x, w=w, h=h, wins=wins, roof=int(r.integers(0, 4)))); x += w + r.uniform(-6, 10)
    return out
CITY = [(_mk_city(3, 0, 90, 300, 60, 130), 0.88, '#0b1030', '#10173f'),
        (_mk_city(5, 0, 50, 190, 50, 110), 0.95, '#070a22', '#0a0f30')]

def city(cv, cy, cx, Z, t, mode='night', sleep_t=None):
    for li, (blds, p, col, colb) in enumerate(CITY):
        camy = H / 2 + (0 - cy * p) * Z   # screen y of world y=0 at this parallax
        if camy < -400: continue
        base_x = W / 2 + (-cx * p * 0.5 - 640 + 640 * 0.0) * Z
        dawn = mode == 'dawn'
        for b in blds:
            x = W / 2 + (b['x'] - cx * p * 0.5 - 640) * Z; w = b['w'] * Z; h = b['h'] * Z
            top = camy - h * (0.9 if li == 0 else 0.8) - (0 if li else 20 * Z)
            if x > W + 20 or x + w < -20: continue
            colr = mix(col, '#7a5aa0', 0.35 if dawn else 0) if dawn else col
            cv.drawRect(skia.Rect.MakeXYWH(x, top, w, 900 * Z), paint(colr if isinstance(colr, str) else colr))
            cv.drawRect(skia.Rect.MakeXYWH(x, top, w, 3 * Z), paint('#5d63b0' if not dawn else '#ffc0b0', .35))
            if b['roof'] == 1:   # antenna
                cv.drawRect(skia.Rect.MakeXYWH(x + w * .5, top - 30 * Z, 2 * Z, 30 * Z), paint(colr if isinstance(colr, str) else colr))
            if b['roof'] == 2:
                cv.drawRect(skia.Rect.MakeXYWH(x + w * .2, top - 14 * Z, w * .3, 14 * Z), paint(colr if isinstance(colr, str) else colr))
            for wx, wy, rv, ph, per in b['wins']:
                # windows turn off one by one as the city falls asleep
                off_t = 2 + rv * 8.5 if sleep_t is not None else 999
                on = (sleep_t is None) or (sleep_t < off_t) or (sleep_t > 55)
                if dawn: on = rv < 0.5
                if not on: continue
                a = 0.55 + 0.25 * math.sin(t * 0.6 + ph)
                wxp = x + (6 + wx * 16) * Z; wyp = top + (8 + wy * 22) * Z
                if wyp > H or wyp < -10: continue
                cv.drawRect(skia.Rect.MakeXYWH(wxp, wyp, 8 * Z, 11 * Z),
                            paint('#ffd88a' if rv < 0.8 else '#bfe6ff', a * (0.35 if dawn else 1)))
    # horizon glow
    gy = H / 2 + (20 - cy * 0.95) * Z
    if -200 < gy < H + 400:
        col = '#ff8f7a' if mode == 'dawn' else '#d86aa8'
        cv.drawRect(skia.Rect.MakeXYWH(0, gy - 220 * Z, W, 300 * Z),
                    paint(shader=lin(0, gy - 220 * Z, 0, gy + 40 * Z, [(col, 0.0), (col, 0.30 if mode != 'dawn' else 0.5)], [0, 1]), blend='plus'))

# ---------- clouds ----------
def _mk_clouds():
    r = np.random.default_rng(21); out = []
    for i in range(70):
        alt = r.uniform(800, 2700); p = r.choice([0.9, 1.0, 1.15, 1.35]); out.append(dict(
            x=r.uniform(-300, 1600), alt=alt, p=p, s=r.uniform(0.7, 1.6) * (1.0 + (p - 1) * 1.0),
            blobs=[(r.uniform(-1, 1), r.uniform(-0.25, 0.2), r.uniform(0.4, 0.9)) for _ in range(6)]))
    return out
CLOUDS = _mk_clouds()
def clouds(cv, cy, cx, Z, t, alt, front=False):
    for c in CLOUDS:
        if (c['p'] >= 1.3) != front: continue
        sy = H / 2 + (-c['alt'] - cy * c['p']) * Z
        if sy < -250 or sy > H + 250: continue
        sx = W / 2 + (c['x'] + 30 * math.sin(t * .1 + c['x']) - cx * 0.3 * c['p'] - 640) * Z
        # pink underlight low, silver/blue higher
        up = sstep(800, 2700, c['alt'])
        base = mix('#d9a5d6', '#9fb4ee', up); top = mix('#f3ddf5', '#e1ecff', up)
        S = c['s'] * 85 * Z
        for bx, by, br in c['blobs']:
            x = sx + bx * S * 1.5; y = sy + by * S * 0.7; r = br * S
            cv.drawCircle(x, y, r, paint(shader=rad(x, y - r * .3, r * 1.1, [(top, .92), (base, .85), (base, 0.0)], [0, .74, 1])))

# ---------- aurora ----------
def aurora(cv, cy, cx, Z, t, strength):
    if strength <= 0.01: return
    p = 0.8
    for k, (c1, c2, ph, ya) in enumerate((('#46ffb5', '#7a5cff', 0.0, 4300), ('#69f0ff', '#d36bff', 2.1, 4700), ('#8bffc9', '#4f7bff', 4.0, 5100))):
        top_y = H / 2 + (-ya - cy * p) * Z
        if top_y > H + 500 or top_y < -1200 * Z: continue
        xs = np.arange(-20, W + 60, 20)
        pts = [(float(x), float(top_y + (60 * math.sin(x * 0.006 + t * 0.35 + ph) + 35 * math.sin(x * 0.015 - t * 0.5 + ph * 2)) * Z)) for x in xs]
        path = skia.Path(); path.moveTo(pts[0][0], pts[0][1])
        for q in pts[1:]: path.lineTo(*q)
        for q, x in zip(reversed(pts), reversed(xs)):
            hh = (260 + 90 * math.sin(x * 0.01 + t * 0.4 + ph * 3)) * Z
            path.lineTo(float(x), q[1] + hh)
        path.close()
        sh = lin(0, top_y - 40 * Z, 0, top_y + 360 * Z, [(c1, 0.0), (c1, .85 * strength), (c2, .35 * strength), (c2, 0.0)], [0, .12, .55, 1])
        pa = paint(shader=sh, blend='plus'); pa.setImageFilter(skia.ImageFilters.Blur(10, 18))
        cv.drawPath(path, pa)
        # vertical rays
        for x in xs[::2]:
            hh = (200 + 120 * (0.5 + 0.5 * math.sin(x * .037 + t * .8 + ph * 5))) * Z
            yy = top_y + (60 * math.sin(x * 0.006 + t * 0.35 + ph) + 35 * math.sin(x * 0.015 - t * 0.5 + ph * 2)) * Z
            cv.drawLine(float(x), yy, float(x), yy + hh, paint(shader=lin(0, yy, 0, yy + hh, [(c1, .25 * strength), (c2, 0)]), stroke=3, blend='plus'))

# ---------- rooftop ----------
def roof(cv, cy, cx, Z, t, mode='night'):
    """near layer: deck, parapet, props. world y=0 is the back edge of the deck."""
    def X(x): return W / 2 + (x - cx - 0) * Z
    def Y(y): return H / 2 + (y - cy) * Z
    dawn = mode == 'dawn'
    deck_top = '#1d2352' if not dawn else '#8a5f9a'
    deck_bot = '#10142e' if not dawn else '#5a3f78'
    face = '#0c1028' if not dawn else '#3d2a58'
    rim = '#4a5aa8' if not dawn else '#ffd0b8'
    x0 = -50; x1 = W + 50
    if Y(-60) > H: return
    # parapet wall (back)
    cv.drawRect(skia.Rect.MakeLTRB(x0, Y(-34), x1, Y(2)), paint(deck_bot if not dawn else '#6b4a88'))
    cv.drawRect(skia.Rect.MakeLTRB(x0, Y(-36), x1, Y(-31)), paint(rim, .6))
    # deck
    cv.drawRect(skia.Rect.MakeLTRB(x0, Y(2), x1, Y(100)), paint(shader=lin(0, Y(2), 0, Y(100), [deck_top, deck_bot])))
    cv.drawRect(skia.Rect.MakeLTRB(x0, Y(100), x1, Y(1400)), paint(face))
    cv.drawRect(skia.Rect.MakeLTRB(x0, Y(98), x1, Y(104)), paint(rim, .5))
    # tiles lines
    for i in range(-6, 30):
        xx = X(i * 130 - cx * 0)
        cv.drawLine(xx, Y(2), X(i * 130 + (i - 5) * 18 - 200 * 0), Y(100), paint(rim, .10, stroke=2))
    # water tank (left)
    tx = X(110); 
    cv.drawRect(skia.Rect.MakeXYWH(tx, Y(-190), 150 * Z, 150 * Z), paint(shader=lin(tx, 0, tx + 150 * Z, 0, ['#2a3370' if not dawn else '#a07aa8', '#151b46' if not dawn else '#6e4f86'])))
    cv.drawOval(skia.Rect.MakeXYWH(tx, Y(-204), 150 * Z, 28 * Z), paint('#3a4590' if not dawn else '#c9a0b8'))
    for lx in (tx + 20 * Z, tx + 125 * Z): cv.drawRect(skia.Rect.MakeXYWH(lx, Y(-42), 8 * Z, 44 * Z), paint(deck_bot))
    # antenna mast (right) with blinking red light
    ax = X(1120)
    cv.drawRect(skia.Rect.MakeXYWH(ax, Y(-340), 5 * Z, 340 * Z), paint(deck_bot))
    cv.drawRect(skia.Rect.MakeXYWH(ax - 36 * Z, Y(-300), 77 * Z, 4 * Z), paint(deck_bot))
    cv.drawRect(skia.Rect.MakeXYWH(ax - 24 * Z, Y(-262), 53 * Z, 4 * Z), paint(deck_bot))
    bl = 0.5 + 0.5 * math.sin(t * 3)
    if not dawn: glow(cv, ax + 2 * Z, Y(-342), 26 * Z, '#ff4a4a', .4 + .6 * bl, 0.18)
    # fairy lights catenary tank -> mast
    ptsx = np.linspace(tx + 75 * Z, ax + 2 * Z, 30)
    y_a = Y(-205); y_b = Y(-330); sag = 90 * Z
    path = skia.Path(); first = True; bulbs = []
    for i, xx in enumerate(ptsx):
        u = i / 29; yy = lerp(y_a, y_b, u) + sag * 4 * u * (1 - u)
        (path.moveTo if first else path.lineTo)(float(xx), float(yy)); first = False
        if i % 3 == 1: bulbs.append((float(xx), float(yy) + 7 * Z, i))
    cv.drawPath(path, paint('#05071a' if not dawn else '#4a3060', .9, stroke=2))
    for bx, by, i in bulbs:
        col = ['#ffd27a', '#ff9ec2', '#9fe8ff', '#b9ff9f'][i % 4]
        a = 0.65 + 0.35 * math.sin(t * 2 + i)
        glow(cv, bx, by, 20 * Z, col, a * (0.4 if dawn else 0.9), .12)
    # vents
    cv.drawRect(skia.Rect.MakeXYWH(X(1260), Y(-70), 90 * Z, 72 * Z), paint(deck_bot))
    cv.drawRect(skia.Rect.MakeXYWH(X(1250), Y(-82), 110 * Z, 14 * Z), paint(deck_top))
    cv.drawRect(skia.Rect.MakeXYWH(X(-60), Y(-50), 70 * Z, 52 * Z), paint(deck_bot))

NEB = [(300, 3000, 520, '#6a3fd0', .22, .5), (1000, 3800, 640, '#2a9ad8', .20, .5), (500, 4700, 700, '#c04ad0', .18, .5), (1100, 2500, 450, '#3a5ae8', .2, .5), (200, 5300, 800, '#2ad8c0', .16, .5)]
def nebula(cv, cy, cx, Z, t, amt=1.0):
    for (x, alt, r, col, a, p) in NEB:
        sx = W / 2 + (x - cx * p * .3 - 640) * Z; sy = H / 2 + (-alt - cy * p) * Z
        if sy < -r * Z or sy > H + r * Z: continue
        cv.drawCircle(sx, sy, r * Z * (1 + .04 * math.sin(t * .3 + x)), paint(shader=rad(sx, sy, r * Z, [(col, a * amt), (col, a * .4 * amt), (col, 0)], [0, .5, 1]), blend='plus'))
