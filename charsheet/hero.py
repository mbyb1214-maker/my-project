import sys, math, random
sys.path.insert(0, '/home/user/my-project/starwhale')
import skia
from gfx import *

BLK, BLK2, BLK_HI = '#1e1a22', '#2e2833', '#4d4558'
TAN, TAN2, CREAM = '#c9864a', '#e2ad74', '#f3dcb8'
NOSE = '#121014'; TONGUE = '#ff7f9a'; EYE = '#5b2e18'
RED = '#d9302c'; RED2 = '#f0524a'
SILV, SILV2 = '#cfd5de', '#8f98a8'
PAD = '#d9ea72'; SMILE = '#f7d83a'
LEASH = '#f08a9e'
OUTL = '#150f18'

PAT = ['#f6f2ea', '#6cb2dc', '#7b60c8', '#f29c6c', '#9ad9c9']
def pattern(cv, path, seed=3, cols=PAT, scale=1.0, base=None):
    """geometric pastel print clipped to path"""
    r = random.Random(seed)
    b = path.getBounds()
    cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
    cv.drawRect(b, paint(base or cols[0]))
    step = 34 * scale
    y = b.top() - step
    while y < b.bottom() + step:
        x = b.left() - step
        while x < b.right() + step:
            c = r.choice(cols[1:]); k = r.random()
            p = skia.Path()
            if k < .4:
                p.moveTo(x, y); p.lineTo(x + step, y + step * .5); p.lineTo(x + step * .3, y + step); p.close()
            elif k < .75:
                p.addRect(skia.Rect.MakeXYWH(x + 4, y + 4, step * .6, step * .45))
            else:
                p.addCircle(x + step * .5, y + step * .5, step * .22)
            cv.drawPath(p, paint(c, .95))
            x += step
        y += step * .8
    cv.restore()
    cv.drawPath(path, paint(OUTL, .0))

def outline(cv, path, w=3, col=OUTL, a=1.0): cv.drawPath(path, paint(col, a, stroke=w))

def fluffy(pts, amp=7, seed=1):
    """wavy outline for feathered fur"""
    r = random.Random(seed); out = []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        nx, ny = pts[(i + 1) % n]; px, py = pts[i - 1]
        tx, ty = nx - px, ny - py; L = math.hypot(tx, ty) or 1
        ox, oy = -ty / L, tx / L
        k = amp * (1 if i % 2 else -.3) * (0.6 + .8 * r.random())
        out.append((x + ox * k, y + oy * k))
    return poly_smooth(out)

# ------------------------------------------------------------------ face parts
def eye_front(cv, x, y, mode='open', s=1.0, look=(0, 0), flip=1):
    rx, ry = 21 * s, 25 * s
    if mode in ('closed', 'happy', 'sleepy', 'joy'):
        p = skia.Path()
        if mode == 'happy' or mode == 'joy':
            p.moveTo(x - rx, y + 6 * s); p.quadTo(x, y - 24 * s, x + rx, y + 6 * s)
        elif mode == 'sleepy':
            p.moveTo(x - rx, y); p.quadTo(x, y + 10 * s, x + rx, y)
        else:
            p.moveTo(x - rx, y); p.quadTo(x, y + 12 * s, x + rx, y)
        cv.drawPath(p, paint(OUTL, stroke=5 * s)); return
    if mode == 'wide': rx, ry = 24 * s, 30 * s
    if mode == 'sad': ry = 25 * s
    cv.drawOval(skia.Rect.MakeXYWH(x - rx, y - ry, 2 * rx, 2 * ry), paint('#f7efe6'))
    ir = rx * (0.93 if mode != 'wide' else .78); iry = ry * (.93 if mode != 'wide' else .8)
    ix, iy = x + look[0] * 4 * s, y + look[1] * 4 * s
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x - rx, y - ry, 2 * rx, 2 * ry))
    cv.drawOval(skia.Rect.MakeXYWH(ix - ir, iy - iry, 2 * ir, 2 * iry), paint(shader=lin(0, iy - iry, 0, iy + iry, ['#3a1c0e', EYE, '#9a5a30'], [0, .55, 1])))
    cv.drawOval(skia.Rect.MakeXYWH(ix - ir * .55, iy - iry * .55, ir * 1.1, iry * 1.1), paint('#150805'))
    if mode == 'angry':
        cv.drawRect(skia.Rect.MakeXYWH(x - rx, y - ry, 2 * rx, ry * .55), paint(BLK))
    if mode == 'sleepy':
        cv.drawRect(skia.Rect.MakeXYWH(x - rx, y - ry, 2 * rx, ry * 1.05), paint(BLK))
    cv.restore()
    cv.drawCircle(ix - ir * .35, iy - iry * .38, ir * .34, paint('#ffffff'))
    cv.drawCircle(ix + ir * .32, iy + iry * .32, ir * .15, paint('#ffffff', .9))
    if mode == 'sparkle':
        sparkle(cv, ix + ir * .25, iy - iry * .1, ir * .5, '#ffffff', 1, 0)
    lid = skia.Path(); lid.moveTo(x - rx * 1.05, y - ry * .1); lid.quadTo(x, y - ry * 1.35, x + rx * 1.05, y - ry * .1)
    cv.drawPath(lid, paint(OUTL, stroke=4.5 * s))
    if mode == 'sad':
        cv.drawCircle(x - 6 * s, y + ry + 4 * s, 5 * s, paint('#9fdcff', .9))

def head_front(cv, expr='normal', s=1.0, ear_flop=0.0, t=0.0):
    """centered at (0,0), width ~ 300*s incl. ears"""
    cv.save(); cv.scale(s, s)
    E = expr
    eyes = {'normal': 'open', 'happy': 'open', 'joy': 'joy', 'surprise': 'wide', 'sad': 'sad', 'angry': 'angry',
            'sleepy': 'sleepy', 'blush': 'open', 'wink': 'wink', 'sparkle': 'sparkle', 'cry': 'closed'}[E]
    # ears (behind head)
    for sg in (-1, 1):
        pts = [(sg * 58, -78), (sg * 112, -66), (sg * 150 + sg * ear_flop, -10), (sg * 162, 60), (sg * 150, 112), (sg * 120, 128),
               (sg * 100, 98), (sg * 84, 40), (sg * 66, -20)]
        ear = fluffy(pts, 8, 4 + int(sg))
        cv.drawPath(ear, paint(shader=lin(sg * 60, -80, sg * 150, 130, [BLK2, BLK, '#100c12'], [0, .5, 1])))
        outline(cv, ear, 3)
        for k in range(5):
            f = skia.Path(); f.moveTo(sg * (92 + k * 14), -30 + k * 10); f.quadTo(sg * (118 + k * 9), 30 + k * 16, sg * (112 + k * 9), 100 - k * 4)
            cv.drawPath(f, paint(BLK_HI, .45, stroke=2.5))
    # head
    head = poly_smooth([(-92, -20), (-84, -66), (-40, -92), (0, -97), (40, -92), (84, -66), (92, -20), (84, 40), (56, 82), (0, 98), (-56, 82), (-84, 40)])
    cv.drawPath(head, paint(shader=lin(0, -100, 0, 100, [BLK_HI, BLK, BLK2], [0, .25, 1])))
    outline(cv, head, 3)
    # forehead sheen
    sh = skia.Path(); sh.moveTo(-40, -76); sh.quadTo(0, -92, 40, -76)
    cv.drawPath(sh, paint('#ffffff', .22, stroke=7))
    # tan cheeks + muzzle
    cheek = poly_smooth([(-82, 10), (-60, -4), (-36, 18), (-20, 50), (0, 62), (20, 50), (36, 18), (60, -4), (82, 10), (74, 52), (44, 84), (0, 92), (-44, 84), (-74, 52)])
    cv.drawPath(cheek, paint(shader=lin(0, -10, 0, 94, [TAN, TAN2, CREAM], [0, .6, 1])))
    muz = poly_smooth([(-34, 0), (-12, -10), (12, -10), (34, 0), (44, 36), (28, 70), (0, 78), (-28, 70), (-44, 36)])
    cv.drawPath(muz, paint(shader=lin(0, -10, 0, 78, [TAN2, CREAM], [0, 1]), a=.9))
    # eyebrow spots
    brow_dy = {'sad': (-1, 6), 'angry': (4, -4), 'surprise': (-10, 0), 'sleepy': (4, 0)}.get(E, (0, 0))
    for sg in (-1, 1):
        dy = brow_dy[0] if brow_dy[1] == 0 else brow_dy[0] * 0
        tilt = (brow_dy[1] if E == 'sad' else -brow_dy[1] if E == 'angry' else 0) * sg * (-1)
        cv.save(); cv.translate(sg * 40, -52 + (brow_dy[0] if E in ('surprise', 'sleepy', 'angry') else 0)); cv.rotate(tilt * 2.5)
        cv.drawOval(skia.Rect.MakeXYWH(-17, -9, 34, 18), paint(TAN2)); cv.restore()
    # eyes
    for sg in (-1, 1):
        m = eyes
        if E == 'wink' and sg == 1: m = 'happy'
        eye_front(cv, sg * 40, -14, m, 1.0, (0, 0))
    if E == 'angry':
        for sg in (-1, 1):
            p = skia.Path(); p.moveTo(sg * 18, -48); p.lineTo(sg * 66, -34 + 0)
    # blush
    if E in ('blush', 'happy', 'joy', 'sparkle'):
        for sg in (-1, 1): cv.drawOval(skia.Rect.MakeXYWH(sg * 62 - 16, 20, 32, 16), paint('#ff7a8a', .5))
    # nose
    nose = skia.Path(); nose.addOval(skia.Rect.MakeXYWH(-23, 4, 46, 30))
    cv.drawPath(nose, paint(NOSE)); cv.drawOval(skia.Rect.MakeXYWH(-13, 9, 14, 6), paint('#ffffff', .55))
    cv.drawLine(0, 34, 0, 48, paint(OUTL, stroke=3))
    # mouth
    my = 48
    def mo(): return skia.Path()
    if E in ('normal', 'blush', 'sleepy'):
        p = mo(); p.moveTo(-30, my + 4); p.quadTo(-14, my + 18, 0, my); p.quadTo(14, my + 18, 30, my + 4)
        cv.drawPath(p, paint(OUTL, stroke=3.5))
        if E == 'blush': cv.drawLine(0, my, 0, my + 2, paint(OUTL, stroke=3))
    elif E in ('happy', 'wink', 'sparkle', 'joy'):
        p = mo(); p.moveTo(-34, my - 2); p.quadTo(0, my + 54, 34, my - 2); p.quadTo(0, my + 12, -34, my - 2)
        cv.drawPath(p, paint('#7a1c30')); 
        cv.save(); cv.clipPath(p, skia.ClipOp.kIntersect, True)
        cv.drawOval(skia.Rect.MakeXYWH(-18, my + 18, 36, 30), paint(TONGUE)); cv.restore()
        cv.drawPath(p, paint(OUTL, stroke=3.5))
    elif E == 'surprise':
        cv.drawOval(skia.Rect.MakeXYWH(-14, my + 2, 28, 34), paint('#7a1c30')); cv.drawOval(skia.Rect.MakeXYWH(-14, my + 2, 28, 34), paint(OUTL, stroke=3.5))
        cv.drawOval(skia.Rect.MakeXYWH(-8, my + 22, 16, 12), paint(TONGUE))
    elif E == 'sad' or E == 'cry':
        p = mo(); p.moveTo(-26, my + 14); p.quadTo(-12, my - 2, 0, my + 6); p.quadTo(12, my - 2, 26, my + 14)
        cv.drawPath(p, paint(OUTL, stroke=3.5))
    elif E == 'angry':
        p = mo(); p.moveTo(-34, my + 8); p.quadTo(-16, my - 6, 0, my + 6); p.quadTo(16, my - 6, 34, my + 8)
        cv.drawPath(p, paint(OUTL, stroke=3.8))
        for sg in (-1, 1): cv.drawPath(skia.Path().moveTo(sg * 12, my + 4).lineTo(sg * 16, my + 16), paint('#ffffff', stroke=0))
    if E == 'cry':
        for sg in (-1, 1):
            tr = skia.Path(); tr.moveTo(sg * 40, -2); tr.quadTo(sg * 56, 40, sg * 48, 80)
            cv.drawPath(tr, paint('#9fdcff', .9, stroke=7))
    if E == 'angry':
        for sg in (-1, 1):
            b = skia.Path(); b.moveTo(sg * 18, -44); b.lineTo(sg * 66, -62 + 14 * 0); 
        # angry brow marks
        cv.drawLine(-62, -52, -20, -38, paint(OUTL, stroke=6)); cv.drawLine(62, -52, 20, -38, paint(OUTL, stroke=6))
        for k in range(3): cv.drawLine(-150 + k * 6, -100 + k * 8, -118 + k * 6, -78 + k * 8, paint('#ff5a4a', stroke=4)) if False else None
    if E == 'sleepy':
        for i in range(3): text(cv, 'Z', 100 + i * 24, -70 - i * 30, 28 + i * 8, '#8aa0ff', .9 - i * .2)
    if E == 'surprise':
        for k in range(4):
            a = math.radians(-60 - k * 20); cv.drawLine(math.cos(a) * 130 - 0, math.sin(a) * 130 - 10, math.cos(a) * 160, math.sin(a) * 160 - 10, paint('#ffffff', .8, stroke=4))
    cv.restore()

# ------------------------------------------------------------------ body pieces
def wheel(cv, x, y, r, face=True):
    cv.drawCircle(x, y, r, paint('#1a181c')); cv.drawCircle(x, y, r, paint('#000000', stroke=2))
    cv.drawCircle(x, y, r * .78, paint('#2a272e')); 
    for k in range(10):
        a = k * math.pi / 5; cv.drawLine(x + math.cos(a) * r * .4, y + math.sin(a) * r * .4, x + math.cos(a) * r * .74, y + math.sin(a) * r * .74, paint('#454050', stroke=1.8))
    cv.drawCircle(x, y, r * .62, paint(shader=rad(x - r * .15, y - r * .15, r * .7, ['#ffffff', SILV, SILV2], [0, .5, 1])))
    cv.drawCircle(x, y, r * .62, paint(OUTL, .6, stroke=2))
    for k in range(5):
        a = k * 2 * math.pi / 5 + .3; cv.drawLine(x, y, x + math.cos(a) * r * .55, y + math.sin(a) * r * .55, paint('#8f98a8', stroke=3))
    cv.drawCircle(x, y, r * .13, paint(SILV2)); cv.drawCircle(x, y, r * .13, paint(OUTL, stroke=1.5))

def tube(cv, pts, w=12):
    p = poly_smooth(pts, closed=False)
    cv.drawPath(p, paint(OUTL, stroke=w + 4))
    cv.drawPath(p, paint(shader=lin(0, pts[0][1] - w, 0, pts[0][1] + w, ['#ffffff', SILV, SILV2]), stroke=w))

def padded(cv, pts, w=20):
    p = poly_smooth(pts, closed=False)
    cv.drawPath(p, paint(OUTL, stroke=w + 4)); cv.drawPath(p, paint(PAD, stroke=w))
    cv.drawPath(p, paint('#ffffff', .35, stroke=w * .3))

def smiley(cv, x, y, r):
    cv.drawCircle(x, y, r, paint(SMILE)); cv.drawCircle(x, y, r, paint('#a89418', stroke=2))
    for sg in (-1, 1): cv.drawOval(skia.Rect.MakeXYWH(x + sg * r * .38 - r * .09, y - r * .38, r * .18, r * .3), paint('#2a2410'))
    p = skia.Path(); p.moveTo(x - r * .5, y + r * .12); p.quadTo(x, y + r * .7, x + r * .5, y + r * .12)
    cv.drawPath(p, paint('#2a2410', stroke=r * .12))

def paw(cv, x, y, w=44, toe=0):
    p = poly_smooth([(x - w / 2, y - 60), (x + w / 2, y - 60), (x + w / 2 + 3, y - 14), (x + w / 2 + 8, y + 4), (x + w / 4, y + 12), (x - w / 4, y + 12), (x - w / 2 - 8, y + 4), (x - w / 2 - 3, y - 14)])
    cv.drawPath(p, paint(shader=lin(0, y - 60, 0, y + 12, [BLK, BLK2, CREAM, CREAM], [0, .45, .62, 1])))
    outline(cv, p, 3)
    for k in (-1, 0, 1): cv.drawLine(x + k * w * .22, y - 2, x + k * w * .22, y + 10, paint(OUTL, .7, stroke=2))

# ------------------------------------------------------------------ FRONT VIEW
def view_front(cv, expr='normal'):
    # coordinate: ground at y=+260, head center (0,-110)
    # cart wheels (behind)
    for sg in (-1, 1):
        wheel(cv, sg * 200, 190, 72)
        tube(cv, [(sg * 200, 190), (sg * 170, 110), (sg * 128, 40)], 11)
    tube(cv, [(-150, 20), (0, 0), (150, 20)], 11)
    # shadow
    cv.drawOval(skia.Rect.MakeXYWH(-190, 246, 380, 28), paint('#000000', .25, blur=8))
    # body
    body = poly_smooth([(-118, -40), (-100, 40), (-96, 140), (-60, 200), (60, 200), (96, 140), (100, 40), (118, -40), (60, -70), (-60, -70)])
    cv.drawPath(body, paint(shader=lin(0, -60, 0, 200, [BLK, BLK2])))
    # chest fur (cream/tan)
    chest = poly_smooth([(-56, 20), (-36, 60), (-30, 130), (0, 168), (30, 130), (36, 60), (56, 20), (0, 4)])
    cv.drawPath(chest, paint(shader=lin(0, 0, 0, 170, [TAN, TAN2, CREAM], [0, .5, 1])))
    # outfit (behind head, over shoulders)
    suit = poly_smooth([(-120, -50), (-122, 30), (-108, 90), (-74, 112), (-40, 100), (0, 108), (40, 100), (74, 112), (108, 90), (122, 30), (120, -50), (60, -80), (-60, -80)])
    pattern(cv, suit, seed=5)
    outline(cv, suit, 3)
    # harness
    for sg in (-1, 1):
        s_ = skia.Path(); s_.moveTo(sg * 62, -30); s_.lineTo(sg * 40, 40); s_.lineTo(sg * 12, 150)
        cv.drawPath(s_, paint(OUTL, stroke=26)); cv.drawPath(s_, paint(RED, stroke=20)); cv.drawPath(s_, paint('#ff8a80', .5, stroke=5))
    cv.drawRoundRect(skia.Rect.MakeXYWH(-22, 36, 44, 30), 6, 6, paint(OUTL)); cv.drawRoundRect(skia.Rect.MakeXYWH(-17, 41, 34, 20), 4, 4, paint(SILV))
    cv.drawRect(skia.Rect.MakeXYWH(-9, 41, 18, 20), paint(RED2))
    # front legs
    for sg in (-1, 1): paw(cv, sg * 48, 252, 50)
    head_front(cv, expr, 1.0)  # at (0,0) → translate before call
    # (head drawn by caller with translation)

def draw_front(cv, x, y, expr='normal', sc=1.0):
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    # draw body parts, then head at (0,-110)
    for sg in (-1, 1):
        wheel(cv, sg * 172, 190, 70)
        tube(cv, [(sg * 172, 190), (sg * 150, 110), (sg * 122, 30)], 11)
    tube(cv, [(-125, 14), (0, -6), (125, 14)], 11)
    cv.drawOval(skia.Rect.MakeXYWH(-190, 246, 380, 28), paint('#000000', .3, blur=8))
    body = poly_smooth([(-112, -40), (-98, 40), (-94, 140), (-60, 205), (60, 205), (94, 140), (98, 40), (112, -40), (60, -70), (-60, -70)])
    cv.drawPath(body, paint(shader=lin(0, -60, 0, 200, [BLK, BLK2]))); outline(cv, body, 3)
    chest = poly_smooth([(-58, 14), (-38, 56), (-32, 130), (0, 172), (32, 130), (38, 56), (58, 14), (0, -4)])
    cv.drawPath(chest, paint(shader=lin(0, 0, 0, 170, [TAN, TAN2, CREAM], [0, .5, 1])))
    for sg in (-1, 1): paw(cv, sg * 46, 258, 52)
    suit = poly_smooth([(-120, -50), (-124, 30), (-110, 84), (-76, 100), (-40, 86), (0, 92), (40, 86), (76, 100), (110, 84), (124, 30), (120, -50), (60, -80), (-60, -80)])
    pattern(cv, suit, seed=5); outline(cv, suit, 3)
    for sg in (-1, 1):
        s_ = skia.Path(); s_.moveTo(sg * 66, -34); s_.lineTo(sg * 44, 40); s_.lineTo(sg * 14, 150)
        cv.drawPath(s_, paint(OUTL, stroke=26)); cv.drawPath(s_, paint(RED, stroke=20)); cv.drawPath(s_, paint('#ff8a80', .45, stroke=5))
    cv.drawRoundRect(skia.Rect.MakeXYWH(-22, 30, 44, 30), 6, 6, paint(OUTL)); cv.drawRoundRect(skia.Rect.MakeXYWH(-17, 35, 34, 20), 4, 4, paint(SILV))
    cv.drawRect(skia.Rect.MakeXYWH(-9, 35, 18, 20), paint(RED2))
    cv.save(); cv.translate(0, -118); head_front(cv, expr, 1.0); cv.restore()
    cv.restore()

# ------------------------------------------------------------------ SIDE VIEW (faces right)
def draw_side(cv, x, y, expr='normal', sc=1.0, flip=1):
    cv.save(); cv.translate(x, y); cv.scale(sc * flip, sc)
    G = 150   # ground
    cv.drawOval(skia.Rect.MakeXYWH(-290, G - 12, 640, 30), paint('#000000', .3, blur=9))
    # far legs
    paw(cv, 84, G, 40); 
    # tail
    tl = poly_smooth([(-168, -52), (-210, -40), (-248, -4), (-262, 40), (-244, 52), (-226, 20), (-196, -14), (-166, -22)])
    cv.drawPath(tl, paint(shader=lin(-260, 0, -170, -40, [BLK2, BLK]))); outline(cv, tl, 3)
    for k in range(4): cv.drawLine(-230 + k * 12, 0 + k * 3, -250 + k * 12, 38 - k * 3, paint(BLK_HI, .5, stroke=2))
    # cart: rear wheel + frame
    wheel(cv, -205, G - 72, 72)
    tube(cv, [(-205, G - 72), (-170, 36), (-120, 24)], 11)
    tube(cv, [(-205, G - 72), (-150, 60), (-40, 40), (80, 30)], 11)
    # body
    body = poly_smooth([(-176, -66), (-182, -10), (-166, 40), (-110, 62), (-20, 58), (80, 56), (150, 40), (178, -6), (170, -66), (110, -96), (0, -102), (-110, -96)])
    cv.drawPath(body, paint(shader=lin(0, -100, 0, 60, [BLK_HI, BLK, BLK2], [0, .3, 1]))); outline(cv, body, 3)
    # belly tan feathering
    bel = poly_smooth([(-90, 54), (-30, 36), (30, 40), (100, 54), (110, 66), (30, 72), (-40, 70), (-100, 66)])
    cv.drawPath(bel, paint(TAN, .85))
    # hind legs in cradle
    for dx, dz in ((-104, 0), (-70, 10)):
        hl = poly_smooth([(dx - 16, 0), (dx + 16, 0), (dx + 18, 54 + dz), (dx + 14, 78 + dz), (dx - 12, 80 + dz), (dx - 16, 54 + dz)])
        cv.drawPath(hl, paint(shader=lin(0, 0, 0, 90, [BLK, BLK2, CREAM], [0, .6, .85]))); outline(cv, hl, 3)
    # cart pad (yellow-green) wrapping under hip
    padded(cv, [(-150, 52), (-110, 66), (-60, 70), (-20, 64)], 22)
    smiley(cv, -128, 66, 12)
    # outfit
    suit = poly_smooth([(-160, -76), (-170, -20), (-150, 6), (-100, 12), (-40, 4), (30, 10), (90, 2), (126, -20), (128, -60), (96, -96), (0, -102), (-100, -96)])
    pattern(cv, suit, seed=8); outline(cv, suit, 3)
    bow = skia.Path(); bow.moveTo(-20, -102); bow.lineTo(-48, -128); bow.lineTo(-46, -92); bow.close(); bow.moveTo(-20, -102); bow.lineTo(8, -126); bow.lineTo(6, -90); bow.close()
    cv.drawPath(bow, paint('#ffd84a')); outline(cv, bow, 2.5); cv.drawCircle(-20, -100, 8, paint('#f0b428')); 
    # harness at chest
    hs = skia.Path(); hs.moveTo(128, -70); hs.quadTo(150, -20, 134, 40)
    cv.drawPath(hs, paint(OUTL, stroke=26)); cv.drawPath(hs, paint(RED, stroke=20)); cv.drawPath(hs, paint('#ff8a80', .45, stroke=5))
    hs2 = skia.Path(); hs2.moveTo(122, -92); hs2.lineTo(40, -98)
    cv.drawPath(hs2, paint(OUTL, stroke=18)); cv.drawPath(hs2, paint(RED, stroke=12))
    cv.drawRoundRect(skia.Rect.MakeXYWH(30, -112, 24, 26), 5, 5, paint(OUTL)); cv.drawRoundRect(skia.Rect.MakeXYWH(34, -108, 16, 18), 3, 3, paint(SILV))
    # leash
    ls = skia.Path(); ls.moveTo(42, -108); ls.cubicTo(-30, -190, -150, -170, -210, -120)
    cv.drawPath(ls, paint(LEASH, stroke=5))
    # near front leg + chest
    ch = poly_smooth([(112, -20), (150, 10), (150, 70), (120, 96), (84, 70), (84, 10)])
    cv.drawPath(ch, paint(shader=lin(0, -20, 0, 100, [TAN, TAN2, CREAM], [0, .6, 1]))); outline(cv, ch, 2.5)
    paw(cv, 118, G, 44)
    # head profile (facing right)
    cv.save(); cv.translate(198, -72)
    ear_sw = 0
    hd = poly_smooth([(-60, -30), (-30, -74), (20, -84), (66, -60), (84, -26), (140, -6), (150, 20), (132, 40), (84, 44), (50, 74), (0, 80), (-44, 60), (-66, 20)])
    cv.drawPath(hd, paint(shader=lin(0, -80, 0, 80, [BLK_HI, BLK, BLK2], [0, .3, 1]))); outline(cv, hd, 3)
    mz = poly_smooth([(84, -14), (140, -6), (150, 20), (132, 42), (84, 46), (60, 24), (70, -4)])
    cv.drawPath(mz, paint(shader=lin(0, -10, 0, 46, [TAN2, TAN, CREAM], [0, .5, 1])))
    cv.drawOval(skia.Rect.MakeXYWH(126, -22, 30, 22), paint(NOSE)); cv.drawOval(skia.Rect.MakeXYWH(136, -19, 10, 5), paint('#ffffff', .55))
    # tan brow + cheek
    cv.save(); cv.translate(60, -38); cv.rotate(-14); cv.drawOval(skia.Rect.MakeXYWH(-14, -8, 28, 16), paint(TAN2)); cv.restore()
    ch2 = poly_smooth([(20, 6), (58, 18), (80, 44), (52, 66), (6, 56)])
    cv.drawPath(ch2, paint(TAN, .85))
    # eye
    eyem = {'normal': 'open', 'happy': 'happy', 'joy': 'joy', 'surprise': 'wide', 'sad': 'sad', 'angry': 'angry', 'sleepy': 'sleepy', 'blush': 'open', 'wink': 'happy', 'sparkle': 'sparkle', 'cry': 'closed'}[expr]
    eye_front(cv, 74, -20, eyem, .95, (.6, 0))
    # mouth line
    m = skia.Path(); m.moveTo(142, 28); m.quadTo(112, 40, 84, 30)
    if expr in ('happy', 'joy', 'sparkle', 'wink', 'surprise'):
        mm = skia.Path(); mm.moveTo(144, 30); mm.quadTo(114, 62, 80, 34); mm.quadTo(112, 40, 144, 30)
        cv.drawPath(mm, paint('#7a1c30')); cv.drawOval(skia.Rect.MakeXYWH(104, 42, 26, 18), paint(TONGUE))
    cv.drawPath(m, paint(OUTL, stroke=3.5))
    # ear (long, hanging) over cheek
    ep = [(10, -62), (56, -58), (66, -8), (68, 50), (54, 104), (24, 122), (-8, 100), (-18, 40), (-14, -20)]
    ear = fluffy(ep, 8, 9)
    cv.drawPath(ear, paint(shader=lin(0, -60, 50, 120, [BLK2, BLK, '#100c12'], [0, .5, 1]))); outline(cv, ear, 3)
    for k in range(5):
        f = skia.Path(); f.moveTo(-6 + k * 12, -30 + k * 4); f.quadTo(-2 + k * 12, 40, 4 + k * 12, 98 - k * 6)
        cv.drawPath(f, paint(BLK_HI, .5, stroke=2.5))
    cv.restore()
    # ground-level front far/near ordering done
    cv.restore()

# ------------------------------------------------------------------ BACK VIEW
def draw_back(cv, x, y, sc=1.0):
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    cv.drawOval(skia.Rect.MakeXYWH(-200, 246, 400, 30), paint('#000000', .3, blur=8))
    # ears (peeking either side of head, behind body)
    for sg in (-1, 1):
        wheel(cv, sg * 172, 190, 70)
        tube(cv, [(sg * 172, 190), (sg * 150, 100), (sg * 118, 20)], 11)
    # cart tray + pad
    tray = poly_smooth([(-120, 150), (-90, 214), (0, 226), (90, 214), (120, 150), (60, 130), (-60, 130)])
    cv.drawPath(tray, paint(OUTL)); 
    tube(cv, [(-172, 190), (-120, 190), (0, 196), (120, 190), (172, 190)], 11)
    # hind legs hanging
    for sg in (-1, 1):
        hl = poly_smooth([(sg * 46 - 20, 150), (sg * 46 + 20, 150), (sg * 48 + 22, 208), (sg * 50 + 16, 244), (sg * 48 - 14, 246), (sg * 44 - 20, 208)])
        cv.drawPath(hl, paint(shader=lin(0, 150, 0, 250, [BLK, BLK2, CREAM], [0, .7, .9]))); outline(cv, hl, 3)
    padded(cv, [(-130, 128), (-100, 160), (0, 172), (100, 160), (130, 128)], 24)
    # tail
    tl = poly_smooth([(-14, 100), (14, 100), (22, 160), (28, 220), (8, 246), (-14, 226), (-18, 160)])
    cv.drawPath(tl, paint(shader=lin(0, 100, 0, 240, [BLK2, BLK]))); outline(cv, tl, 3)
    smiley(cv, 0, 204, 20)
    # body
    body = poly_smooth([(-118, -50), (-124, 30), (-112, 100), (-70, 150), (0, 160), (70, 150), (112, 100), (124, 30), (118, -50), (60, -88), (-60, -88)])
    cv.drawPath(body, paint(shader=lin(0, -80, 0, 150, [BLK, BLK2]))); outline(cv, body, 3)
    suit = poly_smooth([(-120, -60), (-128, 40), (-112, 104), (-60, 122), (0, 130), (60, 122), (112, 104), (128, 40), (120, -60), (60, -92), (-60, -92)])
    pattern(cv, suit, seed=5, scale=1.1); outline(cv, suit, 3)
    # bow
    bow = skia.Path(); bow.moveTo(0, 20); bow.lineTo(-52, -6); bow.lineTo(-48, 50); bow.close(); bow.moveTo(0, 20); bow.lineTo(52, -6); bow.lineTo(48, 50); bow.close()
    cv.drawPath(bow, paint('#ffd84a')); outline(cv, bow, 2.5); cv.drawCircle(0, 20, 11, paint('#f0b428')); outline(cv, skia.Path().addCircle(0, 20, 11), 2)
    # harness straps + ring
    for sg in (-1, 1):
        s_ = skia.Path(); s_.moveTo(sg * 28, -70); s_.lineTo(sg * 100, 30); s_.lineTo(sg * 118, 100)
        cv.drawPath(s_, paint(OUTL, stroke=22)); cv.drawPath(s_, paint(RED, stroke=16)); cv.drawPath(s_, paint('#ff8a80', .4, stroke=4))
    cv.drawCircle(0, -70, 14, paint(SILV)); cv.drawCircle(0, -70, 14, paint(OUTL, stroke=3)); cv.drawCircle(0, -70, 6, paint('#555555'))
    # cart belt across back
    tube(cv, [(-130, 58), (0, 44), (130, 58)], 9)
    # head from behind
    cv.save(); cv.translate(0, -140)
    for sg in (-1, 1):
        pts = [(sg * 50, -66), (sg * 106, -60), (sg * 146, -6), (sg * 156, 56), (sg * 142, 106), (sg * 114, 122), (sg * 94, 94), (sg * 78, 40), (sg * 60, -14)]
        ear = fluffy(pts, 8, 12 + int(sg)); cv.drawPath(ear, paint(shader=lin(sg * 60, -60, sg * 150, 120, [BLK2, BLK, '#100c12'], [0, .5, 1]))); outline(cv, ear, 3)
        for k in range(5):
            f = skia.Path(); f.moveTo(sg * (88 + k * 12), -30 + k * 10); f.quadTo(sg * (110 + k * 9), 30 + k * 16, sg * (104 + k * 9), 96 - k * 4)
            cv.drawPath(f, paint(BLK_HI, .45, stroke=2.5))
    hd = poly_smooth([(-86, -10), (-80, -58), (-40, -84), (0, -90), (40, -84), (80, -58), (86, -10), (76, 40), (46, 76), (0, 88), (-46, 76), (-76, 40)])
    cv.drawPath(hd, paint(shader=lin(0, -90, 0, 90, [BLK_HI, BLK, BLK2], [0, .25, 1]))); outline(cv, hd, 3)
    sh = skia.Path(); sh.moveTo(-36, -68); sh.quadTo(0, -84, 36, -68); cv.drawPath(sh, paint('#ffffff', .22, stroke=7))
    cv.restore()
    cv.restore()

# ------------------------------------------------------------------ layout
def label(cv, s, x, y, size=26, col='#3a2f45', a=1.0, align='center'):
    text(cv, s, x, y, size, col, a, align=align)

def tag(cv, x, y, s, w=None, col='#7a5fc8'):
    f = skia.Font(FONT, 20); tw = f.measureText(s) + 28 if w is None else w
    cv.drawRoundRect(skia.Rect.MakeXYWH(x, y, tw, 34), 17, 17, paint(col))
    text(cv, s, x + tw / 2, y + 24, 20, '#ffffff')
    return tw

def callout(cv, x0, y0, x1, y1, s, align='left'):
    cv.drawLine(x0, y0, x1, y1, paint('#7a5fc8', .8, stroke=2))
    cv.drawCircle(x0, y0, 5, paint('#7a5fc8'))
    f = skia.Font(FONT, 21); w = f.measureText(s)
    bx = x1 if align == 'left' else x1 - w - 20
    cv.drawRoundRect(skia.Rect.MakeXYWH(bx, y1 - 18, w + 20, 34), 10, 10, paint('#ffffff', .95))
    cv.drawRoundRect(skia.Rect.MakeXYWH(bx, y1 - 18, w + 20, 34), 10, 10, paint('#7a5fc8', stroke=2))
    text(cv, s, bx + 10, y1 + 6, 21, '#2d2540', align='left')


def checker(cv, rect, c1='#d9302c', c2='#fff4f0', n=12):
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(rect, 16, 16), skia.ClipOp.kIntersect, True)
    w = rect.width() / n
    for i in range(n):
        for j in range(int(rect.height() / w) + 1):
            cv.drawRect(skia.Rect.MakeXYWH(rect.left() + i * w, rect.top() + j * w, w, w), paint(c1 if (i + j) % 2 else c2))
    cv.restore()

def pinkprint(cv, rect):
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(rect, 16, 16), skia.ClipOp.kIntersect, True)
    cv.drawRect(rect, paint('#fff0f4'))
    r = random.Random(4)
    for k in range(34):
        x = rect.left() + r.random() * rect.width(); y = rect.top() + r.random() * rect.height()
        c = r.choice(['#f48aa8', '#6cb2dc', '#ffd36a', '#9ad9c9', '#b79af0'])
        cv.drawCircle(x, y, 9 + r.random() * 6, paint(c, .95)); cv.drawCircle(x - 3, y - 3, 3, paint('#ffffff', .8))
    cv.restore()

def swatch(cv, x, y, col, name, hexs):
    cv.drawCircle(x, y, 42, paint(OUTL, .15)); cv.drawCircle(x, y, 40, paint(col)); cv.drawCircle(x - 12, y - 14, 9, paint('#ffffff', .5))
    text(cv, name, x, y + 72, 21, '#2d2540'); text(cv, hexs, x, y + 96, 17, '#7a6f90')

def panel(cv, x, y, w, h, title):
    cv.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), 20, 20, paint('#ffffff', .65))
    cv.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), 20, 20, paint('#c9c4e8', stroke=2))
    tag(cv, x + 16, y + 14, title)

def sheet(path):
    SW, SH = 3000, 1900
    s = skia.Surface(SW, SH); cv = s.getCanvas()
    cv.drawRect(skia.Rect.MakeWH(SW, SH), paint(shader=lin(0, 0, 0, SH, ['#fbf7ff', '#eef0ff'])))
    for gx in range(0, SW, 40):
        for gy in range(0, SH, 40): cv.drawCircle(gx, gy, 1.4, paint('#c9c4e8', .6))
    cv.drawRect(skia.Rect.MakeXYWH(0, 0, SW, 120), paint(shader=lin(0, 0, SW, 0, ['#5b3fc0', '#8f6ae8', '#f08ab0'])))
    text(cv, "主人公キャラクター設定シート", 60, 82, 62, '#ffffff', align='left', spacing=4)
    f = skia.Font(FONT, 28); t_ = "CHARACTER DESIGN SHEET  /  PROTAGONIST"; text(cv, t_, SW - 60 - f.measureText(t_), 72, 28, '#ffffff', .9, align='left')
    cv.drawRoundRect(skia.Rect.MakeXYWH(40, 140, 2920, 76), 18, 18, paint('#ffffff', .9)); cv.drawRoundRect(skia.Rect.MakeXYWH(40, 140, 2920, 76), 18, 18, paint('#c9c4e8', stroke=2))
    info = [("キャラクター名", "（未設定）"), ("種族", "ダックスフンド系の犬（ブラック＆タン／ロングコート）"), ("特徴", "後肢サポートカート（車いす）で元気に走る"), ("性格", "好奇心旺盛・人懐っこい・くじけない")]
    xx = 70
    for k, v in info:
        w = tag(cv, xx, 160, k, col='#6a4fc0'); text(cv, v, xx + w + 14, 186, 25, '#2d2540', align='left')
        xx += w + 14 + skia.Font(FONT, 25).measureText(v) + 60
    # turnarounds
    P = [("FRONT  正面", 40, 560), ("SIDE (LEFT)  左側面", 620, 860), ("BACK  背面", 1500, 560), ("SIDE (RIGHT)  右側面", 2080, 880)]
    for nm, px, pw in P: panel(cv, px, 236, pw, 740, nm)
    G = 930
    draw_front(cv, 40 + 280, G - 262, 'normal')
    draw_side(cv, 620 + 430 + 44, G - 150, 'normal', 1.0, flip=-1)
    draw_back(cv, 1500 + 280, G - 262)
    draw_side(cv, 2080 + 440 - 44, G - 150, 'normal', 1.0, flip=1)
    # callouts
    callout(cv, 462, 560, 590, 340, "ふさふさの長い垂れ耳", 'right')
    callout(cv, 282, 498, 60, 420, "眉のタンの点（チャームポイント）", 'left')
    callout(cv, 1299, 925, 1010, 957, "銀フレームの歩行補助カート", 'left')
    callout(cv, 1090, 700, 700, 390, "長い胴と短い足（ダックス体型）", 'left')
    callout(cv, 2612, 735, 2940, 340, "赤いハーネス＆リボン", 'right')
    callout(cv, 2376, 862, 2130, 957, "黄緑のパッド＆スマイルシール", 'left')
    callout(cv, 1780, 598, 1860, 350, "ハーネスのリング", 'left')
    callout(cv, 1780, 872, 1540, 957, "スマイルシール付きトレイ", 'left')
    # expressions
    panel(cv, 40, 996, 2040, 880, "EXPRESSIONS  表情集")
    ex = [('normal', "通常"), ('happy', "にっこり"), ('joy', "大喜び"), ('surprise', "びっくり"), ('sad', "しょんぼり"),
          ('angry', "ムッ！（やる気）"), ('sleepy', "ねむい"), ('blush', "てれ"), ('wink', "ウインク"), ('sparkle', "キラキラ")]
    for i, (e, nm) in enumerate(ex):
        cx = 40 + 220 + (i % 5) * 400 - 20 + 20; cy = 1230 + (i // 5) * 400
        cv.save(); cv.translate(cx, cy); head_front(cv, e, 1.12); cv.restore()
        text(cv, nm, cx, cy + 190, 28, '#2d2540')
    # right column: palette, outfits, notes
    panel(cv, 2100, 996, 860, 300, "COLOR PALETTE  配色")
    sw = [(BLK, "ブラック", BLK), (TAN, "タン", TAN), (CREAM, "クリーム", CREAM), (RED, "ハーネス赤", RED), (PAD, "パッド黄緑", PAD), (SILV, "フレーム銀", SILV)]
    for i, (c, n, h) in enumerate(sw): swatch(cv, 2170 + i * 134, 1100, c, n, h.upper() if False else h)
    panel(cv, 2100, 1316, 860, 250, "OUTFIT  衣装バリエーション")
    r1 = skia.Rect.MakeXYWH(2130, 1370, 240, 150); r2 = skia.Rect.MakeXYWH(2400, 1370, 240, 150); r3 = skia.Rect.MakeXYWH(2670, 1370, 240, 150)
    pth = skia.Path(); pth.addRoundRect(r1, 16, 16); pattern(cv, pth, seed=5, scale=.8); outline(cv, pth, 3)
    pinkprint(cv, r2); cv.drawRoundRect(r2, 16, 16, paint(OUTL, stroke=3))
    checker(cv, r3); cv.drawRoundRect(r3, 16, 16, paint(OUTL, stroke=3))
    cv.drawOval(skia.Rect.MakeXYWH(2760, 1385, 60, 36), paint('#ffe14a')); cv.drawOval(skia.Rect.MakeXYWH(2760, 1385, 60, 36), paint(OUTL, stroke=2.5))
    for r_, n in ((r1, "A  幾何柄（基本）"), (r2, "B  ポップ柄"), (r3, "C  チェック＋リボン")): text(cv, n, r_.centerX(), 1550, 21, '#2d2540')
    panel(cv, 2100, 1586, 860, 290, "NOTES  デザインメモ")
    notes = ["・黒×茶（ブラック＆タン）の長毛。耳と胸の毛はふわっと波打つ", "・眉のタン点と大きな茶色の瞳で、表情が読み取りやすい", "・後ろ足はカートに預け、前足で力強く進む（走る時はしっぽ・耳が揺れる）", "・カートは銀フレーム＋黄緑パッド、スマイルシールがトレードマーク", "・赤いハーネスとピンクのリードは常に装着。服は日替わりで着替える"]
    for i, n in enumerate(notes): text(cv, n, 2124, 1672 + i * 40, 22, '#2d2540', align='left')
    s.makeImageSnapshot().save(path, skia.kPNG)

if __name__ == '__main__':
    sheet('/home/user/my-project/charsheet/protagonist_character_sheet.png')
