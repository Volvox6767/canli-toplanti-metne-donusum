# -*- coding: utf-8 -*-
"""Bagimsiz whisper dogrulama: jfk.wav -> transkript."""
import urllib.request, sys, time

wav_path = "jfk.wav"
try:
    open(wav_path, "rb").close()
except FileNotFoundError:
    print("[dl] jfk.wav indiriliyor...")
    urllib.request.urlretrieve(
        "https://github.com/SYSTRAN/faster-whisper/raw/master/tests/data/jfk.wav",
        wav_path)
    print("[dl] tamam")

t0 = time.time()
from faster_whisper import WhisperModel
print("[model] yukleniyor (ilk indirme ~460 MB surebilir)...")
model = WhisperModel("small", device="cuda", compute_type="float16")
print("[model] yuklendi, sure: %.1f sn" % (time.time() - t0))

t1 = time.time()
segs, info = model.transcribe(wav_path, beam_size=1)
text = " ".join(s.text for s in segs).strip()
print("[sonuc] dil: %s, olasilik: %.2f" % (info.language, info.language_probability))
print("[sonuc] metin: %s" % text)
print("[sonuc] transcribe suresi: %.1f sn" % (time.time() - t1))
print("PASS" if len(text) > 20 else "FAIL")
