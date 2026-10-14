# canli-toplanti-metne-donusum 🎙️📝

**EN | Live Turkish transcription for meetings & online lectures — 100% local, Whisper, copy or export to Word.**
**TR | Canlı Türkçe metne dönüştürme — toplantı ve online dersler için, tamamen yerel, Whisper ile, kopyala veya Word'e aktar.**

Your Zoom / Meet / Teams lecture is running and you want the notes without typing?
Online transcription services want uploads and subscriptions. This one listens to
the sound your computer is playing, writes Turkish text live in your browser, and
never sends audio anywhere.

Zoom / Meet / Teams dersini dinlerken not tutmak mı istiyorsun? Online servisler
ses yüklemeni ve abonelik istiyor. Bu uygulama bilgisayarın çaldığı sesi dinler,
Türkçe metni tarayıcında canlı yazar ve sesi hiçbir yere göndermez.

```
[00:12] Bugün regresyon modellerinde özellik seçimini inceleyeceğiz.
[00:19] L1 düzenlileştirme bazı katsayıları sıfıra çeker.
[00:27] Bu yüzden seyrek modeller elde ederiz.
```

---

## 🇬🇧 English

### Why?

- Online transcription = **uploading your lecture audio to strangers' servers**.
- Phone recorders only work for the room, not for the video call playing on your PC.
- This app captures **system audio** (loopback), so whatever your speakers play gets transcribed.

### Features

| Feature | What it does |
|---|---|
| Live transcript | Text appears in the browser as you listen, with timestamps |
| ▶ Start / ■ Stop | Control recording from the panel |
| Copy | Copies the full transcript to the clipboard |
| Word export | Downloads the transcript as a Word document |
| Turkish | Transcribes Turkish (`language=tr`) with a course-context prompt |
| 100% local | Whisper runs on your machine; no audio or text leaves it |

### Install

Windows, Python 3.10+ (tested on 3.14):

```bash
pip install faster-whisper soundcard numpy flask python-docx
```

The first run downloads the Whisper model (`large-v3-turbo`, ~1.6 GB) once.

### Usage

```bash
python app.py
```

Then open **http://localhost:5000**, play the lecture, and press **▶ Start**.
Press **■ Stop** when it ends, then **Copy** or **Export**.

### Settings

Edit the constants at the top of [app.py](app.py):

| Setting | Default | Meaning |
|---|---|---|
| `MODEL_SIZE` | `large-v3-turbo` | Whisper model; `small` is faster but less accurate in Turkish |
| `LANGUAGE` | `tr` | Transcription language |
| `WINDOW_SEC` | `10.0` | Audio chunk sent to Whisper; longer = better sentences, more delay |
| `BEAM_SIZE` | `5` | Decoding beam; higher = more accurate, slower |
| `INITIAL_PROMPT` | course/meeting context | Vocabulary hint for Turkish terms |

### Limitations

- **Latency:** on CPU, text appears a few seconds after it is spoken (about the window length plus processing).
- **Only system audio:** your own microphone (questions you ask) is not transcribed.
- **Windows-tested:** loopback capture uses `soundcard`; other OSes are untested.
- **Accuracy:** tested with a synthetic TTS sample and live loopback audio; check it against a real lecture before relying on it.

---

## 🇹🇷 Türkçe

### Neden?

- Online transkript servisleri = **ders sesini yabancı sunuculara yüklemek**.
- Telefon kaydı yalnızca odayı duyar; bilgisayarda çalan video toplantıyı duymaz.
- Bu uygulama **sistem sesini** (loopback) yakalar; hoparlörden çalan her şey yazılır.

### Özellikler

| Özellik | Ne yapar |
|---|---|
| Canlı transkript | Dinlerken metin tarayıcıda zaman damgalarıyla belirir |
| ▶ Başlat / ■ Stop | Kaydı panelden yönetir |
| Copy | Tüm metni panoya kopyalar |
| Word dışa aktarma | Metni Word belgesi olarak indirir |
| Türkçe | `language=tr` ile, ders bağlamı ipucuyla çevirir |
| %100 yerel | Whisper kendi bilgisayarında çalışır; ses ya da metin dışarı çıkmaz |

### Kurulum

Windows, Python 3.10+ (3.14 ile test edildi):

```bash
pip install faster-whisper soundcard numpy flask python-docx
```

İlk çalıştırmada Whisper modeli (`large-v3-turbo`, ~1,6 GB) bir kez indirilir.

### Kullanım

```bash
python app.py
```

Ardından **http://localhost:5000** adresini aç, dersi oynat ve **▶ Başlat**'a bas.
Ders bitince **■ Stop**, sonra **Copy** veya **Export**.

### Ayarlar

[app.py](app.py) dosyasının başındaki sabitleri düzenleyebilirsin (yukarıdaki tablo).

### Sınırlar

- **Gecikme:** CPU'da metin, konuşulduktan birkaç saniye sonra belirir.
- **Yalnızca sistem sesi:** kendi mikrofonun (sorduğun sorular) yazılmaz.
- **Test:** Windows üzerinde test edildi; diğer işletim sistemleri test edilmedi.
- **Doğruluk:** Sentetik ses ve canlı loopback ile test edildi. Gerçek bir derste kontrol etmeden güvenme.
