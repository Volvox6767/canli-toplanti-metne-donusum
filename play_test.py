# -*- coding: utf-8 -*-
"""tts_test.wav dosyasini varsayilan hoparlorden calar (loopback dinleme icin)."""
import wave, numpy as np
import soundcard as sc

w = wave.open("tts_test.wav", "rb")
sr = w.getframerate()
frames = w.readframes(w.getnframes())
audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
if w.getnchannels() > 1:
    audio = audio[::w.getnchannels()]
w.close()

# sistemin gercek varsayilan cikisi (kulaklik/hoparlor fark etmez)
spk = sc.default_speaker()
print("[caliyor]", spk.name)
with spk.player(samplerate=sr) as p:
    p.play(audio)
print("[bitti]")
