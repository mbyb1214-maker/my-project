import skia, math, numpy as np
from gfx import *

SKIN, SKIN_SH, BLUSH = '#ffe0c8', '#f3b9a2', '#ff9aa8'
HAIR, HAIR_HI = '#2d2350', '#6a5aa8'

# ============================ MIO ============================
def mio_head(cv, r, look=(0, 0), mouth=0.0, blink=0.0, mood='calm', tilt=0.0, t=0.0, sway=0.0, clip_glow=1.0):
    """head centred at (0,0). blink 0=open 1=closed"""
    cv.save(); cv.rotate(tilt)
    # back hair (bob)
    back = poly_smooth([(-r * 1.2, -r * .2), (-r * 1.08, -r * .95), (0, -r * 1.3), (r * 1.08, -r * .95), (r * 1.2, -r * .2),
                        (r * 1.2 + sway * .4, r * .62), (r * 1.02 + sway, r * 1.02), (r * .62 + sway, r * .98), (-r * .62 + sway, r * .98), (-r * 1.02 + sway, r * 1.02), (-r * 1.2 + sway * .4, r * .62)])
    cv.drawPath(back, paint(shader=lin(0, -r * 1.3, 0, r * 1.1, [HAIR_HI, HAIR, '#241b42'], [0, .35, 1])))
    # ahoge (antenna hair)
    sw = math.sin(t * 2.2) * 6 + sway * 3
    ah = skia.Path(); ah.moveTo(-r * .05, -r * 1.12); ah.cubicTo(-r * .2, -r * 1.55, r * .35 + sw, -r * 1.55, r * .2 + sw, -r * 1.85)
    cv.drawPath(ah, paint(HAIR, stroke=r * .1))
    # face
    cv.drawOval(skia.Rect.MakeXYWH(-r, -r * .93, r * 2, r * 1.9), paint(shader=lin(0, -r, 0, r, [SKIN, '#ffd0b8'])))
    # ears hint
    # eyes
    ex = r * .40; ey = r * .12
    open_ = 1 - clamp(blink)
    for sgn in (-1, 1):
        cx = sgn * ex + look[0] * r * .05; cy = ey + look[1] * r * .04
        if mood == 'happy' or mood == 'sleep' or open_ < 0.18:
            a = skia.Path(); 
            if mood == 'sleep':
                a.moveTo(cx - r * .17, cy); a.quadTo(cx, cy + r * .13, cx + r * .17, cy)
            else:
                a.moveTo(cx - r * .17, cy + r * .04); a.quadTo(cx, cy - r * .20, cx + r * .17, cy + r * .04)
            cv.drawPath(a, paint('#2a1a3a', stroke=r * .075))
        else:
            big = 1.18 if mood == 'surprise' else 1.0
            rx, ry = r * .175 * big, r * .245 * big * (0.3 + 0.7 * open_)
            cv.drawOval(skia.Rect.MakeXYWH(cx - rx, cy - ry, rx * 2, ry * 2), paint('#ffffff'))
            irx = rx * (0.72 if mood == 'surprise' else 0.92); iry = ry * (0.78 if mood == 'surprise' else 0.95)
            ix = cx + look[0] * rx * .22; iy = cy + look[1] * ry * .18
            cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cx - rx, cy - ry, rx * 2, ry * 2)); 
            cv.drawOval(skia.Rect.MakeXYWH(ix - irx, iy - iry, irx * 2, iry * 2), paint(shader=lin(0, iy - iry, 0, iy + iry, ['#3a2a70', '#6a4ad0', '#46d6e0'], [0, .55, 1])))
            cv.drawCircle(ix, iy + iry * .05, irx * .5, paint('#1a1030'))
            cv.restore()
            cv.drawCircle(ix - irx * .35, iy - iry * .38, irx * .3, paint('#ffffff'))
            cv.drawCircle(ix + irx * .3, iy + iry * .35, irx * .14, paint('#ffffff', .9))
            # upper lid / lash
            lid = skia.Path(); lid.moveTo(cx - rx * 1.05, cy - ry * .2); lid.quadTo(cx, cy - ry * 1.28, cx + rx * 1.05, cy - ry * .2)
            cv.drawPath(lid, paint('#2a1a3a', stroke=r * .07))
            if mood == 'tear':
                pass
        # brows
        by = ey - r * .34 + (0 if mood != 'surprise' else -r * .07)
        tiltb = {'sad': -1, 'determined': 1, 'tender': -.6}.get(mood, 0)
        bp = skia.Path(); bp.moveTo(cx - r * .14, by + tiltb * sgn * -r * .05); bp.lineTo(cx + r * .14, by + tiltb * sgn * r * .05)
        if tiltb: cv.drawPath(bp, paint('#3a2850', stroke=r * .05))
        else:
            bq = skia.Path(); bq.moveTo(cx - r * .13, by + r * .02); bq.quadTo(cx, by - r * .05, cx + r * .13, by + r * .02)
            cv.drawPath(bq, paint('#3a2850', .8, stroke=r * .04))
    # blush
    for sgn in (-1, 1): cv.drawOval(skia.Rect.MakeXYWH(sgn * r * .6 - r * .17, r * .36, r * .34, r * .16), paint(BLUSH, .55))
    # mouth
    my = r * .56
    if mouth > 0.08:
        mw = r * (.09 + .07 * mouth); mh = r * (.03 + .17 * mouth)
        cv.drawOval(skia.Rect.MakeXYWH(-mw, my - mh * .4, mw * 2, mh * 1.6), paint('#8a2c46'))
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(-mw, my + mh * .3, mw * 2, mh))
        cv.drawOval(skia.Rect.MakeXYWH(-mw * .65, my + mh * .45, mw * 1.3, mh * .9), paint('#ff8aa0')); cv.restore()
    else:
        m = skia.Path()
        if mood in ('sad', 'tender'):
            m.moveTo(-r * .09, my + r * .03); m.quadTo(0, my - r * .03, r * .09, my + r * .03)
        elif mood == 'determined':
            m.moveTo(-r * .09, my); m.lineTo(r * .09, my)
        else:
            m.moveTo(-r * .11, my - r * .01); m.quadTo(0, my + r * .1, r * .11, my - r * .01)
        cv.drawPath(m, paint('#8a3050', stroke=r * .05))
    # fringe
    fr = poly_smooth([(-r * 1.12, -r * .05), (-r * 1.08, -r * .85), (0, -r * 1.22), (r * 1.08, -r * .85), (r * 1.12, -r * .05),
                      (r * .9, r * .22), (r * .72, -r * .22), (r * .42, r * .08), (r * .18, -r * .36), (-r * .1, r * .02),
                      (-r * .38, -r * .3), (-r * .62, r * .12), (-r * .85, -r * .22), (-r * .92, r * .3)])
    cv.drawPath(fr, paint(shader=lin(0, -r * 1.3, 0, r * .3, [HAIR_HI, HAIR], [0, .7])))
    hl = skia.Path(); hl.moveTo(-r * .6, -r * .95); hl.quadTo(-r * .1, -r * 1.15, r * .45, -r * 1.0)
    cv.drawPath(hl, paint('#ffffff', .22, stroke=r * .09))
    # side locks
    for sgn in (-1, 1):
        sl = poly_smooth([(sgn * r * .95, -r * .1), (sgn * r * 1.14, r * .35), (sgn * r * 1.02 + sway, r * 1.0), (sgn * r * .86, r * .5)])
        cv.drawPath(sl, paint(HAIR))
    # star clip
    glow(cv, r * .82, -r * .62, r * .55, '#ffe27a', .55 * clip_glow, .0)
    sparkle(cv, r * .82, -r * .62, r * .23, '#ffe9a0', 1.0, 0.3)
    cv.restore()

def mio_body(cv, pose, t, wind=0.0, arm=0.0, step=0.0, grip=False, reach=0.0, freearm=0.0):
    """feet origin at (0,0). returns head position (x,y)."""
    PJ, PJ2, BL, BL2 = '#fff0c4', '#ffd24d', '#c9406f', '#ee7fa3'
    if pose == 'sit':
        bob = math.sin(t * 1.6) * 1.5
        # legs / knees pulled up
        cv.drawOval(skia.Rect.MakeXYWH(-62, -70, 130, 78), paint('#a9c8ff'))
        for sx in (-30, 18): cv.drawOval(skia.Rect.MakeXYWH(sx, -8, 40, 20), paint('#ffd1dc'))
        # blanket burrito
        b = poly_smooth([(-78, 0), (-82, -60), (-60, -118 + bob), (0, -138 + bob), (62, -118 + bob), (86, -60), (82, 0), (0, 10)])
        cv.drawPath(b, paint(shader=lin(0, -140, 0, 10, [BL2, BL, '#b83a66'], [0, .4, 1])))
        for i in range(9):
            cv.drawCircle(-55 + i * 14 + (i % 2) * 6, -90 + (i * 37) % 60, 3.2, paint('#ffd8e4', .7))
        fold = skia.Path(); fold.moveTo(-70, -92); fold.quadTo(0, -62 + bob, 72, -96)
        cv.drawPath(fold, paint('#ffffff', .25, stroke=6))
        # hands grip blanket
        for sx in (-34, 34): cv.drawCircle(sx, -100 + bob, 11, paint(SKIN))
        return (0, -168 + bob)
    if pose == 'stand':
        sw = math.sin(t * 2) * 2
        # cape (behind)
        cape = poly_smooth([(-30, -118), (-70 - wind * 30, -80), (-90 - wind * 55, -20 + sw), (-60 - wind * 40, 8), (-20, -20), (24, -118)])
        cv.drawPath(cape, paint(shader=lin(-90, -120, 0, 0, [BL2, BL])))
        # legs
        for sx in (-14, 14):
            limb(cv, [(sx, -62), (sx + step * sx * .02, -30), (sx, -8)], 15, '#a9c8ff')
            cv.drawOval(skia.Rect.MakeXYWH(sx - 18, -14, 36, 17), paint('#ffd1dc'))
        # torso
        tor = poly_smooth([(-30, -126), (-38, -66), (-30, -56), (30, -56), (38, -66), (30, -126), (0, -134)])
        cv.drawPath(tor, paint(shader=lin(0, -134, 0, -56, [PJ, '#ffe6a0'])))
        for (px, py) in ((-14, -102), (12, -86), (-6, -70), (18, -112)): sparkle(cv, px, py, 5, PJ2, .95, 0)
        # collar blanket wrap
        cv.drawOval(skia.Rect.MakeXYWH(-38, -134, 76, 22), paint(BL2))
        # arms
        a = arm
        for sgn in (-1, 1):
            if reach > 0.01:
                gx_, gy_ = sgn * 12, lerp(-66, -272, reach)
                limb(cv, [(sgn * 30, -118), (sgn * lerp(44, 26, reach), lerp(-92, -190, reach)), (gx_, gy_)], 13, PJ)
                cv.drawCircle(gx_, gy_ - 3, 9, paint(SKIN))
            elif sgn == 1 and a > 0.01:  # raised arm
                limb(cv, [(30, -118), (46 + 10 * a, -150 * (0.7 + a * .5) + 20), (40 + 30 * a, -126 - 120 * a)], 13, PJ)
                cv.drawCircle(40 + 30 * a, -126 - 120 * a, 9, paint(SKIN))
            else:
                limb(cv, [(sgn * 30, -118), (sgn * 44, -92), (sgn * 38 + (6 if grip else 0), -66)], 13, PJ)
                cv.drawCircle(sgn * 38 + (6 if grip else 0), -64, 9, paint(SKIN))
        return (0, -168)
    if pose == 'hang':
        sw = math.sin(t * 2.0) * 6
        # blanket flapping behind
        fl = math.sin(t * 9) * 10
        cape = poly_smooth([(-18, -120), (-60 + fl, -30 + 60), (-96 + fl * 1.5, 40), (-70, 70 + fl), (-10, 30), (20, -118)])
        cv.save(); cv.rotate(sw * .6)
        cv.drawPath(cape, paint(shader=lin(-90, -100, 0, 60, [BL2, BL])))
        # legs dangling
        for sx, ph in ((-14, 0), (14, 1.3)):
            limb(cv, [(sx, -60), (sx + math.sin(t * 5 + ph) * 8, -20), (sx + math.sin(t * 5 + ph) * 14 + 4, 22)], 15, '#a9c8ff')
            cv.drawOval(skia.Rect.MakeXYWH(sx + math.sin(t * 5 + ph) * 14 - 14, 18, 34, 16), paint('#ffd1dc'))
        tor = poly_smooth([(-30, -126), (-36, -66), (-28, -56), (28, -56), (36, -66), (30, -126), (0, -134)])
        cv.drawPath(tor, paint(shader=lin(0, -134, 0, -56, [PJ, '#ffe6a0'])))
        # arms: left grips Pom, right is free (freearm 0 = grips too, 1 = reaching out, cupped)
        limb(cv, [(-30, -118), (-24, -190), (-10, -272)], 13, PJ); cv.drawCircle(-10, -275, 9, paint(SKIN))
        gxr, gyr = lerp(10, 78, freearm), lerp(-272, -150 + 10 * math.sin(t * 3), freearm)
        limb(cv, [(30, -118), (lerp(24, 60, freearm), lerp(-190, -128, freearm)), (gxr, gyr)], 13, PJ); cv.drawCircle(gxr, gyr - (3 if freearm < .5 else -2), 9, paint(SKIN))
        cv.restore()
        return (0, -166)
    if pose == 'sleep':
        br = math.sin(t * 1.3) * 2
        cv.drawOval(skia.Rect.MakeXYWH(-90, -22, 150, 44), paint('#fff4e0'))
        cv.drawOval(skia.Rect.MakeXYWH(-90, -22, 150, 44), paint('#d9b8a8', .5, stroke=2))
        cv.drawOval(skia.Rect.MakeXYWH(26, -64 + br, 250, 78), paint(shader=lin(0, -64, 0, 14, ['#ff9fbd', '#ee7fa3', '#c9406f'], [0, .45, 1])))
        hl = skia.Path(); hl.moveTo(50, -50 + br); hl.quadTo(150, -66 + br, 250, -46 + br)
        cv.drawPath(hl, paint('#ffffff', .35, stroke=5))
        for i in range(10): cv.drawCircle(52 + i * 21, -36 + (i * 13) % 30 + br, 3.2, paint('#ffd8e4', .75))
        cv.drawOval(skia.Rect.MakeXYWH(250, -30, 34, 18), paint('#ffd1dc'))
        return (-14, -44)

def mio(cv, x, y, pose, t, look=(0, 0), mouth=0, mood='calm', blink=None, flip=1, wind=0, arm=0, grip=False, tilt=0, scale=1.0, clip_glow=1.0, reach=0.0, freearm=0.0, under=None):
    cv.save(); cv.translate(x, y); cv.scale(scale * flip, scale)
    if blink is None:
        ph = (t * 0.62) % 3.1
        blink = 1.0 if ph > 3.0 else 0.0
    hx, hy = mio_body(cv, pose, t, wind, arm, grip=grip, reach=reach, freearm=freearm)
    cv.save(); cv.translate(hx, hy)
    sway = math.sin(t * 1.9) * 3 + wind * 10
    if pose == 'sleep':
        cv.rotate(-8)
        mio_head(cv, 52, (0, 0), 0, 1, 'sleep', 0, t, 0, clip_glow)
    else:
        mio_head(cv, 52, look, mouth, blink, mood, tilt, t, sway, clip_glow)
    cv.restore()
    cv.restore()

# ============================ POM ============================
def pom(cv, x, y, t, look=(0, 0), mouth=0, mood='calm', flying=0.0, point=0.0, scale=1.0, eyes_closed=0.0, glow_lvl=1.0, tiltd=0.0, hold=0.0):
    cv.save(); cv.translate(x, y); cv.scale(scale, scale); cv.rotate(tiltd)
    R = 60
    belly_pulse = 0.75 + 0.25 * math.sin(t * 3.2)
    # thruster flames
    if flying > 0.01:
        for sx in (-24, 24):
            fl = 0.7 + 0.3 * math.sin(t * 40 + sx)
            L = (22 + 26 * flying) * fl
            p = skia.Path(); p.moveTo(sx - 9, R - 2); p.quadTo(sx, R + L, sx + 9, R - 2); p.close()
            cv.drawPath(p, paint(shader=lin(0, R, 0, R + L, [('#fff8d0', 0.95), ('#ffb04a', .8), ('#ff5a2a', 0.0)], [0, .45, 1]), blend='plus'))
            glow(cv, sx, R + 14, 36 * flying, '#ffb060', .5 * flying)
    # feet
    for sx in (-24, 24): cv.drawRoundRect(skia.Rect.MakeXYWH(sx - 11, R - 8, 22, 18), 6, 6, paint('#6a7aa8'))
    # arms
    for sgn in (-1, 1):
        if sgn == 1 and point > 0.01:
            ang = -70 * point
            cv.save(); cv.translate(R - 4, 4); cv.rotate(ang)
            limb(cv, [(0, 0), (22, -4), (40, -2)], 11, '#e8ecff'); cv.drawCircle(42, -2, 8, paint('#ffd88a')); cv.restore()
        elif hold > 0.01:
            limb(cv, [(sgn * (R - 4), 6), (sgn * (R + 14), 10 + 4 * math.sin(t * 7)), (sgn * (R + 24), 24)], 11, '#e8ecff'); cv.drawCircle(sgn * (R + 24), 26, 8, paint('#ffd88a'))
        else:
            wv = math.sin(t * 2.3 + sgn) * 4 + (6 if flying else 0)
            limb(cv, [(sgn * (R - 6), 8), (sgn * (R + 14), 18 + wv), (sgn * (R + 22), 36 + wv * .6)], 11, '#e8ecff'); cv.drawCircle(sgn * (R + 22), 38 + wv * .6, 8, paint('#ffd88a'))
    # handle + mast + propeller
    hp = skia.Path(); hp.moveTo(-26, -R + 14); hp.cubicTo(-30, -R - 48, 30, -R - 48, 26, -R + 14)
    cv.drawPath(hp, paint('#8f9bc8', stroke=7))
    cv.drawRect(skia.Rect.MakeXYWH(-3, -R - 50, 6, 18), paint('#8f9bc8'))
    # antenna bulb
    cv.drawLine(-26 + 6, -R + 6, -40, -R - 22, paint('#8f9bc8', stroke=4))
    glow(cv, -40, -R - 26, 22, '#7ae8ff', .6 + .3 * math.sin(t * 4))
    cv.drawCircle(-40, -R - 26, 6, paint('#d8fbff'))
    # body
    cv.drawCircle(0, 0, R + 12, paint('#8fb6ff', 0.0))
    glow(cv, 0, 4, R * 1.9, '#ffcf8a', 0.20 * glow_lvl)
    cv.drawCircle(0, 0, R, paint(shader=rad(-R * .35, -R * .4, R * 1.5, ['#ffffff', '#e3e9ff', '#9aa8d8'], [0, .5, 1])))
    cv.drawCircle(0, 0, R, paint('#5b6aa8', .6, stroke=3))
    # panel line + rivets
    cv.drawArc(skia.Rect.MakeXYWH(-R + 6, -R + 6, 2 * R - 12, 2 * R - 12), 20, 140, False, paint('#7f8fc8', .5, stroke=2))
    for ang in (200, 340): cv.drawCircle(math.cos(math.radians(ang)) * (R - 8), math.sin(math.radians(ang)) * (R - 8), 2.6, paint('#8f9bc8'))
    # face screen
    cv.drawRoundRect(skia.Rect.MakeXYWH(-40, -34, 80, 46), 20, 20, paint('#151a4a'))
    cv.drawRoundRect(skia.Rect.MakeXYWH(-40, -34, 80, 46), 20, 20, paint('#7ae8ff', .35, stroke=2))
    ec = clamp(eyes_closed) if eyes_closed else 0
    bl = 1.0 if (t * 0.5) % 2.7 > 2.62 else 0.0
    op = 1 - max(ec, bl)
    for sgn in (-1, 1):
        ex = sgn * 17 + look[0] * 3; ey = -15 + look[1] * 2
        if mood == 'happy' or op < 0.2:
            a = skia.Path(); a.moveTo(ex - 8, ey + 3); a.quadTo(ex, ey - 8 if mood == 'happy' else ey + 4, ex + 8, ey + 3)
            cv.drawPath(a, paint('#7ae8ff', stroke=3.5)); glow(cv, ex, ey, 14, '#7ae8ff', .4)
        else:
            h = (11 if mood != 'surprise' else 14) * op
            cv.drawOval(skia.Rect.MakeXYWH(ex - 6.5, ey - h, 13, h * 2), paint('#c8fbff'))
            glow(cv, ex, ey, 16, '#7ae8ff', .45)
            cv.drawCircle(ex - 2, ey - h * .4, 2.3, paint('#ffffff'))
    for sgn in (-1, 1): cv.drawCircle(sgn * 30, -2, 5, paint('#ff9ec2', .55))
    my = -2
    if mouth > .08:
        cv.drawRoundRect(skia.Rect.MakeXYWH(-8, my - 1, 16, 3 + 11 * mouth), 4, 4, paint('#7ae8ff'))
    else:
        m = skia.Path(); m.moveTo(-8, my); m.quadTo(0, my + (7 if mood != 'sad' else -2), 8, my)
        cv.drawPath(m, paint('#7ae8ff', stroke=3))
    # belly window with star core
    cv.drawCircle(0, 38, 19, paint('#3a2a58'))
    cv.drawCircle(0, 38, 17, paint(shader=rad(0, 38, 18, [('#fffbe0', 1), ('#ffcf6a', 1), ('#ff9a3a', .9)], [0, .5, 1])))
    glow(cv, 0, 38, 46 * glow_lvl, '#ffcf6a', .55 * belly_pulse * glow_lvl)
    sparkle(cv, 0, 38, 11 * belly_pulse, '#ffffff', .9, t * .6)
    cv.drawCircle(0, 38, 19, paint('#8f9bc8', stroke=3))
    # propeller (on top of mast)
    py = -R - 54
    spin = t * 30
    if flying > 0.02:
        cv.drawOval(skia.Rect.MakeXYWH(-82, py - 7, 164, 14), paint('#9ff3ff', 0.18 + 0.2 * flying))
        for k in range(3):
            w = 74 * abs(math.cos(spin + k * 1.05))
            cv.drawOval(skia.Rect.MakeXYWH(-w, py - 3, 2 * w, 6), paint('#e0fbff', .25))
        glow(cv, 0, py, 70, '#7ae8ff', .25 * flying)
    else:
        w = 62 * math.cos(t * 1.2 + 0.4) if point == 0 else 62
        cv.drawOval(skia.Rect.MakeXYWH(-abs(w), py - 3.5, 2 * abs(w), 7), paint('#7ae8ff', .9))
        cv.drawOval(skia.Rect.MakeXYWH(-abs(w) * .6, py - 2, 1.2 * abs(w), 4), paint('#ffffff', .6))
    cv.drawCircle(0, py, 6, paint('#d6deff'))
    cv.restore()

# ============================ WHALE ============================
def _profile(u, R):
    if u < 0.2:
        v = 1 - ((0.2 - u) / 0.2) ** 2
        return R * math.sqrt(max(v, 0))
    return R * (0.10 + 0.90 * (1 - ((u - 0.2) / 0.8) ** 1.35))

_rs = np.random.default_rng(4)
FRECK = [(float(_rs.uniform(0.04, 0.85)), float(_rs.uniform(-0.8, 0.5)), float(_rs.uniform(0.6, 1.6))) for _ in range(46)]

def whale(cv, x, y, L, R, t, flip=1, look=(0, 0), mouth=0.0, blink=None, kind='cub', pal='cub', speed=1.6, amp=0.10, rot=0.0, alpha=1.0, glow_a=0.6, happy=0.0, stars_tex=False, fin=0.0, wave_ph=0.0):
    PAL = {'cub': ('#6fe0ff', '#b49bff', '#fff0fb', '#7ae8ff'), 'mom': ('#1b2c8a', '#5a3fc0', '#c8b8ff', '#9d8cff'),
           'pod1': ('#ffb3d9', '#b88cff', '#fff0fb', '#ffb3d9'), 'pod2': ('#9fffe0', '#6fb0ff', '#f0fff8', '#9fffe0'),
           'pod3': ('#ffe08a', '#ff9ac0', '#fff6e0', '#ffe08a'), 'pod4': ('#b8c4ff', '#8f7cff', '#f0f0ff', '#b8c4ff')}[pal]
    cv.save(); cv.translate(x, y); cv.scale(flip, 1); cv.rotate(rot)
    N = 56
    top, bot = [], []
    cen = []
    for i in range(N + 1):
        u = i / N; r = _profile(u, R)
        yo = amp * L * (u ** 1.5) * math.sin(2 * math.pi * (speed * t) - 3.4 * u + wave_ph)
        xo = -u * L
        cen.append((xo, yo, r))
        top.append((xo, yo - r)); bot.append((xo, yo + r * 0.92))
    # tail fluke at end
    ex, ey, _ = cen[-1]; px, py, _ = cen[-3]
    ang = math.atan2(ey - py, ex - px)
    fl = L * 0.2
    cv.save(); cv.translate(ex, ey); cv.rotate(math.degrees(ang) + 0)
    for sgn in (-1, 1):
        p = skia.Path(); p.moveTo(-fl * .05, 0); p.cubicTo(fl * .35, sgn * fl * .15, fl * .75, sgn * fl * 1.0, fl * 1.1, sgn * fl * .85)
        p.cubicTo(fl * .9, sgn * fl * .4, fl * .75, sgn * fl * .15, fl * .45, 0); p.close()
        if glow_a > 0: cv.drawPath(p, paint(PAL[3], glow_a * .5 * alpha, blur=8))
        cv.drawPath(p, paint(shader=lin(0, 0, fl, sgn * fl, [PAL[1], PAL[0]]), a=alpha))
    cv.restore()
    # pectoral fin (behind body)
    fx, fy, fr_ = cen[int(N * 0.30)]
    fa = math.sin(t * 3 + 1) * 18 + 24 + fin * -50
    cv.save(); cv.translate(fx, fy + fr_ * .55); cv.rotate(fa)
    fp = skia.Path(); fp.moveTo(0, 0); fp.cubicTo(-R * .2, R * .5, -R * .55, R * .8, -R * .8, R * .75); fp.cubicTo(-R * .6, R * .35, -R * .35, R * .05, 0, -R * .12); fp.close()
    cv.drawPath(fp, paint(shader=lin(0, 0, -R, R, [PAL[1], PAL[0]]), a=alpha))
    cv.restore()
    path = poly_smooth(top + list(reversed(bot[1:-1])))
    if glow_a > 0:
        cv.drawPath(path, paint(PAL[3], glow_a * .55 * alpha, blur=R * .22 + 6, blend='plus'))
    cv.drawPath(path, paint(shader=lin(0, cen[2][1] - R, 0, cen[2][1] + R, [PAL[0], PAL[1], PAL[2]], [0, .62, 1]), a=alpha))
    # texture
    cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
    # belly pleats
    for k in range(0, 14 if kind == 'mom' else 7):
        xs = -L * (0.08 + k * (0.5 / (14 if kind == 'mom' else 7)))
        pp = skia.Path(); u = -xs / L; yo = amp * L * (u ** 1.5) * math.sin(2 * math.pi * (speed * t) - 3.4 * u + wave_ph); r_ = _profile(u, R)
        pp.moveTo(xs, yo + r_ * .45); pp.lineTo(xs - R * .06, yo + r_ * .98)
        cv.drawPath(pp, paint('#ffffff', .30 * alpha, stroke=2))
    if kind == 'cub' or stars_tex:
        for (fu, fv, fs) in FRECK:
            u = fu; r_ = _profile(u, R); yo = amp * L * (u ** 1.5) * math.sin(2 * math.pi * (speed * t) - 3.4 * u + wave_ph)
            sx = -u * L; sy = yo + fv * r_
            tw = .55 + .45 * math.sin(t * 3 + fu * 40)
            cv.drawCircle(sx, sy, fs * (R / 60 + .4), paint('#ffffff', .65 * tw * alpha))
    if kind == 'mom':
        pts = []
        for (fu, fv, fs) in FRECK:
            u = fu * 1.1; r_ = _profile(min(u, .98), R); yo = amp * L * (u ** 1.5) * math.sin(2 * math.pi * (speed * t) - 3.4 * u + wave_ph)
            pts.append((-u * L, yo + fv * r_ * .85, fs))
        for i, (a_x, a_y, s_) in enumerate(pts):
            for j in range(i + 1, min(i + 4, len(pts))):
                b_x, b_y, _ = pts[j]
                if (a_x - b_x) ** 2 + (a_y - b_y) ** 2 < (R * 1.5) ** 2: cv.drawLine(a_x, a_y, b_x, b_y, paint('#cfe0ff', .35 * alpha, stroke=1.6))
        for i, (a_x, a_y, s_) in enumerate(pts):
            tw = .5 + .5 * math.sin(t * 2.4 + i)
            glow(cv, a_x, a_y, 12 * s_ * (R / 150 + .5), '#ffffff', .6 * tw * alpha, .2)
    cv.restore()
    cv.drawPath(path, paint('#ffffff', .30 * alpha, stroke=2.5))
    # face
    if kind in ('cub', 'mom'):
        eu = 0.15; ex_, ey_, er = cen[int(N * eu)]
        eyx, eyy = ex_ + look[0] * R * .03, ey_ - R * .14 + look[1] * R * .03
        er_ = R * (.20 if kind == 'cub' else .12)
        if blink is None: blink = 1.0 if (t * 0.55 + (0.3 if kind == 'mom' else 0)) % 3.3 > 3.2 else 0.0
        if kind == 'mom' or happy > 0.5 or blink > 0.5:
            ee = skia.Path()
            if happy > .5 or kind == 'mom' and blink < .5:
                ee.moveTo(eyx - er_ * 1.2, eyy + er_ * .3); ee.quadTo(eyx, eyy - er_ * 1.5, eyx + er_ * 1.2, eyy + er_ * .3)
            else:
                ee.moveTo(eyx - er_ * 1.2, eyy); ee.quadTo(eyx, eyy + er_ * .8, eyx + er_ * 1.2, eyy)
            cv.drawPath(ee, paint('#14103a', stroke=max(3, er_ * .5)))
            if kind == 'mom':   # gentle glowing iris peek
                glow(cv, eyx, eyy + er_ * .1, er_ * 3, '#ffe9a8', .35)
        else:
            cv.drawCircle(eyx, eyy, er_, paint('#14103a'))
            cv.drawCircle(eyx + look[0] * er_ * .15 - er_ * .3, eyy - er_ * .35, er_ * .38, paint('#ffffff'))
            cv.drawCircle(eyx + er_ * .3, eyy + er_ * .32, er_ * .18, paint('#ffffff', .9))
        # cheek blush
        cv.drawOval(skia.Rect.MakeXYWH(eyx - er_ * .8, eyy + er_ * 1.5, er_ * 1.6, er_ * .8), paint('#ff8fb8', .55 * alpha))
        # mouth
        mx0, my0, _ = cen[int(N * .01)]; mx1, my1, mr = cen[int(N * .22)]
        mm = skia.Path(); mm.moveTo(mx0 - R * .02, my0 + R * .30); mm.quadTo((mx0 + mx1) / 2, my0 + R * (.55 + .4 * mouth), mx1, my1 + R * .26)
        cv.drawPath(mm, paint('#14103a', stroke=max(2, R * .05)))
        if mouth > .1:
            cv.drawOval(skia.Rect.MakeXYWH((mx0 + mx1) / 2 - R * .1, my0 + R * .38, R * .2, R * .14 * mouth + 2), paint('#ff7a9a', .8))
    # forehead star
    if kind == 'cub':
        hx, hy, _ = cen[int(N * .08)]
        sparkle(cv, hx - R * .08, hy - R * .62, R * .22, '#fff3a8', .95, t)
    cv.restore()
    return cen
