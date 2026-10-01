import sys, skia, scenes
from timeline import FPS
for tt in sys.argv[1:]:
    f = int(float(tt) * FPS)
    s = scenes.render(f)
    s.makeImageSnapshot().save(f"build/p_{float(tt):05.1f}.png", skia.kPNG)
    print("saved", tt)
