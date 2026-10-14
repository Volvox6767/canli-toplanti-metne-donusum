# -*- coding: utf-8 -*-
import sys, time, wave
import numpy as np
from faster_whisper import WhisperModel

size = sys.argv[1] if len(sys.argv) > 1 else "medium"
w = wave.open("tts_test.wav", "rb")
sr = w.getframerate(); ch = w.getnchannels()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
w.close()
if ch > 1:
    a = a.reshape(-1, ch).mean(axis=1)
if sr != 16000:
    idx = np.linspace(0, len(a) - 1, int(len(a) * 16000 / sr)).astype(int)
    a = a[idx]
print(f"audio {len(a)/16000:.1f}s")

t0 = time.time()
m = WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=12)
print(f"load {time.time()-t0:.1f}s")
for beam in (1, 5):
    t0 = time.time()
    segs, info = m.transcribe(a, language="tr", beam_size=beam, vad_filter=False,
                              condition_on_previous_text=False)
    txt = " ".join(s.text.strip() for s in segs)
    print(f"[{size} beam={beam}] {time.time()-t0:.1f}s -> {txt}")
