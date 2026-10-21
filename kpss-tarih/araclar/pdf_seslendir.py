"""Herhangi bir Türkçe PDF'in metnini çıkarıp düzenli bir PDF'e ve MP3'e çevirir.

Örnek: Scribd'den kendi indirdiğin bir ders notunu dinlemek için.
Kullanım:
    python3 araclar/pdf_seslendir.py girdi.pdf [cikti_klasoru]
Çıktılar: <ad>-duzenli.pdf ve <ad>.mp3
"""

import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdf_olustur  # noqa: E402  (yazı tiplerini kaydeder)
from ortak import cumlelere_bol, seslendirme_metni  # noqa: E402
from seslendir import HIZ, SESSIZLIK, model_hazirla, mp3_yaz  # noqa: E402


def metni_cikar(pdf):
    sonuc = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True)
    return sonuc.stdout


def paragraflara_ayir(ham):
    sayfalar = ham.split("\f")
    # Her sayfada tekrar eden üst/alt bilgi satırlarını bul
    sayac = {}
    for s in sayfalar:
        for satir in {x.strip() for x in s.splitlines() if x.strip()}:
            sayac[satir] = sayac.get(satir, 0) + 1
    tekrar = {k for k, v in sayac.items() if len(sayfalar) > 4 and v > len(sayfalar) * 0.5}

    paragraflar, gecerli = [], []
    for s in sayfalar:
        for satir in s.splitlines():
            t = re.sub(r"\s+", " ", satir).strip()
            if not t or t in tekrar or re.fullmatch(r"[-–—\s\d]+", t):
                if gecerli:
                    paragraflar.append(" ".join(gecerli))
                    gecerli = []
                continue
            if gecerli and gecerli[-1].endswith("-"):
                gecerli[-1] = gecerli[-1][:-1] + t  # satır sonu tirelemesini birleştir
            else:
                gecerli.append(t)
    if gecerli:
        paragraflar.append(" ".join(gecerli))
    return [p for p in paragraflar if len(p) > 1]


def duzenli_pdf(paragraflar, hedef, baslik):
    govde = ParagraphStyle("g", fontName="Govde", fontSize=11, leading=16, spaceAfter=7)
    bas = ParagraphStyle("b", fontName="Govde-Kalin", fontSize=13, leading=18, spaceBefore=8, spaceAfter=4,
                         textColor=pdf_olustur.LACIVERT)
    hikaye = [Paragraph(escape(baslik), pdf_olustur.S["icindekiler"]), Spacer(1, 6)]
    for p in paragraflar:
        kisa_baslik = len(p) < 70 and not p.endswith((".", ",", ";", ":"))
        hikaye.append(Paragraph(escape(p), bas if kisa_baslik else govde))
    SimpleDocTemplate(str(hedef), title=baslik).build(hikaye)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    girdi = Path(sys.argv[1])
    cikti = Path(sys.argv[2]) if len(sys.argv) > 2 else girdi.parent
    cikti.mkdir(parents=True, exist_ok=True)
    paragraflar = paragraflara_ayir(metni_cikar(girdi))
    if not paragraflar:
        raise SystemExit("PDF'te metin bulunamadı (taranmış resim olabilir).")
    duzenli_pdf(paragraflar, cikti / f"{girdi.stem}-duzenli.pdf", girdi.stem)

    tts = model_hazirla()
    parcalar = []
    for p in paragraflar:
        for c in cumlelere_bol(seslendirme_metni(p)):
            ses = tts.generate(c, sid=0, speed=HIZ)
            parcalar += [np.asarray(ses.samples, dtype=np.float32),
                         np.zeros(int(tts.sample_rate * SESSIZLIK["cumle"]), dtype=np.float32)]
        parcalar.append(np.zeros(int(tts.sample_rate * SESSIZLIK["paragraf"]), dtype=np.float32))
    mp3_yaz(np.concatenate(parcalar), tts.sample_rate, cikti / f"{girdi.stem}.mp3", girdi.stem)
    print("Hazır:", cikti / f"{girdi.stem}-duzenli.pdf", "ve", cikti / f"{girdi.stem}.mp3")


if __name__ == "__main__":
    main()
