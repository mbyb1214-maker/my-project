import skia, math, json, os, numpy as np
from gfx import *
import bg, chars
from timeline import *

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
LIP = json.load(open(os.path.join(B, "lip.json")))
SUBS = {k: json.load(open(os.path.join(B, "meta.json")))[k]["text"] for k in LIP}
NAMES = {"mio": ("ミオ", "#ffc2d6"), "pom": ("ポム", "#9ff0ff"), "cub": ("こくじら", "#ffe9a0"), "mom": ("星くじらの母", "#d4c4ff")}

def speaking(t):
    """-> (speaker, mouth_open, line_id) of the line active at time t"""
    for k, d in LIP.items():
        if d["start"] - 0.02 <= t <= d["end"] + 0.05:
            i = int((t - d["start"]) * FPS)
            env = d["env"]; v = env[min(max(i, 0), len(env) - 1)]
            return d["spk"], clamp(v ** 0.8), k
    return None, 0.0, None

def kf(keys, t):
    """keys: [(t, *values)] smooth interpolation"""
    if t <= keys[0][0]: return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            u = easeinout((t - a[0]) / (b[0] - a[0]))
            return tuple(lerp(x, y, u) for x, y in zip(a[1:], b[1:]))
    return keys[-1][1:]

# ---------- ascent profile ----------
V = 520.0; T1 = T_LIFT + 3.6; T2 = 34.0; T3 = 38.6
def alt_g(t):
    if t <= T_LIFT: return 0.0
    if t <= T1:
        tau = t - T_LIFT; return V * tau * tau / (2 * (T1 - T_LIFT))
    a1 = V * (T1 - T_LIFT) / 2
    if t <= T2: return a1 + V * (t - T1)
    a2 = a1 + V * (T2 - T1)
    if t <= T3:
        tau = t - T2; return a2 + V * (tau - tau * tau / (2 * (T3 - T2)))
    return a2 + V * (T3 - T2) / 2
def vel_g(t):
    if t <= T_LIFT: return 0.0
    if t <= T1: return V * (t - T_LIFT) / (T1 - T_LIFT)
    if t <= T2: return V
    if t <= T3: return V * (1 - (t - T2) / (T3 - T2))
    return 0.0

MIO_X, MIO_Y = 470.0, 50.0
CUB_HEAD_X = 735.0
CUB_L, CUB_R = 130.0, 40.0

# ---------- actors' positions ----------
def pom_pos(t):
    """pom center position & mood params"""
    bob = math.sin(t * 1.7) * 6
    if t < T_LIFT - 2.0:
        keys = [(0, 590, -105), (9.5, 590, -105), (10.0, 650, -150), (11.0, 700, -135), (15.5, 700, -135), (16.4, 720, -190),
                (19.0, 720, -190), (20.0, 740, -175), (22.4, 740, -175), (23.2, 595, -240)]
        x, y = kf(keys, t)
        # landing jolt
        j = clamp((t - T_LAND) / 0.5)
        if 0 <= t - T_LAND < 0.5: x += 40 * math.sin(math.pi * j) * (1 - j); y -= 25 * math.sin(math.pi * j)
        return x, y + bob * (1 if t < 22.4 else 0.4)
    # climb: pom hovers above mio x
    gx = 590
    y0 = -240 - alt_g(t)
    if t > T3: y0 = -240 - alt_g(T3) - 8 * math.sin((t - T3) * 1.1)
    xs = gx + 22 * math.sin(t * 0.9) * sstep(T_LIFT + 2, T_LIFT + 5, t)
    return xs, y0 + (bob * 0.4 if t < T_LIFT else 3 * math.sin(t * 1.3))

def lift_k(t): return sstep(T_LIFT - 0.5, T_LIFT + 1.5, t)

def camera(t):
    if t < T_LIFT - 1.0:
        keys = [(0, 650, -125, 1.00), (3.5, 660, -150, 1.02), (7.8, 690, -265, 1.06), (9.4, 700, -200, 1.06),
                (9.8, 690, -150, 1.12),
                (12.4, 700, -110, 1.55), (13.8, 735, -85, 1.78), (16.2, 735, -85, 1.75),
                (16.9, 690, -150, 1.22), (18.6, 690, -150, 1.20),
                (19.4, 585, -110, 1.45), (22.0, 590, -118, 1.52),
                (22.9, 600, -125, 1.15), (23.7, 590, -125, 1.15)]
        return kf(keys, t)
    # follow the group
    px, py = pom_pos(t)
    fx = 590 + 0 * px
    cy_follow = py + 68
    ground_cy = -125
    k = sstep(T_LIFT - 0.8, T_LIFT + 2.6, t)
    cy = lerp(ground_cy, cy_follow, k)
    cx = lerp(590, px, k)
    Z = 1.0
    if t < T_LIFT: Z = 1.15 - 0.15 * sstep(T_LIFT - 1.0, T_LIFT + .6, t)
    # whale reveal / reunion / gift
    zk = [(T_LIFT + 0.6, 1.0), (T_AURORA, 1.0), (T_MOTHER + 0.3, 0.9), (T_MOTHER + 4.0, 0.66), (T_REUNION + 3.5, 0.72),
          (T_GIFT - 2.5, 0.72), (T_GIFT + 1.0, 1.05), (T_GIFT + 2.0, 1.15)]
    if t >= T_LIFT + .6:
        Z = zk[-1][1]
        for a, b in zip(zk, zk[1:]):
            if a[0] <= t <= b[0]: Z = lerp(a[1], b[1], easeinout((t - a[0]) / (b[0] - a[0]))); break
        else:
            if t < zk[0][0]: Z = zk[0][1]
        # drift the camera toward the whale for composition
        s = sstep(T_MOTHER, T_MOTHER + 4, t) * (1 - sstep(T_GIFT - 1.0, T_GIFT + 1.5, t))
        cx += -170 * s * 0 + 260 * s * (1 - 0) * 0.0
    # shake
    return cx, cy, Z

def ground_shake(t):
    d = t - T_LAND
    if 0 <= d < 0.9: return math.sin(d * 70) * 9 * math.exp(-d * 5), math.cos(d * 63) * 7 * math.exp(-d * 5)
    return 0, 0

# ---------- helper effects ----------
def meteor(cv, x0, y0, x1, y1, u, a=1.0, w=3.0):
    u = clamp(u)
    if u <= 0 or u >= 1.0: return
    hx, hy = lerp(x0, x1, u), lerp(y0, y1, u)
    tl = 0.22
    tx, ty = lerp(x0, x1, max(0, u - tl)), lerp(y0, y1, max(0, u - tl))
    fade = math.sin(math.pi * u) ** 0.6
    cv.drawLine(tx, ty, hx, hy, paint(shader=lin(tx, ty, hx, hy, [('#ffffff', 0), ('#cfe6ff', .9 * a * fade)]), stroke=w, blend='plus'))
    glow(cv, hx, hy, 14 * w / 3, '#ffffff', .8 * a * fade, .3)

def ring(cv, x, y, t0, t, col='#bfa8ff', sp=520, life=3.0, w=5, squash=0.6, a0=.55):
    d = t - t0
    if d < 0 or d > life: return
    r = d * sp; a = a0 * (1 - d / life) ** 1.5
    cv.drawOval(skia.Rect.MakeXYWH(x - r, y - r * squash, 2 * r, 2 * r * squash), paint(col, a, stroke=w * (1 + d), blend='plus'))

def burst(cv, x, y, t0, t, n=26, col='#ffffff', sp=380, life=1.4, seed=1, size=9):
    d = t - t0
    if d < 0 or d > life: return
    for i in range(n):
        ang = hnoise(i, seed) * 6.283; v = sp * (0.35 + 0.65 * hnoise(i, seed + 5))
        px = x + math.cos(ang) * v * d * (1 - 0.35 * d / life); py = y + math.sin(ang) * v * d * (1 - .35 * d / life) + 120 * d * d
        a = (1 - d / life) ** 1.2
        sparkle(cv, px, py, size * (0.5 + hnoise(i, seed + 9)) * (1 - d / life * .5), col, a, d * 3 + i)

def hologram(cv, x, y, t, k):
    """projection panel above Pom: a pod of star-whales, one missing"""
    if k <= 0.01: return
    w, h = 330 * easeout(k), 200 * easeout(k)
    cv.save(); cv.translate(x, y)
    # cone of light from pom's hand
    pth = skia.Path(); pth.moveTo(-14, 70); pth.lineTo(-w / 2, 0); pth.lineTo(w / 2, 0); pth.lineTo(14, 70); pth.close()
    cv.drawPath(pth, paint(shader=lin(0, 70, 0, 0, [('#7ae8ff', .35), ('#7ae8ff', .05)]), blend='plus'))
    r = skia.Rect.MakeXYWH(-w / 2, -h, w, h)
    cv.drawRoundRect(r, 14, 14, paint('#0e2a5a', .55 * k))
    cv.drawRoundRect(r, 14, 14, paint('#7ae8ff', .9 * k, stroke=3, blend='plus'))
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(r, 14, 14), skia.ClipOp.kIntersect, True)
    for i in range(0, int(h), 8): cv.drawLine(-w / 2, -h + i + (t * 20) % 8, w / 2, -h + i + (t * 20) % 8, paint('#7ae8ff', .10, stroke=1))
    # constellation of whales: a pod following the big leader, with a little lost one blinking
    pods = [(-110, -120, 46, '#ffb3d9'), (-30, -150, 54, '#9fffe0'), (60, -118, 50, '#ffe08a'), (120, -150, 42, '#b8c4ff'), (-70, -62, 40, '#ffb3d9')]
    for (px, py, L, col) in pods:
        pk = clamp(k * 1.5 - 0.3)
        chars.whale(cv, px + L * .5 + 6 * math.sin(t + px), py + 3 * math.sin(t * 1.3 + px), L, L * .3, t, flip=1, kind='icon', pal='pod4', glow_a=0.4, alpha=.85 * pk, speed=1.0, amp=.08)
    # the lost one (blinking, far from the pod)
    lost_x, lost_y = 118, -52
    blink = 0.4 + 0.6 * (math.sin(t * 7) > 0)
    cv.drawCircle(lost_x, lost_y, 15, paint('#ffe27a', .22 * blink, blend='plus'))
    chars.whale(cv, lost_x + 20, lost_y, 38, 11, t, flip=1, kind='icon', pal='cub', glow_a=.7, alpha=blink, speed=3.0)
    # dotted path from lost -> pod
    for i in range(10):
        u = i / 9; px = lerp(lost_x - 30, 20, u); py = lerp(lost_y, -118, u) - 16 * math.sin(u * math.pi)
        cv.drawCircle(px, py, 2.4, paint('#ffffff', (.9 if (int(t * 8) + i) % 4 else .25) * k))
    cv.restore(); cv.restore()

def title_card(cv, t):
    if t < T_TITLE: return
    u = t - T_TITLE
    a = sstep(0, 1.0, u) * (1 - sstep(2.5, 3.0, u))
    cv.drawRect(skia.Rect.MakeLTRB(0, 190, W, 520), paint(shader=lin(0, 190, 0, 520, [('#120a30', 0), ('#120a30', .62 * a), ('#120a30', .62 * a), ('#120a30', 0)], [0, .3, .7, 1])))
    glow(cv, 640, 330, 520, '#ffd987', .22 * a)
    for i in range(14):
        ang = i * 2.4 + u * .3; rr = 220 + 130 * hnoise(i, 3)
        sparkle(cv, 640 + math.cos(ang) * rr * 1.4, 330 + math.sin(ang * 1.3) * rr * .5, 8 + 8 * hnoise(i, 7), '#fff0b8', a * (.5 + .5 * math.sin(u * 3 + i)), u * 2 + i)
    text(cv, "星くじらの夜", 640, 350, 104, '#ffe9a8', a * .75, blur=14, blend='plus', spacing=14)
    text(cv, "星くじらの夜", 640, 350, 104, '#fffaf0', a, spacing=14)
    text(cv, "ほしくじらのよる", 640, 410, 30, '#ffe0c8', a * .9, spacing=10)
    text(cv, "おわり", 640, 470, 22, '#ffd6e0', a * .6 * sstep(1.2, 2.0, u), spacing=8)

def subtitle(cv, t):
    spk, _, k = speaking(t)
    if k is None: return
    d = LIP[k]; a = sstep(d["start"] - .02, d["start"] + .15, t) * (1 - sstep(d["end"] + .1, d["end"] + .35, t))
    name, col = NAMES[spk]; s = SUBS[k]
    f = skia.Font(FONT, 36); w = f.measureText(s)
    pad = 26; bx = 640 - w / 2 - pad; by = 628
    cv.drawRoundRect(skia.Rect.MakeXYWH(bx, by, w + pad * 2, 62), 31, 31, paint('#06081c', .55 * a))
    cv.drawRoundRect(skia.Rect.MakeXYWH(bx, by, w + pad * 2, 62), 31, 31, paint(col, .35 * a, stroke=1.5))
    text(cv, s, 640, by + 43, 36, '#ffffff', a)
    nf = skia.Font(FONT, 20); nw = nf.measureText(name)
    cv.drawRoundRect(skia.Rect.MakeXYWH(bx + 14, by - 14, nw + 28, 28), 14, 14, paint(col, a))
    text(cv, name, bx + 28, by + 6, 20, '#1a1038', a, align='left')

# ============================== NIGHT WORLD ==============================
def night_world(cv, t):
    cx, cy, Z = camera(t)
    sx_, sy_ = ground_shake(t)
    alt = -cy
    mode = 'night'
    bg.sky(cv, alt, mode)
    bg.stars(cv, cy, cx, Z, t, alt, mode)
    bg.nebula(cv, cy, cx, Z, t, sstep(1800, 3200, alt))
    bg.moon(cv, cy, cx, Z, t, mode)
    bg.aurora(cv, cy, cx, Z, t, sstep(T_SPACE, T_MOTHER + 1, t) * 0.9)
    bg.city(cv, cy, cx, Z, t, mode, sleep_t=t)
    bg.clouds(cv, cy, cx, Z, t, alt)
    cv.save(); cv.translate(sx_, sy_)
    # meteors
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(Z, Z); cv.translate(-cx, -cy)
    if T_SHOOT - .2 < t < T_FALL + .5 and t < T_LAND:
        for dt, (x0, y0, x1, y1) in ((0, (900, -520, 500, -300)), (0.9, (1150, -600, 820, -350)), (1.5, (400, -640, 80, -420))):
            meteor(cv, x0, y0 + 0, x1, y1, (t - T_SHOOT - dt) / 0.9)
    # the big star falls
    if T_FALL <= t < T_LAND:
        u = (t - T_FALL) / (T_LAND - T_FALL); u2 = u * u * (3 - 2 * u) * .4 + u * .6
        x0, y0, x1, y1 = 1150, -820, CUB_HEAD_X + 70, -30
        hx, hy = lerp(x0, x1, u2), lerp(y0, y1, u2)
        for i in range(40):
            uu = max(0, u2 - i * 0.012); px, py = lerp(x0, x1, uu), lerp(y0, y1, uu)
            glow(cv, px + 6 * math.sin(i * 1.7), py + 6 * math.cos(i), (30 - i * .6), '#ffe9a0' if i < 14 else '#b8a8ff', .55 * (1 - i / 40))
        glow(cv, hx, hy, 120, '#fff3c0', .9, .15)
        sparkle(cv, hx, hy, 55, '#ffffff', 1.0, t * 3)
    cv.restore()
    bg.roof(cv, cy, cx, Z, t, mode)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(Z, Z); cv.translate(-cx, -cy)
    actors(cv, t)
    cv.restore()
    bg.clouds(cv, cy, cx, Z, t, alt, front=True)
    cv.restore()
    # screen-space fx: speed lines + landing flash
    if T_LIFT + .5 < t < T3 + .5:
        v = vel_g(t) / V
        for i in range(34):
            x = (hnoise(i, 2) * W); ln = 90 + 260 * hnoise(i, 4)
            y = ((t * (700 + 900 * hnoise(i, 6)) * v + hnoise(i, 8) * 2000) % (H + 400)) - 200
            a = .22 * v * (0.4 + .6 * hnoise(i, 9))
            cv.drawLine(x, y, x, y + ln * v, paint('#cfe0ff', a, stroke=1.6 + 1.2 * hnoise(i, 10), blend='plus'))
    d = t - T_LAND
    if 0 <= d < 0.6: cv.drawRect(skia.Rect.MakeWH(W, H), paint('#fff6d8', .95 * (1 - d / .6) ** 2))
    if T_LAND - .25 < t < T_LAND: cv.drawRect(skia.Rect.MakeWH(W, H), paint('#fff6d8', ((t - (T_LAND - .25)) / .25) * .8))

def actors(cv, t):
    spk, mouth, lid = speaking(t)
    mio_m = mouth if spk == 'mio' else 0.0
    pom_m = mouth if spk == 'pom' else 0.0
    cub_m = mouth if spk == 'cub' else 0.0
    mom_m = mouth if spk == 'mom' else 0.0
    px, py = pom_pos(t)
    fly = lift_k(t) * (1 if t < T3 + 1.5 else 0.45)
    # ---------- mother whale & pod (behind everything in the sky) ----------
    gx, gy = px, py + 68
    if t >= T_MOTHER - 2.5:
        sky_whales(cv, t, px, py, mom_m)
    # ---------- cub ----------
    cub_pose(cv, t, px, py, cub_m)
    # ---------- mio ----------
    mio_pose(cv, t, px, py, mio_m)
    # ---------- pom ----------
    look = (0, 0); mood = 'calm'; point = 0.0
    if t < 5: look = (-1, .3)
    elif t < 7.5: look = (0, -1); point = easeout((t - 5.0) / .5) * (1 - sstep(7.2, 7.8, t))
    elif t < T_LAND: look = (.6, -.6)
    elif t < 16: look = (.5, .5); mood = 'surprise' if t < 12 else 'calm'
    elif t < 19: look = (0, -.2)
    elif t < 22: look = (-.8, .2)
    else: look = (0, -.5); mood = 'happy' if t > 24 else 'calm'
    if t > T_REUNION: mood = 'happy'
    if T_DAWN - 1 < t: mood = 'calm'
    if t >= T_LIFT: point = 0
    holo = hologram_k(t)
    pom_args = dict(look=look, mouth=pom_m, mood=mood, flying=fly, point=point)
    if holo > 0 or 16.4 < t < 19.2:
        pom_args['hold'] = 1.0
    chars.pom(cv, px, py, t, **pom_args)
    if holo > 0.01: hologram(cv, px + 135, py - 90, t, holo)
    # sparkle trail during flight
    if T_LIFT + .3 < t < T3 + 3:
        for k in range(46):
            age = k * 0.045; tb = t - age
            if tb < T_LIFT: continue
            ppx, ppy = pom_pos(tb)
            jx = (hnoise(k, int(tb * 7)) - .5) * 90; jy = 70 + age * 30
            a = (1 - age / 2.1) * 0.8 * min(1, (tb - T_LIFT) / 1.0) * (1 - sstep(T3 - .5, T3 + 2.5, t))
            if a > 0: sparkle(cv, ppx + jx, ppy + jy + 40, 5 + 6 * hnoise(k, 5), '#ffe9b0' if k % 2 else '#bfe8ff', a, k)

def hologram_k(t):
    return easeout((t - 16.55) / .5) * (1 - sstep(18.6, 19.0, t)) if 16.5 < t < 19.1 else 0.0

def cub_pose(cv, t, px, py, mouth):
    L, R = CUB_L, CUB_R
    lookup = (-.6, .3)
    if t < T_LAND + 0.2: return
    u = t - T_LAND
    pop = easeback(u / .9) if u < .9 else 1.0
    sling_k = sstep(22.0, 23.4, t)
    # roof position
    hx = CUB_HEAD_X; hy = MIO_Y - R * .95 + 6 * math.sin(t * 2.0) * (1 if t < 14 else .6)
    # sling position (on Mio's chest while flying)
    mx = px + 4; my = py + 290 - 96 * .8
    if t < 22.0:
        x, y = hx, hy; rot = 0.0; fl = -1
    elif t < T_REUNION:
        # arc into the blanket sling
        k = sling_k; arc = -90 * math.sin(math.pi * k)
        x = lerp(hx, mx + 24, easeinout(k)); y = lerp(hy, my, easeinout(k)) + arc
        rot = lerp(0, -24, k); fl = -1
    else:
        # swim to mother
        x, y, rot, fl = cub_swim(t, px, py, mx, my)
    sc = pop if t < T_LAND + 1.0 else 1.0
    if sc <= 0.01: return
    # shrink slightly when held
    held = (t >= 23.4 and t < T_REUNION)
    cv.save(); cv.translate(x, y); cv.scale(sc * (0.9 if held else 1.0), sc * (0.9 if held else 1.0))
    wiggle = 1.2 if t < 14 else 2.0
    look = (-.7, .1) if t < 22 else (0, -.7)
    happy = 1.0 if (t > T_REUNION + .4 or (24 < t < 27.5)) else 0.0
    mood_m = mouth
    if t < T_LAND + 1.2 and u > 0.2:  # sparkle burst halo
        glow(cv, 0, 0, 160 * (1 - u / 1.2), '#fff3c0', .7 * (1 - u / 1.2))
    if t < 22.0:  # resting glow on the deck
        cv.drawOval(skia.Rect.MakeXYWH(-L * .7, R * .85, L * 1.9, 24), paint('#7ae8ff', .22, blend='plus', blur=8))
    chars.whale(cv, 0, 0, L, R, t, flip=fl, look=look, mouth=mood_m, kind='cub', pal='cub', speed=wiggle if t < T_REUNION else 2.6, amp=.07 if t < 14 else .11, rot=rot, glow_a=.7, happy=happy)
    cv.restore()
    burst(cv, CUB_HEAD_X + 50, MIO_Y - R, T_LAND + .1, t, n=34, col='#fff1b0', sp=420, life=1.5, seed=3, size=11)

def cub_swim(t, px, py, mx, my):
    # cub leaves the sling, flies a loop, nuzzles mother's cheek near her eye
    mh = mother_head(t, px, py)
    ex, ey = mh[0] - 170, mh[1] + 10      # cheek target
    d = t - T_REUNION
    k = easeinout(clamp(d / 2.2))
    midx, midy = (mx + ex) / 2 - 20, min(my, ey) - 190
    x = (1 - k) ** 2 * (mx + 24) + 2 * (1 - k) * k * midx + k * k * ex
    y = (1 - k) ** 2 * my + 2 * (1 - k) * k * midy + k * k * ey
    rot = lerp(-24, 8, k) + 20 * math.sin(k * math.pi * 2) * (1 - k)
    x += 8 * math.sin(t * 2.6) * k; y += 8 * math.cos(t * 3) * k
    if d > 2.2:
        x = ex + 10 * math.sin(t * 1.5); y = ey + 10 * math.sin(t * 1.9)
        rot = 8 + 6 * math.sin(t * 2)
    return x, y, rot, 1

def mother_head(t, px, py):
    """head position of the mother whale in world coords"""
    gx, gy = px, py + 68
    slide = easeout((t - T_MOTHER + 2.5) / 6.0)
    hx = lerp(gx - 700, gx + 520, slide) + 6 * math.sin(t * .5)
    hy = gy + 70 + 10 * math.sin(t * .7)
    return hx, hy

def sky_whales(cv, t, px, py, mom_m):
    # pod of distant star whales
    pod = [(-640, -330, 330, 'pod1', .7), (-200, -520, 260, 'pod2', .6), (560, -420, 300, 'pod3', .75), (900, 90, 360, 'pod4', .7), (-820, 120, 280, 'pod2', .6), (180, 280, 240, 'pod1', .55), (1040, -250, 220, 'pod3', .5)]
    for i, (dx, dy, L, pal, a) in enumerate(pod):
        t0 = T_REUNION + 0.4 + i * 0.22
        k = clamp((t - t0) / 1.0)
        if k <= 0: continue
        # swim on a lazy loop around the group
        ph = t * 0.12 + i
        x = px + dx + 80 * math.sin(ph) + (t - t0) * 6; y = py + 68 + dy + 30 * math.cos(ph * 1.3)
        burst(cv, x, y, t0, t, n=14, col='#ffffff', sp=160, life=1.0, seed=i + 20, size=8)
        chars.whale(cv, x, y, L * easeout(k), L * .26 * easeout(k), t + i, flip=1 if i % 2 else -1, kind='pod', pal=pal, alpha=a * easeout(k), glow_a=.8, speed=.7, amp=.07, stars_tex=True)
    # mother
    mh = mother_head(t, px, py)
    k = sstep(T_MOTHER - 2.5, T_MOTHER, t)
    eye_blink = None
    if k > 0:
        # singing glow behind her
        glow(cv, mh[0] - 260, mh[1] - 40, 760, '#8f78ff', .22 * k)
        for tc in (T_MOTHER - .8, T_MOTHER + 3.0, T_REUNION - .3, T_GIFT - 1.0):
            ring(cv, mh[0] - 90, mh[1] - 30, tc, t, '#d6c8ff', 480, 3.2, 4)
        chars.whale(cv, mh[0], mh[1], 1700, 255, t, flip=1, look=(0, 0), mouth=mom_m, kind='mom', pal='mom', speed=.35, amp=.06, glow_a=.75, alpha=1.0)

def mio_pose(cv, t, px, py, mouth):
    # expression timeline
    mood = 'calm'; look = (0, 0); arm = 0.0
    if t < 1.0: mood = 'sad'; look = (.6, .4)
    elif t < 4.3: mood = 'sad'; look = (.4, .5)
    elif t < 5.4: mood = 'calm'; look = (.8, -.2)
    elif t < 8.0: mood = 'calm'; look = (.1, -1)
    elif t < T_LAND: mood = 'surprise'; look = (.7, -.5)
    elif t < 13.0: mood = 'surprise' if t < 12.6 else 'happy'; look = (.9, .4)
    elif t < 16.5: mood = 'tender'; look = (.9, .6)
    elif t < 19.3: mood = 'sad'; look = (0, -.2)
    elif t < 22.2: mood = 'determined'; look = (0, -.1)
    elif t < 24.2: mood = 'determined'; look = (0, -.6)
    elif t < 27: mood = 'surprise'; look = (0, -.2)
    elif t < 31.5: mood = 'happy'; look = (.2, -.3)
    elif t < 35: mood = 'happy'; look = (.2, -.5)
    elif t < 42.3: mood = 'surprise'; look = (.6, -.3)
    elif t < 50: mood = 'happy'; look = (.6, -.1)
    else: mood = 'surprise' if t < 51.5 else 'happy'; look = (.4, -.4)
    x, y = MIO_X, MIO_Y
    if t < T_LAND:
        sit = lerp(0, 1, 1)
        chars.mio(cv, x, y, 'sit', t, look=look, mouth=mouth, mood=mood)
        return
    # stand, then walk to the cub
    wk = easeinout((t - 11.0) / 2.2)
    x = lerp(MIO_X, 595.0, wk)
    step = 0
    if 11.0 < t < 13.2: y = MIO_Y - abs(math.sin((t - 11.0) * 9)) * 5
    sc = 1.0
    if t > 22.0: sc = lerp(1.0, 0.8, sstep(22.0, 22.9, t))
    reach = sstep(22.7, 23.7, t) if t < T_LIFT else 1.0
    if t < T_LIFT + .2:
        # Mio reaches up to Pom's feet and is lifted
        lift = lift_k(t)
        yy = y - 0
        gy = py + 290
        yy = lerp(y, gy, 0) if t < T_LIFT else gy
        if t < T_LIFT: yy = y
        chars.mio(cv, 595.0 if t > 13.2 else x, yy, 'stand', t, look=look, mouth=mouth, mood=mood, scale=sc, reach=reach, wind=0.3 * lift_k(t))
        return
    # hanging flight
    gx, gy = px, py + 251
    freearm = 0.0
    if t > 35.5: freearm = sstep(35.5, 38.5, t) * .4
    if t > T_GIFT - 1.8: freearm = max(freearm, sstep(T_GIFT - 1.8, T_GIFT + .2, t))
    if t > T_GIFT + 2.5: freearm = freearm
    wind = 0.5 if t < T3 else .2
    chars.mio(cv, gx, gy, 'hang', t, look=look, mouth=mouth, mood=mood, scale=0.8, wind=wind, freearm=freearm)
    # cub peeks out of the blanket sling
    # (cub drawn in cub_pose)
    # gift star
    if T_GIFT - 0.2 < t < T_DAWN + 0.4:
        u = clamp((t - T_GIFT) / 1.8)
        mh = mother_head(t, px, py)
        sx0, sy0 = mh[0] - 120, mh[1] - 110
        hand = (gx + 78 * .8, gy - 150 * .8 + 4)
        ee = easeinout(u)
        bx = (1 - ee) ** 2 * sx0 + 2 * (1 - ee) * ee * ((sx0 + hand[0]) / 2) + ee * ee * hand[0]
        by = (1 - ee) ** 2 * sy0 + 2 * (1 - ee) * ee * (min(sy0, hand[1]) - 150) + ee * ee * (hand[1] - 16)
        big = 1.0 + 3.2 * sstep(T_DAWN - 1.2, T_DAWN + .2, t)
        glow(cv, bx, by, 150 * big, '#ffe9a0', .65)
        sparkle(cv, bx, by, 46 * big * (0.8 + .2 * math.sin(t * 6)), '#fffbe8', 1.0, t * 1.5)
        burst(cv, sx0, sy0, T_GIFT - .2, t, n=22, col='#fff1b0', sp=260, life=1.6, seed=9, size=9)

# ============================== DAWN ==============================
def dawn_scene(cv, t):
    u = t - T_DAWN
    cx, cy, Z = 640 + 6 * u, -150 + 3 * u, 1.0 + 0.012 * u
    bg.sky(cv, 0, 'dawn')
    bg.stars(cv, cy, cx, Z, t, 0, 'dawn')
    # rising sun
    sx_ = W / 2 + (900 - cx - 640) * Z; sy_ = H / 2 + (-40 - cy) * Z - 8 * u
    glow(cv, sx_, sy_, 520, '#ffd9a0', .55 + .1 * math.sin(t))
    cv.drawCircle(sx_, sy_, 70, paint(shader=rad(sx_, sy_, 70, ['#fffbe8', '#ffe2a0', '#ffb48a'], [0, .6, 1])))
    bg.city(cv, cy, cx, Z, t, 'dawn')
    # pastel clouds
    for i in range(7):
        x = (hnoise(i, 31) * 1500 - 100 + 8 * t * (0.5 + hnoise(i, 2))) % 1500 - 100; y = 90 + 260 * hnoise(i, 33)
        for j in range(5):
            bx = x + j * 46 - 80; by = y + 12 * math.sin(j * 1.3)
            cv.drawOval(skia.Rect.MakeXYWH(bx, by, 150 - j * 14 if j < 3 else 90 + j * 4, 56), paint('#ffd8e0', .55))
    # tiny whale-shaped cloud waves goodbye
    wx = 1010 + 6 * math.sin(t * .5); wy = 200 + 8 * math.sin(t * .8)
    chars.whale(cv, wx, wy, 150, 40, t, flip=-1, kind='icon', pal='pod4', alpha=.65 * (0.5 + 0.5 * sstep(0, 2, u)), glow_a=.3, speed=1.1, amp=.08, fin=1.0)
    if 1.2 < u < 4.0:
        sparkle(cv, wx - 40, wy - 70, 18, '#ffffff', .9 * (0.5 + .5 * math.sin(u * 6)), u)
    bg.roof(cv, cy, cx, Z, t, 'dawn')
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(Z, Z); cv.translate(-cx, -cy)
    spk, mouth, lid = speaking(t)
    # Mio asleep, star in hands
    chars.mio(cv, 400, 56, 'sleep', t, mood='sleep', clip_glow=.5)
    br = math.sin(t * 1.3) * 2
    glow(cv, 470, 4 + br, 120, '#ffe9a0', .6 + .12 * math.sin(t * 2), .0)
    sparkle(cv, 470, 4 + br, 22 + 3 * math.sin(t * 3), '#fffbe8', 1.0, t)
    cv.drawCircle(470, 6 + br, 10, paint('#fff3c0', .95))
    for sgn in (-1, 1): cv.drawCircle(470 + sgn * 12, 10 + br, 8, paint(chars.SKIN))
    # Pom, powered down, hovering low, wakes briefly to say goodnight
    awake = sstep(T_DAWN + 1.0, T_DAWN + 1.5, t) * (1 - sstep(T_DAWN + 4.6, T_DAWN + 5.2, t))
    pm = mouth if spk == 'pom' else 0
    chars.pom(cv, 770, lerp(-4, -40, awake) + 3 * math.sin(t * 1.2), t, look=(-.8, .3), mouth=pm, mood='happy' if awake > .5 else 'calm',
              flying=0.0, eyes_closed=1.0 - awake, glow_lvl=lerp(0.35, 1.0, awake), scale=0.95)
    # little zzz
    for i in range(3):
        ph = (t * .5 + i * .33) % 1
        text(cv, "z", 440 + ph * 40 + i * 12, -90 - ph * 90, 26 + i * 6, '#ffffff', (1 - ph) * .8 * (1 - awake), align='left')
    cv.restore()
    # dawn light rays
    for i in range(7):
        a0 = -0.15 + i * 0.12
        pth = skia.Path(); pth.moveTo(sx_, sy_); pth.lineTo(sx_ - 900 * math.cos(a0 + .35) * 1.6, sy_ + 900 * math.sin(a0 + .35) * 1.2); pth.lineTo(sx_ - 900 * math.cos(a0 + .42) * 1.6, sy_ + 900 * math.sin(a0 + .42) * 1.2); pth.close()
        cv.drawPath(pth, paint('#ffe6b8', .06 + .03 * math.sin(t * .7 + i), blend='plus'))
    # whiteout transition from the gift star
    if u < 1.6:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint('#fffbe8', (1 - easeinout(u / 1.6)) * 1.0))
    # float motes
    for i in range(24):
        x = (hnoise(i, 41) * W + 14 * math.sin(t * .6 + i)) % W; y = (hnoise(i, 43) * H - t * 8 * (.4 + hnoise(i, 45))) % H
        cv.drawCircle(x, y, 1.6 + hnoise(i, 47) * 1.6, paint('#fff3d0', .5, blend='plus'))

# ============================== FRAME ==============================
VIG = None
def finish(cv, surface, t):
    # bloom
    img = surface.makeImageSnapshot()
    small = skia.Surface(W // 4, H // 4); sc = small.getCanvas()
    thr = skia.ColorFilters.Matrix([2.4, 0, 0, 0, -1.55, 0, 2.4, 0, 0, -1.55, 0, 0, 2.4, 0, -1.55, 0, 0, 0, 1, 0])
    p = skia.Paint(); p.setColorFilter(thr)
    sc.drawImageRect(img, skia.Rect.MakeWH(W // 4, H // 4), skia.SamplingOptions(skia.FilterMode.kLinear), p)
    s2 = skia.Surface(W // 4, H // 4); c2 = s2.getCanvas(); p2 = skia.Paint(); p2.setImageFilter(skia.ImageFilters.Blur(9, 9))
    c2.drawImage(small.makeImageSnapshot(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p2)
    bp = skia.Paint(); bp.setBlendMode(skia.BlendMode.kPlus); bp.setAlphaf(0.9)
    cv.drawImageRect(s2.makeImageSnapshot(), skia.Rect.MakeWH(W, H), skia.SamplingOptions(skia.FilterMode.kLinear), bp)
    # vignette
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=rad(W / 2, H / 2, 820, [('#000000', 0.0), ('#000000', 0.0), ('#02030f', .55)], [0, .55, 1])))

def render(f):
    t = f / FPS
    surface = skia.Surface(W, H); cv = surface.getCanvas()
    if t < T_DAWN: night_world(cv, t)
    else: dawn_scene(cv, t)
    finish(cv, surface, t)
    title_card(cv, t)
    subtitle(cv, t)
    # fades
    fa = 1 - sstep(0, 1.0, t)
    fb = sstep(DUR - 0.8, DUR, t)
    if fa > 0: cv.drawRect(skia.Rect.MakeWH(W, H), paint('#000000', fa))
    if fb > 0: cv.drawRect(skia.Rect.MakeWH(W, H), paint('#000000', fb))
    return surface

def frame_array(f):
    s = render(f)
    return s.makeImageSnapshot().toarray()
