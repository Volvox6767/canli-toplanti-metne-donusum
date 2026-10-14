# -*- coding: utf-8 -*-
"""
Canli Transkript — local uygulama
Bilgisayardan çikan sesi (loopback) yakalar, Whisper ile Türkçe metne döker,
tarayıcı panelinde canlı gösterir. Copy / .docx dışa aktarma içerir.

Çalıştırma: python app.py  →  http://localhost:5000
"""
import json
import queue
import threading
import time
import datetime
import os

import numpy as np
import soundcard as sc
from flask import Flask, Response, jsonify, send_file, request, render_template
from faster_whisper import WhisperModel

# ================= AYARLAR =================
# model boyutu: "small" CPU'da iyi, "base" çok hızlı.
MODEL_SIZE = "large-v3-turbo"  # ölçüm: small/medium'dan hızlı ve Türkçede çok daha doğru
LANGUAGE = "tr"
SAMPLE_RATE = 16000
BLOCK_SEC = 1.0          # okuma bloğu
WINDOW_SEC = 10.0        # uzun pencere: cümleler ortadan kesilmesin
MIN_AUDIO_SEC = 1.2      # bundan kısa pencere atlanır
BEAM_SIZE = 5
# Whisper'a verilen Türkçe bağlam: terimleri ve noktalama stilini iyileştirir
INITIAL_PROMPT = "Bu bir Türkçe ders ve toplantı kaydıdır. Veri madenciliği, özellik seçimi, makine öğrenmesi, sınıflandırma ve kümeleme konuşulur."
# ===========================================

app = Flask(__name__)

# ---------- paylaşımlı durum ----------
SEGMENTS = []            # [{"time": "...", "text": "..."}]
LOCK = threading.Lock()
RUNNING = False
THREAD = None
STOP_EV = threading.Event()
START_TS = None

MODEL = None

def _cuda_usable(model) -> bool:
    """CUDA gerçekten çalışıyor mu? Gerçek sinyal (sentetik dalga) transkribe ederek test et.
    Sessiz pencere VAD'dan geçip encode'a ulaşmadığı için yanlış pozitif verirdi.
    """
    try:
        t = np.linspace(0, 1.0, SAMPLE_RATE, dtype=np.float32)
        tone = (0.25 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
        list(model.transcribe(tone, language=LANGUAGE, beam_size=1, vad_filter=False))
        return True
    except Exception as e:
        print(f"[model] CUDA testi başarısız: {e}")
        return False


def get_model():
    global MODEL
    if MODEL is None:
        # NOT: bu kurulumda Python 3.14 + ctranslate2 cublas DLL çakışması nedeniyle
        # CUDA güvenilir değil; CPU int8 deterministik ve yeterince hızlı.
        MODEL = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=12)
        print(f"[model] {MODEL_SIZE} CPU int8 OK")
    return MODEL


def find_loopback():
    """Sistemin AKTİF varsayılan çıkışının loopback'ini bul.
    Önce gerçek default speaker adını bul, eşleşen loopback'i seç.
    """
    mics = sc.all_microphones(include_loopback=True)
    loopbacks = [m for m in mics if m.isloopback]
    try:
        default_name = sc.default_speaker().name
        # isim taban eşleşme: "Kulaklık (2- Realtek Audio)" -> loopback aynı gövde
        for m in loopbacks:
            base = m.name.split("(")[-1].strip(" ")
            if base and base in default_name:
                return m
    except Exception:
        pass
    if loopbacks:
        return loopbacks[0]
    raise RuntimeError("Loopback cihaz bulunamadı")


def transcription_loop():
    global RUNNING, START_TS
    model = get_model()
    loop_mic = find_loopback()
    print(f"[ses] {loop_mic.name}")

    q = queue.Queue()
    STOP_EV.clear()

    def recorder():
        with loop_mic.recorder(samplerate=SAMPLE_RATE) as rec:
            n = int(SAMPLE_RATE * BLOCK_SEC)
            while not STOP_EV.is_set():
                data = rec.record(numframes=n)          # (n, ch)
                q.put(data)

    rec_thread = threading.Thread(target=recorder, daemon=True)
    rec_thread.start()

    buf = []
    buf_start = None
    while not STOP_EV.is_set():
        try:
            data = q.get(timeout=0.5)
        except queue.Empty:
            continue
        if buf_start is None:
            buf_start = datetime.datetime.now().strftime("%H:%M:%S")
        mono = data.astype(np.float32)
        buf.append(mono.mean(axis=1) if mono.ndim > 1 else mono)
        dur = sum(len(b) for b in buf) / SAMPLE_RATE
        if dur < WINDOW_SEC:
            continue

        audio = np.concatenate(buf)
        buf.clear()
        start_label = buf_start; buf_start = None

        if dur < MIN_AUDIO_SEC or float(np.abs(audio).max()) < 0.003:
            continue   # sessiz pencere

        try:
            segments, _ = model.transcribe(
                audio, language=LANGUAGE, beam_size=BEAM_SIZE,
                vad_filter=True, condition_on_previous_text=False,
                initial_prompt=INITIAL_PROMPT,
            )
            for seg in segments:
                text = (seg.text or "").strip()
                if not text:
                    continue
                with LOCK:
                    SEGMENTS.append({"time": start_label, "text": text})
                    if len(SEGMENTS) > 4000:
                        del SEGMENTS[:len(SEGMENTS) - 4000]
        except Exception as e:
            print("[whisper hata]", repr(e)[:200])

    RUNNING = False


def start():
    global RUNNING, THREAD, START_TS
    if RUNNING:
        return False
    with LOCK:
        SEGMENTS.clear()
    RUNNING = True
    START_TS = datetime.datetime.now()
    THREAD = threading.Thread(target=transcription_loop, daemon=True)
    THREAD.start()
    return True


# ---------- Flask ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/events")
def events():
    def gen():
        last = 0
        while True:
            with LOCK:
                n = len(SEGMENTS)
            if n > last:
                with LOCK:
                    items = SEGMENTS[last:]
                last = n
                yield "data: " + json.dumps({'items': items}, ensure_ascii=False) + "\n\n"
            else:
                yield ": keepalive\n\n"
            time.sleep(1.0)
    return Response(gen(), mimetype="text/event-stream")


@app.route("/api/start", methods=["POST"])
def api_start():
    ok = start()
    return jsonify({"started": ok})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    global RUNNING
    STOP_EV.set()
    RUNNING = False
    return jsonify({"stopped": True})


@app.route("/api/status")
def api_status():
    with LOCK:
        n = len(SEGMENTS)
    return jsonify({"running": RUNNING, "count": n})


@app.route("/api/clear", methods=["POST"])
def api_clear():
    with LOCK:
        SEGMENTS.clear()
    return jsonify({"cleared": True})


@app.route("/api/text")
def api_text():
    with LOCK:
        lines = [f"[{s['time']}] {s['text']}" for s in SEGMENTS]
    return Response("\n".join(lines), mimetype="text/plain; charset=utf-8")


@app.route("/api/docx")
def api_docx():
    """Veri Madenciliği ders notu gibi .doc (Word) çıktısı üretir."""
    path = export_docx()
    return send_file(path, as_attachment=True,
                     download_name=f"transkript_{datetime.datetime.now():%Y%m%d_%H%M%S}.doc")


def export_docx():
    try:
        package_dir = os.path.dirname(__file__)
        from docx import Document
        doc = Document()
        with LOCK:
            for s in SEGMENTS:
                p = doc.add_paragraph(f"[{s['time']}] {s['text']}")
        path = os.path.join(package_dir, "transkript_export.docx")
        doc.save(path)
        return path
    except ImportError:
        # python-docx yoksa HTML-tabanlı .doc yedek
        with LOCK:
            rows = "".join(f"<p>[{s['time']}] {s['text']}</p>" for s in SEGMENTS)
        html = f"<html><head><meta charset='utf-8'></head><body>{rows}</body></html>"
        path = os.path.join(os.path.dirname(__file__), "transkript_export.doc")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path


if __name__ == "__main__":
    print("=" * 50)
    print("  Canli Transkript  ->  http://localhost:5000")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
