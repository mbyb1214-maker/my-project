"""Small skia helpers shared by the renderer."""
import skia, math, numpy as np
W, H = 1280, 720
FONT = skia.Typeface.MakeFromFile('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf')

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, t): return a + (b - a) * t
def sstep(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else (1.0 if x >= b else 0.0)
    return t * t * (3 - 2 * t)
def easeout(t): t = clamp(t); return 1 - (1 - t) ** 3
def easeinout(t): t = clamp(t); return 0.5 - 0.5 * math.cos(math.pi * t)
def easeback(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def C(h, a=1.0):
    r, g, b = hexrgb(h) if isinstance(h, str) else h
    return skia.ColorSetARGB(int(clamp(a) * 255), r, g, b)
def mix(h1, h2, t):
    a, b = hexrgb(h1), hexrgb(h2)
    return tuple(int(lerp(a[i], b[i], clamp(t))) for i in range(3))

def paint(color=None, a=1.0, stroke=0, blur=0, blend=None, shader=None, cap=True, join=True):
    p = skia.Paint(AntiAlias=True)
    if shader is not None: p.setShader(shader)
    elif color is not None: p.setColor(C(color, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        if cap: p.setStrokeCap(skia.Paint.kRound_Cap)
        if join: p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend == 'plus': p.setBlendMode(skia.BlendMode.kPlus)
    elif blend == 'screen': p.setBlendMode(skia.BlendMode.kScreen)
    return p

def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [C(c[0], c[1]) if isinstance(c, tuple) and len(c) == 2 and not isinstance(c[0], int) else C(c) for c in cols], pos)
def rad(cx, cy, r, cols, pos=None):
    return skia.GradientShader.MakeRadial((cx, cy), max(r, 0.01), [C(c[0], c[1]) if isinstance(c, tuple) and len(c) == 2 and not isinstance(c[0], int) else C(c) for c in cols], pos)

def glow(cv, x, y, r, color, a=1.0, core=0.0):
    """additive soft glow"""
    cols = [(color, a), (color, a * 0.35), (color, 0.0)]
    cv.drawCircle(x, y, r, paint(shader=rad(x, y, r, cols, [0, 0.35, 1]), blend='plus'))
    if core > 0:
        cv.drawCircle(x, y, r * core, paint('#ffffff', min(1, a), blend='plus'))

def sparkle(cv, x, y, r, color='#ffffff', a=1.0, rot=0.0):
    """4-point twinkle"""
    p = skia.Path()
    for i in range(8):
        ang = rot + i * math.pi / 4; rr = r if i % 2 == 0 else r * 0.16
        px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
        (p.moveTo if i == 0 else p.lineTo)(px, py)
    p.close()
    cv.drawPath(p, paint(color, a, blend='plus'))
    cv.drawCircle(x, y, r * 0.22, paint('#ffffff', a * .9, blend='plus'))

def poly_smooth(pts, closed=True):
    """Catmull-Rom -> cubic path through pts"""
    p = skia.Path(); n = len(pts)
    if n < 3:
        p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; return p
    g = lambda i: pts[i % n] if closed else pts[max(0, min(n - 1, i))]
    p.moveTo(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1, p2, p3 = g(i - 1), g(i), g(i + 1), g(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    if closed: p.close()
    return p

def limb(cv, pts, w, color, a=1.0):
    p = poly_smooth(pts, closed=False)
    cv.drawPath(p, paint(color, a, stroke=w))

def text(cv, s, x, y, size, color='#ffffff', a=1.0, align='center', blur=0, blend=None, spacing=0):
    f = skia.Font(FONT, size)
    if spacing:
        total = sum(f.measureText(c) + spacing for c in s) - spacing
        cx = x - total / 2 if align == 'center' else x
        for c in s:
            cv.drawString(c, cx, y, f, paint(color, a, blur=blur, blend=blend)); cx += f.measureText(c) + spacing
        return
    w = f.measureText(s)
    ox = x - w / 2 if align == 'center' else x
    cv.drawString(s, ox, y, f, paint(color, a, blur=blur, blend=blend))
    return w

def hnoise(i, s=0):
    return (math.sin(i * 127.1 + s * 311.7) * 43758.5453) % 1.0
