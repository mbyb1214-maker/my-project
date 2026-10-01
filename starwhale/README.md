# 星くじらの夜 (Hoshikujira no Yoru)

60秒の2Dアニメーション。映像・音声・音楽・効果音のすべてをコードで生成しています(外部素材なし)。

- `voices.py`  : OpenJTalk(pyopenjtalk-plus)で日本語セリフを合成し、キャラごとに声質を加工
- `audio.py`   : 音楽(オルゴール/パッド/鯨の歌)・効果音を合成し、ダッキング付きでミックス
- `gfx.py` `bg.py` `chars.py` `scenes.py` : Skiaによるベクター描画(口パクは音声の振幅から自動生成)
- `render.py`  : 4並列でフレーム描画 → ffmpeg でMP4化

再生成: `python3 voices.py && python3 audio.py && python3 render.py`
(要: pip install pyopenjtalk-plus skia-python numpy scipy pillow / ffmpeg / libegl1)
