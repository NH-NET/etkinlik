"""Ünite metinlerinden içindekiler sayfalı, düzenli bir PDF ders notu üretir.

Kullanım: python3 araclar/pdf_olustur.py
Gerekenler: pip install reportlab ; Liberation veya DejaVu yazı tipleri
"""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import KOK, ayristir, uniteleri_bul  # noqa: E402

CIKTI = KOK / "cikti" / "KPSS-Tarih-Konu-Anlatimi.pdf"

LACIVERT = colors.HexColor("#1F3A5F")
KIRMIZI = colors.HexColor("#A23B2A")
ALTIN = colors.HexColor("#C9962B")
NOT_ZEMIN = colors.HexColor("#FBF3E2")
TABLO_ZEMIN = colors.HexColor("#EEF2F7")
GRI = colors.HexColor("#5B6573")


def yazi_tiplerini_kaydet():
    adaylar = [
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
    ]
    for normal, kalin, egik in adaylar:
        if Path(normal).exists():
            pdfmetrics.registerFont(TTFont("Govde", normal))
            pdfmetrics.registerFont(TTFont("Govde-Kalin", kalin))
            pdfmetrics.registerFont(TTFont("Govde-Egik", egik))
            pdfmetrics.registerFontFamily("Govde", normal="Govde", bold="Govde-Kalin",
                                          italic="Govde-Egik", boldItalic="Govde-Kalin")
            return
    raise SystemExit("Türkçe karakter destekli yazı tipi bulunamadı")


yazi_tiplerini_kaydet()

S = {
    "govde": ParagraphStyle("govde", fontName="Govde", fontSize=10.5, leading=15.2,
                            alignment=TA_JUSTIFY, spaceAfter=6),
    "madde": ParagraphStyle("madde", fontName="Govde", fontSize=10.5, leading=14.6,
                            alignment=TA_JUSTIFY, leftIndent=14, bulletIndent=3, spaceAfter=2.5),
    "h2": ParagraphStyle("h2", fontName="Govde-Kalin", fontSize=14, leading=18, textColor=LACIVERT,
                         spaceBefore=12, spaceAfter=2),
    "h3": ParagraphStyle("h3", fontName="Govde-Kalin", fontSize=11.5, leading=15, textColor=KIRMIZI,
                         spaceBefore=8, spaceAfter=4),
    "h4": ParagraphStyle("h4", fontName="Govde-Kalin", fontSize=10.5, leading=14, textColor=LACIVERT,
                         spaceBefore=5, spaceAfter=3),
    "not": ParagraphStyle("not", fontName="Govde", fontSize=10, leading=14, alignment=TA_JUSTIFY),
    "not_baslik": ParagraphStyle("not_baslik", fontName="Govde-Kalin", fontSize=8.5, leading=11,
                                 textColor=KIRMIZI, spaceAfter=2),
    "tablo": ParagraphStyle("tablo", fontName="Govde", fontSize=9.5, leading=12.5),
    "tablo_bas": ParagraphStyle("tablo_bas", fontName="Govde-Kalin", fontSize=9.5, leading=12.5,
                                textColor=colors.white),
    "unite_no": ParagraphStyle("unite_no", fontName="Govde-Kalin", fontSize=11, leading=14,
                               textColor=ALTIN),
    "unite": ParagraphStyle("unite", fontName="Govde-Kalin", fontSize=21, leading=26,
                            textColor=colors.white),
    "unite_ses": ParagraphStyle("unite_ses", fontName="Govde-Egik", fontSize=9, leading=12,
                                textColor=colors.HexColor("#D6DEE8")),
    "icindekiler": ParagraphStyle("icindekiler", fontName="Govde-Kalin", fontSize=20, leading=26,
                                  textColor=LACIVERT, spaceAfter=14),
}

TOC_STILLERI = [
    ParagraphStyle("toc0", fontName="Govde-Kalin", fontSize=10.5, leading=14, textColor=LACIVERT,
                   spaceBefore=6, leftIndent=0),
    ParagraphStyle("toc1", fontName="Govde", fontSize=8.8, leading=11.2, textColor=GRI, leftIndent=16),
]


def satir_ici(metin):
    t = escape(metin)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


class Belge(BaseDocTemplate):
    def __init__(self, yol):
        super().__init__(str(yol), pagesize=A4, leftMargin=2.1 * cm, rightMargin=2.1 * cm,
                         topMargin=2.2 * cm, bottomMargin=2 * cm, title="KPSS Tarih Konu Anlatımı",
                         author="KPSS Tarih Sesli Anlatım", subject="KPSS Genel Kültür - Tarih")
        cerceve = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="ana")
        self.addPageTemplates([
            PageTemplate(id="kapak", frames=[cerceve], onPage=self.kapak_ciz),
            PageTemplate(id="icerik", frames=[cerceve], onPageEnd=self.sayfa_susle),
        ])
        self.aktif_unite = ""

    def beforeDocument(self):
        self.aktif_unite = ""

    def afterFlowable(self, f):
        seviye = getattr(f, "toc_seviye", None)
        if seviye is None:
            return
        anahtar = f"bolum-{id(f)}"
        self.canv.bookmarkPage(anahtar)
        self.canv.addOutlineEntry(f.toc_metin, anahtar, level=seviye, closed=seviye == 0)
        self.notify("TOCEntry", (seviye, f.toc_metin, self.page, anahtar))
        if seviye == 0:
            self.aktif_unite = f.toc_metin

    def kapak_ciz(self, canv, doc):
        w, h = A4
        canv.saveState()
        canv.setFillColor(LACIVERT)
        canv.rect(0, 0, w, h, fill=1, stroke=0)
        canv.setFillColor(ALTIN)
        canv.rect(0, h * 0.42, w, 0.25 * cm, fill=1, stroke=0)
        canv.setFillColor(colors.white)
        canv.setFont("Govde-Kalin", 46)
        canv.drawString(2.4 * cm, h * 0.62, "KPSS TARİH")
        canv.setFont("Govde", 22)
        canv.drawString(2.4 * cm, h * 0.62 - 1.3 * cm, "Konu Anlatımı")
        canv.setFillColor(colors.HexColor("#D6DEE8"))
        canv.setFont("Govde", 12)
        canv.drawString(2.4 * cm, h * 0.62 - 2.5 * cm,
                        "İslamiyet öncesi Türk tarihinden çağdaş Türk ve dünya tarihine")
        canv.drawString(2.4 * cm, h * 0.62 - 3.15 * cm, "tüm üniteler, KPSS notları ve kronolojilerle")
        canv.setFillColor(ALTIN)
        canv.setFont("Govde-Kalin", 11)
        canv.drawString(2.4 * cm, h * 0.42 - 1.3 * cm, "SESLİ ANLATIM EŞLİKLİ")
        canv.setFillColor(colors.white)
        canv.setFont("Govde", 10.5)
        canv.drawString(2.4 * cm, h * 0.42 - 2.0 * cm,
                        "Her ünitenin MP3 dosyası bu metni baştan sona okur; dinlerken buradan takip edebilirsiniz.")
        canv.restoreState()

    def sayfa_susle(self, canv, doc):
        w, h = A4
        canv.saveState()
        canv.setStrokeColor(ALTIN)
        canv.setLineWidth(0.8)
        canv.line(self.leftMargin, h - 1.45 * cm, w - self.rightMargin, h - 1.45 * cm)
        canv.setFont("Govde-Kalin", 8.5)
        canv.setFillColor(LACIVERT)
        canv.drawString(self.leftMargin, h - 1.25 * cm, "KPSS TARİH · KONU ANLATIMI")
        canv.setFont("Govde", 8.5)
        canv.setFillColor(GRI)
        canv.drawRightString(w - self.rightMargin, h - 1.25 * cm, self.aktif_unite)
        canv.drawCentredString(w / 2, 1.1 * cm, str(doc.page))
        canv.restoreState()


def isaretle(flowable, metin, seviye):
    flowable.toc_metin = metin
    flowable.toc_seviye = seviye
    return flowable


def unite_bandi(no, baslik, mp3_adi, genislik):
    icerik = [
        Paragraph(f"ÜNİTE {int(no)}", S["unite_no"]),
        Spacer(1, 3),
        Paragraph(escape(baslik), S["unite"]),
        Spacer(1, 6),
        Paragraph(f"Ses dosyası: mp3/{escape(mp3_adi)}", S["unite_ses"]),
    ]
    t = Table([[icerik]], colWidths=[genislik])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LACIVERT),
        ("LINEBELOW", (0, 0), (-1, -1), 3, ALTIN),
        ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 16), ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
    ]))
    return t


def not_kutusu(metin, genislik):
    t = Table([[[Paragraph("KPSS NOTU", S["not_baslik"]), Paragraph(satir_ici(metin), S["not"])]]],
              colWidths=[genislik])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NOT_ZEMIN),
        ("LINEBEFORE", (0, 0), (0, -1), 3.5, ALTIN),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def tablo(satirlar, genislik):
    bas, *govde = satirlar
    veri = [[Paragraph(satir_ici(h), S["tablo_bas"]) for h in bas]]
    veri += [[Paragraph(satir_ici(h), S["tablo"]) for h in r] for r in govde]
    ilk = 3.0 * cm if len(bas) == 2 else genislik / len(bas)
    sutunlar = [ilk] + [(genislik - ilk) / (len(bas) - 1)] * (len(bas) - 1)
    t = Table(veri, colWidths=sutunlar, repeatRows=1)
    stil = [
        ("BACKGROUND", (0, 0), (-1, 0), LACIVERT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2DE")),
    ]
    for i in range(2, len(veri), 2):
        stil.append(("BACKGROUND", (0, i), (-1, i), TABLO_ZEMIN))
    t.setStyle(TableStyle(stil))
    return t


def main():
    doc = Belge(CIKTI)
    g = doc.width
    hikaye = [Spacer(1, 1), NextPageTemplate("icerik"), PageBreak()]

    toc = TableOfContents(levelStyles=TOC_STILLERI, dotsMinLevel=0)
    hikaye += [Paragraph("İçindekiler", S["icindekiler"]), toc, PageBreak()]

    for yol in uniteleri_bul():
        no = yol.name[:2]
        for tur, icerik in ayristir(yol):
            if tur == "h1":
                bant = unite_bandi(no, icerik, f"{yol.stem}.mp3", g)
                hikaye += [isaretle(bant, f"{int(no)}. {icerik}", 0), Spacer(1, 14)]
            elif tur == "h2":
                baslik = isaretle(Paragraph(satir_ici(icerik), S["h2"]), icerik, 1)
                cizgi = Table([[""]], colWidths=[g], rowHeights=[1.2])
                cizgi.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ALTIN)]))
                hikaye += [CondPageBreak(3.2 * cm), baslik, cizgi, Spacer(1, 6)]
            elif tur == "h3":
                hikaye += [CondPageBreak(2.4 * cm), Paragraph(satir_ici(icerik), S["h3"])]
            elif tur == "h4":
                hikaye += [CondPageBreak(2 * cm), Paragraph(satir_ici(icerik), S["h4"])]
            elif tur == "p":
                hikaye.append(Paragraph(satir_ici(icerik), S["govde"]))
            elif tur == "ul":
                for m in icerik:
                    hikaye.append(Paragraph(satir_ici(m), S["madde"], bulletText="•"))
                hikaye.append(Spacer(1, 5))
            elif tur == "not":
                hikaye += [Spacer(1, 3), KeepTogether(not_kutusu(icerik, g)), Spacer(1, 9)]
            elif tur == "tablo":
                t = tablo(icerik, g)
                hikaye += [KeepTogether(t) if len(icerik) <= 10 else t, Spacer(1, 10)]
        hikaye.append(PageBreak())

    if isinstance(hikaye[-1], PageBreak):
        hikaye.pop()
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    doc.multiBuild(hikaye)
    print("PDF oluşturuldu:", CIKTI)


if __name__ == "__main__":
    main()
