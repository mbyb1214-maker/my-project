"""Procedural score + sfx + mix. Everything synthesized in numpy."""
import numpy as np, json, os
from scipy.signal import fftconvolve, butter, sosfilt, lfilter
from voices import wavread, wavwrite, B, SR
from timeline import *
rng = np.random.default_rng(7)
N = int(DUR*SR); T = np.arange(N)/SR
mid = lambda m: 440*2**((m-69)/12)

def env_ad(n, a, d, sr=SR):
    t=np.arange(n)/sr; return np.minimum(t/max(a,1e-4),1)*np.exp(-t/d)
def add(buf, x, t0, pan=0.0, gain=1.0):
    i=int(t0*SR); 
    if i>=N: return
    x=x[:N-i] if i>=0 else x
    l=np.sqrt(0.5*(1-pan)); r=np.sqrt(0.5*(1+pan))
    buf[0,i:i+len(x)]+=x*gain*l; buf[1,i:i+len(x)]+=x*gain*r
def bell(f, dur, bright=1.0):
    n=int(dur*SR); t=np.arange(n)/SR
    parts=[(1,1.0,1.0),(2.0,0.35,0.6),(3.01,0.18*bright,0.35),(4.2,0.10*bright,0.2),(5.4,0.05*bright,0.12)]
    y=sum(a*np.sin(2*np.pi*f*r*t)*np.exp(-t/(dec*dur*0.45)) for r,a,dec in parts)
    return y*np.minimum(t/0.004,1)*0.5
def pad(f, dur, att=1.2, rel=1.5, bright=0.5):
    n=int((dur+rel)*SR); t=np.arange(n)/SR; y=0
    for det in (-0.0035,0,0.0035):
        ph=rng.uniform(0,6.28)
        for h,a in ((1,1),(2,0.45*bright*2),(3,0.22*bright*2),(4,0.1*bright)):
            y=y+a*np.sin(2*np.pi*f*(1+det)*h*t+ph)/3
    e=np.minimum(t/att,1)*np.where(t>dur,np.exp(-(t-dur)/(rel/4)),1)
    return y*e
def noise_sweep(n, f0, f1, q=0.9):
    x=rng.standard_normal(n); out=np.zeros(n); blk=512
    for i in range(0,n,blk):
        f=f0+(f1-f0)*i/n; f=np.clip(f,40,SR/2*0.9)
        sos=butter(2,[f*(1-0.45*q)/(SR/2),min(f*(1+0.45*q)/(SR/2),0.99)],btype="band",output="sos")
        out[i:i+blk]=sosfilt(sos,x[i:i+blk]) if i==0 else sosfilt(sos,x[i:i+blk])
    return out/np.abs(out).max()
def reverb(x, secs=2.8, wet=1.0, damp=3500):
    n=int(secs*SR); t=np.arange(n)/SR
    outs=[]
    for c in range(2):
        ir=rng.standard_normal(n)*np.exp(-t/(secs/4.2)); 
        sos=butter(1,damp/(SR/2),output="sos"); ir=sosfilt(sos,ir)
        ir[:int(0.012*SR)]*=np.linspace(0,1,int(0.012*SR)); ir/=np.sqrt((ir**2).sum())
        outs.append(fftconvolve(x[c],ir)[:N])
    return np.array(outs)*wet

chords = ["Dm9","Bbmaj7","Gm9","C7sus","Fmaj7","Am7","Bbmaj7","C","Dm","Bb","F","C","Dm","Bbmaj7","C","F","C","Dm7","Bbmaj7","Fmaj9","Fmaj9"]
C = {"Dm9":[50,53,57,60,64],"Bbmaj7":[46,53,57,62],"Gm9":[43,50,53,57,62],"C7sus":[48,53,55,58],
     "Fmaj7":[41,48,52,57],"Am7":[45,52,55,60],"C":[48,55,60,64],"Dm":[50,57,62,65],"Bb":[46,53,58,62],
     "F":[41,48,53,57,60],"Dm7":[50,57,60,64],"Fmaj9":[41,48,52,57,64]}
BAR=60/84*4
music=np.zeros((2,N))
# --- pads + bass
for b,ch in enumerate(chords):
    t0=b*BAR; notes=C[ch]
    vol = 0.5 if b<8 else (0.65 if b<13 else 0.85)
    if b>=19: vol=0.6
    for m in notes[1:]:
        add(music, pad(mid(m+12*(m<48)),BAR,att=1.0,rel=1.4)*0.05*vol, t0, pan=rng.uniform(-.5,.5))
    add(music, pad(mid(notes[0]),BAR,att=.25,rel=1.0,bright=.2)*0.11*vol, t0, 0)
# --- music box arpeggio / lead
scale_f=[65,67,69,70,72,74,76,77,79,81,84]  # F major-ish (Bb used)
step=BAR/8
for b,ch in enumerate(chords):
    notes=[m+12 for m in C[ch][1:]]; 
    dens = 0.35 if b<2 else 0.55 if b<8 else 0.9 if b<13 else 0.6 if b<19 else 0.4
    for s in range(8):
        t0=b*BAR+s*step
        if 8<=b<13 or b in (13,): pass
        if rng.random()<dens*(1.0 if s%2==0 else 0.7):
            m=notes[(s*3+b)%len(notes)]+ (12 if rng.random()<0.25 else 0)
            add(music, bell(mid(m+12),1.6)*0.075, t0, pan=rng.uniform(-.6,.6))
# lead lullaby melody, wonder -> end
mel=[(11.4,81),(12.1,84),(12.8,81),(13.5,79),(14.3,77),(15.7,79),(16.4,81),(17.1,77),(18.6,76),(19.3,77),(20.0,79),(21.5,81),(22.2,84),
     (37.2,88),(38.3,84),(39.5,81),(40.0,84),(41.0,88),(42.3,89),(43.0,91),(45.0,89),(46.5,84),(47.5,86),(49.0,84),(52.0,81),(53.2,84),
     (54.4,81),(55.4,77),(56.4,79),(57.4,81),(58.4,84),(59.0,89)]
for t0,m in mel: add(music, bell(mid(m),2.4,1.2)*0.12, t0, pan=0.15)
# rising shimmer harp on ascent
for k in range(26):
    t0=T_LIFT+k*0.5; m=[65,69,72,74,77,81,84][k%7]+12*(k//7)
    add(music, bell(mid(min(m,100)),1.2)*0.06*min(1,k/6), t0, pan=np.sin(k))
# soft kick-less pulse for ascent (heartbeat pad)
for k in range(int((T_AURORA-T_LIFT)/0.7143)):
    t0=T_LIFT+k*0.7143; n=int(.5*SR); tt=np.arange(n)/SR
    add(music,(np.sin(2*np.pi*(52+30*np.exp(-tt*30))*tt)*np.exp(-tt*9))*0.18*min(1,k/8),t0,0)
# final fade handled in master
music=music+0.55*reverb(music,3.2,1.0)

# --- whale songs (mother) ---
whale=np.zeros((2,N))
def whale_call(t0,f_a,f_b,dur,amp=1.0,pan=0.0):
    n=int(dur*SR); t=np.arange(n)/SR; u=t/dur
    f=f_a*(f_b/f_a)**(u**0.7)*(1+0.012*np.sin(2*np.pi*5.2*t))
    ph=2*np.pi*np.cumsum(f)/SR; y=0
    for h,a in ((1,1),(2,.55),(3,.3),(4,.14),(5,.07)): y=y+a*np.sin(h*ph)
    e=np.sin(np.pi*u)**1.4
    add(whale,y*e*0.11*amp,t0,pan)
whale_call(T_MOTHER-0.8,70,118,3.6,1.0,-.2)
whale_call(T_MOTHER+3.0,110,82,3.2,0.8,.2)
whale_call(T_REUNION-0.3,95,190,2.6,1.0,0)
whale_call(T_GIFT-1.0,90,140,3.0,0.7,0)
whale_call(T_AURORA-1.8,60,95,3.0,0.6,0)
# cub squeaks (non-verbal) on arrival
whale_call(T_REUNION+1.7,700,1250,0.5,0.35,.3); whale_call(T_REUNION+2.3,900,1500,0.4,0.3,-.3)
whale=whale+0.9*reverb(whale,4.5,1.0,2500)
# --- sfx ---
sfx=np.zeros((2,N))
def whoosh(t0,dur,f0,f1,amp,pan=0):
    n=int(dur*SR); x=noise_sweep(n,f0,f1)*np.sin(np.pi*np.linspace(0,1,n))**1.5; add(sfx,x*amp,t0,pan)
# meteors
for tm,p in ((T_SHOOT,-.5),(T_SHOOT+.9,.4),(T_SHOOT+1.5,-.2)): whoosh(tm,.9,5000,1500,.05,p)
# the big falling star: descending sine with sparkle + landing thud
n=int((T_LAND-T_FALL)*SR); tt=np.arange(n)/SR; u=tt/(T_LAND-T_FALL)
fq=2600*(0.22)**(u); y=np.sin(2*np.pi*np.cumsum(fq)/SR)*np.sin(np.pi*u*0.5+0.1)*0.18
add(sfx,y,T_FALL,0); whoosh(T_FALL,T_LAND-T_FALL,4000,600,.08)
nn=int(1.0*SR); t3=np.arange(nn)/SR
add(sfx,np.sin(2*np.pi*(70*np.exp(-t3*3)+35)*t3)*np.exp(-t3*5)*0.5,T_LAND,0)
for k in range(14): add(sfx,bell(mid(rng.choice([88,91,93,96,100])),1.0)*0.07,T_LAND+0.05+k*0.07,rng.uniform(-.8,.8))
# propeller whirr
n=int((T_AURORA+1-T_LIFT+1)*SR); t4=np.arange(n)/SR
amp=np.minimum(t4/1.2,1)*np.where(t4>(T_AURORA+1-T_LIFT),1,1)*np.exp(-np.maximum(t4-(T_AURORA-T_LIFT),0)*1.5)
whir=(np.sin(2*np.pi*(180+20*np.sin(t4*.5))*t4)*(0.6+0.4*np.sin(2*np.pi*34*t4))*0.5)*amp*0.06
add(sfx,whir,T_LIFT-0.5,0.1)
whoosh(T_LIFT,3.0,500,3500,.14); whoosh(T_CLOUDS-.5,3.0,2000,600,.09,-.4); whoosh(T_CLOUDS+2,4,800,2600,.07,.4)
whoosh(T_SPACE-.5,3.5,300,5200,.10)
# cloud break sparkle
for k in range(22): add(sfx,bell(mid(rng.choice([84,86,89,91,93,96])),1.2)*0.05,T_SPACE+k*0.11,rng.uniform(-.9,.9))
# reunion swell sparkles
for k in range(40): add(sfx,bell(mid(rng.choice([77,81,84,88,91,93])),1.6)*0.05*(1-k/60),T_REUNION+k*0.09,rng.uniform(-.9,.9))
# gift: star twinkle chord
for k,m in enumerate([81,84,88,91,96]): add(sfx,bell(mid(m),2.5,1.4)*0.09,T_GIFT+k*0.18,0)
# dawn birds + rooster-free ambience
for tb in (T_DAWN+0.6,T_DAWN+1.2,T_DAWN+2.9,T_DAWN+3.3):
    n=int(.22*SR); t5=np.arange(n)/SR; f=3200+900*np.sin(2*np.pi*14*t5)*np.exp(-t5*6)
    add(sfx,np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t5*10)*0.05,tb,rng.uniform(-.7,.7))
# night ambience: wind + crickets (first scene)
wind=noise_sweep(N,300,500,1.4)*0.02*(np.sin(np.pi*np.clip(T/ T_LIFT,0,1)))
add(sfx,wind,0,0)
for tc in np.arange(0,T_LIFT-2,0.17):
    if rng.random()<0.7:
        n=int(.05*SR); t6=np.arange(n)/SR
        add(sfx,np.sin(2*np.pi*4300*t6)*np.sin(np.pi*t6/0.05)*0.012*(1 if tc<T_LIFT-4 else .5),tc,rng.uniform(-.8,.8))
sfx=sfx+0.35*reverb(sfx,2.0,1.0)

# --- voices ---
meta=json.load(open(os.path.join(B,"meta.json")))
PAN={"mio":-0.2,"pom":0.25,"cub":0.1,"mom":0.0}
voice=np.zeros((2,N)); vsend=np.zeros((2,N)); voiceenv=np.zeros(N)
lip={}
for lid,start in START.items():
    x,_=wavread(os.path.join(B,lid+".wav"))
    # trim silence
    idx=np.where(np.abs(x)>0.006)[0]; x=x[idx[0]:idx[-1]+1]
    spk=meta[lid]["spk"]; x=x*(0.95 if spk!="mom" else 1.0)
    # fade
    f=int(0.01*SR); x[:f]*=np.linspace(0,1,f); x[-f:]*=np.linspace(1,0,f)
    add(voice,x,start,PAN[spk])
    send={"mio":0.18,"pom":0.12,"cub":0.35,"mom":0.9}[spk]
    add(vsend,x,start,PAN[spk],send)
    # lip sync envelope per frame (rms)
    hop=int(SR/FPS); nfr=len(x)//hop+1
    rms=np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)) if i*hop<len(x) else 0 for i in range(nfr)])
    rms=rms/(np.percentile(rms,92)+1e-9)
    lip[lid]={"spk":spk,"start":start,"end":start+len(x)/SR,"env":[round(float(min(1.2,v)),3) for v in rms]}
    print(lid,spk,round(start,2),"->",round(start+len(x)/SR,2))
    i=int(start*SR); voiceenv[i:i+len(x)]=np.maximum(voiceenv[i:i+len(x)],np.abs(x))
json.dump(lip,open(os.path.join(B,"lip.json"),"w"))
voice=voice+reverb(vsend,3.5,1.0,3000)
# ducking
sos=butter(1,4/(SR/2),output="sos"); duck=sosfilt(sos,voiceenv); duck=np.clip(duck*9,0,1)
g=1-0.45*duck
mix=(music*0.9+whale*1.0)*g+sfx*(1-0.3*duck)+voice*1.25
# master: fades, soft clip
fade=np.minimum(T/1.0,1)*np.minimum((DUR-T)/2.2,1)
mix=mix*fade
mix=np.tanh(mix*1.1)/np.tanh(1.1)
mix=mix/np.abs(mix).max()*0.92
st=np.stack([mix[0],mix[1]],1)
import wave
with wave.open(os.path.join(B,"mix.wav"),"wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st*32767).astype(np.int16).tobytes())
print("ok",st.shape, "rms",np.sqrt((st**2).mean()))
