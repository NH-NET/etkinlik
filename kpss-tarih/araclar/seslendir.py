"""Ünite metinlerini ücretsiz ve çevrimdışı Türkçe sesle (Piper / sherpa-onnx) MP3'e çevirir.

Kullanım:
    python3 araclar/seslendir.py              # tüm üniteler + tek parça birleşik MP3
    python3 araclar/seslendir.py 03 07        # yalnızca seçilen üniteler
Gerekenler: pip install sherpa-onnx soundfile numpy ; ffmpeg
"""

import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import sherpa_onnx
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import KOK, ayristir, cumlelere_bol, seslendirme_metni, uniteleri_bul  # noqa: E402

SES = "tr_TR-dfki-medium"
MODEL_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-{SES}.tar.bz2"
MODEL_DIZINI = KOK / ".modeller"
MP3_DIZINI = KOK / "cikti" / "mp3"
HIZ = 1.1
ALBUM = "KPSS Tarih Konu Anlatımı"

SESSIZLIK = {"cumle": 0.30, "madde": 0.45, "paragraf": 0.70, "baslik": 0.90, "unite": 1.50}


def model_hazirla():
    hedef = MODEL_DIZINI / f"vits-piper-{SES}"
    if not (hedef / f"{SES}.onnx").exists():
        MODEL_DIZINI.mkdir(parents=True, exist_ok=True)
        arsiv = MODEL_DIZINI / "model.tar.bz2"
        print("Ses modeli indiriliyor:", MODEL_URL)
        urllib.request.urlretrieve(MODEL_URL, arsiv)
        with tarfile.open(arsiv) as t:
            t.extractall(MODEL_DIZINI)
        arsiv.unlink()
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(hedef / f"{SES}.onnx"),
                tokens=str(hedef / "tokens.txt"),
                data_dir=str(hedef / "espeak-ng-data"),
            ),
            num_threads=4,
        )
    )
    return sherpa_onnx.OfflineTts(cfg)


def okuma_plani(bloklar, unite_no):
    """Blokları (okunacak metin, sonrasındaki sessizlik) çiftlerine çevirir."""
    plan = []

    def ekle(metin, son_sessizlik, ara_sessizlik=SESSIZLIK["cumle"]):
        cumleler = cumlelere_bol(seslendirme_metni(metin))
        for i, c in enumerate(cumleler):
            plan.append((c, son_sessizlik if i == len(cumleler) - 1 else ara_sessizlik))

    def nokta(metin):
        metin = metin.rstrip()
        return metin if metin.endswith((".", "!", "?", ":")) else metin + "."

    for tur, icerik in bloklar:
        if tur == "h1":
            ekle(f"Ünite {int(unite_no)}: {icerik}.", SESSIZLIK["unite"])
        elif tur in ("h2", "h3", "h4"):
            ekle(icerik.rstrip(".") + ".", SESSIZLIK["baslik"])
        elif tur == "p":
            ekle(icerik, SESSIZLIK["paragraf"])
        elif tur == "ul":
            for m in icerik:
                ekle(nokta(m), SESSIZLIK["madde"])
            plan[-1] = (plan[-1][0], SESSIZLIK["paragraf"])
        elif tur == "not":
            ekle("KPSS notu.", SESSIZLIK["cumle"])
            ekle(icerik, SESSIZLIK["paragraf"])
        elif tur == "tablo":
            for satir in icerik[1:]:  # ilk satır sütun başlıklarıdır
                ekle(": ".join(h for h in satir if h).rstrip(".") + ".", SESSIZLIK["madde"])
            plan[-1] = (plan[-1][0], SESSIZLIK["paragraf"])
    return plan


def seslendir(tts, plan):
    sr = tts.sample_rate
    parcalar = []
    for metin, sessizlik in plan:
        ses = tts.generate(metin, sid=0, speed=HIZ)
        parcalar.append(np.asarray(ses.samples, dtype=np.float32))
        parcalar.append(np.zeros(int(sr * sessizlik), dtype=np.float32))
    return np.concatenate(parcalar), sr


def mp3_yaz(ses, sr, hedef, baslik, parca_no=None):
    with tempfile.NamedTemporaryFile(suffix=".wav") as gecici:
        sf.write(gecici.name, ses, sr)
        komut = ["ffmpeg", "-y", "-loglevel", "error", "-i", gecici.name,
                 "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "1",
                 "-codec:a", "libmp3lame", "-b:a", "64k",
                 "-metadata", f"title={baslik}", "-metadata", f"album={ALBUM}",
                 "-metadata", "artist=KPSS Tarih Sesli Anlatım"]
        if parca_no:
            komut += ["-metadata", f"track={parca_no}"]
        subprocess.run(komut + [str(hedef)], check=True)


def main():
    secilen = set(sys.argv[1:])
    tts = model_hazirla()
    MP3_DIZINI.mkdir(parents=True, exist_ok=True)
    uretilen = []
    for yol in uniteleri_bul():
        no = yol.name[:2]
        if secilen and no not in secilen:
            continue
        bloklar = ayristir(yol)
        baslik = next(i for t, i in bloklar if t == "h1")
        ses, sr = seslendir(tts, okuma_plani(bloklar, no))
        hedef = MP3_DIZINI / f"{yol.stem}.mp3"
        mp3_yaz(ses, sr, hedef, f"Ünite {int(no)} - {baslik}", int(no))
        uretilen.append(hedef)
        print(f"{hedef.name}: {len(ses) / sr / 60:.1f} dakika")
    if not secilen and uretilen:
        birlestir(uretilen, KOK / "cikti" / "KPSS-Tarih-Tum-Uniteler.mp3")


def birlestir(mp3ler, hedef):
    """Ünite MP3'lerini tek dosyada birleştirir; boyutu küçük tutmak için 48 kbps ile kodlar."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt") as liste:
        liste.write("".join(f"file '{m}'\n" for m in mp3ler))
        liste.flush()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", liste.name, "-ar", "22050", "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "48k",
                        "-metadata", "title=KPSS Tarih - Tüm Üniteler", "-metadata", f"album={ALBUM}",
                        str(hedef)], check=True)
    print(f"{hedef.name} oluşturuldu")


if __name__ == "__main__":
    main()
