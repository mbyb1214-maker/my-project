import subprocess, sys, time, multiprocessing as mp, numpy as np, os
from timeline import FPS, DUR
W, H = 1280, 720
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hoshikujira_no_yoru.mp4")
MIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "mix.wav")

def work(f):
    import scenes
    return f, scenes.frame_array(f).tobytes()

if __name__ == "__main__":
    n = int(DUR * FPS)
    last = int(sys.argv[1]) if len(sys.argv) > 1 else n
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", MIX, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-tune", "animation",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with mp.Pool(4) as pool:
        for i, (f, b) in enumerate(pool.imap(work, range(last), chunksize=2)):
            p.stdin.write(b)
            if i % 48 == 0: print(f"frame {i}/{last}  {time.time()-t0:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print("done", time.time() - t0)
