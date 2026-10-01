"""Japanese voice synthesis (OpenJTalk) + character voice shaping via rubberband."""
import numpy as np, subprocess, os, wave, json, pyopenjtalk
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
SR = 48000
# (id, speaker, text, speed, pitch_semitones, formant_ratio_semitones)
LINES = [
 ("l1","mio", "ねえ、ポム。今夜も、眠れないや。", 1.05),
 ("l2","pom", "だいじょうぶ。ほら、空を見て。", 1.1),
 ("l3","mio", "えっ、くじら？　星の、くじら！", 1.15),
 ("l4","cub", "きゅう、ママ、どこ？", 1.0),
 ("l5","pom", "空の群れから、はぐれたんだ。", 1.1),
 ("l6","mio", "だいじょうぶ！　ママのところまで、連れていく！", 1.2),
 ("l7","pom", "ミオ、つかまって！　行くよ！", 1.25),
 ("l8","cub", "わあ、たかい！", 1.1),
 ("l9","mio", "こわくないよ。みんな、いっしょだもん。", 1.1),
 ("l10","mom","……わたしの、かわいい子。", 0.95),
 ("l11","cub","ママーっ！", 1.1),
 ("l12","mom","ありがとう、小さな友だち。お礼に、星をひとつ、あげましょう。", 1.05),
 ("l13","mom","眠れない夜を、そっと照らす星を。", 1.0),
 ("l14","pom","おやすみ、ミオ。いい夢を。", 0.95),
]
# character shaping: (f0 shift semitones, formant shift semitones)
SHAPE = {"mio":(3.0,2.0), "pom":(8.0,4.0), "cub":(11.0,7.0), "mom":(-3.0,-2.5)}

def wavwrite(p, x, sr=SR):
    x = np.clip(x,-1,1); 
    with wave.open(p,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((x*32767).astype(np.int16).tobytes())
def wavread(p):
    with wave.open(p,"rb") as w:
        d=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float64)/32768
        return d, w.getframerate()

def make():
    meta={}
    for lid,spk,text,speed in LINES:
        f0,fm = SHAPE[spk]
        x,sr = pyopenjtalk.tts(text, speed=speed, half_tone=0.0)
        x = x/ (np.abs(x).max()+1e-9)*0.9
        raw=os.path.join(B,f"{lid}_raw.wav"); out=os.path.join(B,f"{lid}.wav")
        wavwrite(raw, x, sr)
        # pitch ratio = f0 semitones; formant preserved-shift via rubberband formant option
        pr = 2**(f0/12); fr = 2**(fm/12)/pr if False else 2**((fm-f0)/12)
        # rubberband: pitch scales f0 AND formants (without formant=preserved); use shifted formants:
        flt = f"rubberband=pitch={pr:.5f}:formant=shifted:transients=smooth"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",raw,"-af",flt+",aresample=48000",out],check=True)
        y,_=wavread(out)
        if spk=="pom":   # little robotic shimmer
            t=np.arange(len(y))/SR
            y = y*(0.78+0.22*np.sign(np.sin(2*np.pi*70*t))*0) + 0.0
            ring = y*np.sin(2*np.pi*180*t)
            y = 0.82*y+0.30*ring
        if spk=="cub":
            t=np.arange(len(y))/SR
            y = y*(1+0.18*np.sin(2*np.pi*6.5*t))   # trembling
        y = y/(np.abs(y).max()+1e-9)*0.9
        wavwrite(out,y)
        meta[lid]={"spk":spk,"dur":len(y)/SR,"text":text}
    json.dump(meta,open(os.path.join(B,"meta.json"),"w"),ensure_ascii=False,indent=1)
    return meta
if __name__=="__main__":
    m=make()
    for k,v in m.items(): print(k,v["spk"],round(v["dur"],2),v["text"])
    print("total",sum(v["dur"] for v in m.values()))
