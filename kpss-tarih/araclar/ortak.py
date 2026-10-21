"""Metin dosyalarını okuyan ve sesli okuma için Türkçe metni düzenleyen ortak araçlar.

Metin biçimi (metin/*.md):
    # Ünite başlığı          (dosya başına bir tane)
    ## Bölüm başlığı
    ### Alt başlık
    #### Küçük başlık
    - madde
    > KPSS notu kutusu
    | sütun 1 | sütun 2 |     (kronoloji tablosu)
    **kalın**                 (satır içi vurgu)
Boş satır paragrafları ayırır.
"""

import re
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
METIN_DIZINI = KOK / "metin"


def uniteleri_bul():
    return sorted(METIN_DIZINI.glob("[0-9][0-9]-*.md"))


def ayristir(yol):
    """Bir metin dosyasını blok listesine çevirir: (tur, icerik)."""
    bloklar = []
    paragraf, maddeler, not_satirlari, tablo = [], [], [], []

    def bosalt():
        if paragraf:
            bloklar.append(("p", " ".join(paragraf)))
            paragraf.clear()
        if maddeler:
            bloklar.append(("ul", list(maddeler)))
            maddeler.clear()
        if not_satirlari:
            bloklar.append(("not", " ".join(not_satirlari)))
            not_satirlari.clear()
        if tablo:
            bloklar.append(("tablo", list(tablo)))
            tablo.clear()

    for satir in Path(yol).read_text(encoding="utf-8").splitlines():
        s = satir.strip()
        if not s:
            bosalt()
            continue
        for on_ek, tur in (("#### ", "h4"), ("### ", "h3"), ("## ", "h2"), ("# ", "h1")):
            if s.startswith(on_ek):
                bosalt()
                bloklar.append((tur, s[len(on_ek):].strip()))
                break
        else:
            if s.startswith("- "):
                if not maddeler:
                    bosalt()
                maddeler.append(s[2:].strip())
            elif s.startswith(">"):
                if not not_satirlari:
                    bosalt()
                not_satirlari.append(s.lstrip("> ").strip())
            elif s.startswith("|"):
                if not tablo:
                    bosalt()
                tablo.append([h.strip() for h in s.strip("|").split("|")])
            elif maddeler:
                # Madde devam satırı
                maddeler[-1] += " " + s
            else:
                paragraf.append(s)
    bosalt()
    return bloklar


# ---------------------------------------------------------------------------
# Türkçe sayı okuma
# ---------------------------------------------------------------------------

BIRLER = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
SIRA = {
    "bir": "birinci", "iki": "ikinci", "üç": "üçüncü", "dört": "dördüncü",
    "beş": "beşinci", "altı": "altıncı", "yedi": "yedinci", "sekiz": "sekizinci",
    "dokuz": "dokuzuncu", "on": "onuncu", "yirmi": "yirminci", "otuz": "otuzuncu",
    "kırk": "kırkıncı", "elli": "ellinci", "altmış": "altmışıncı",
    "yetmiş": "yetmişinci", "seksen": "sekseninci", "doksan": "doksanıncı",
    "yüz": "yüzüncü", "bin": "bininci", "milyon": "milyonuncu", "milyar": "milyarıncı",
}


def _uc_basamak(n):
    y, o, b = n // 100, (n // 10) % 10, n % 10
    parca = []
    if y:
        parca.append("yüz" if y == 1 else BIRLER[y] + " yüz")
    if o:
        parca.append(ONLAR[o])
    if b:
        parca.append(BIRLER[b])
    return " ".join(parca)


def sayi_oku(n):
    if n == 0:
        return "sıfır"
    parca = []
    for deger, ad in ((10**9, "milyar"), (10**6, "milyon"), (1000, "bin")):
        grup = n // deger
        if grup:
            parca.append("bin" if (ad == "bin" and grup == 1) else _uc_basamak(grup) + " " + ad)
            n %= deger
    if n:
        parca.append(_uc_basamak(n))
    return " ".join(parca)


def sira_oku(n):
    kelimeler = sayi_oku(n).split()
    kelimeler[-1] = SIRA[kelimeler[-1]]
    return " ".join(kelimeler)


ROMA = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roma_coz(r):
    toplam, onceki = 0, 0
    for h in reversed(r):
        d = ROMA[h]
        toplam = toplam - d if d < onceki else toplam + d
        onceki = max(onceki, d)
    return toplam


KISALTMALAR = {
    "M.Ö.": "milattan önce",
    "M.S.": "milattan sonra",
    "Hz.": "Hazreti",
    "vb.": "ve benzeri",
    "vs.": "vesaire",
    "örn.": "örneğin",
    "yy.": "yüzyıl",
    "km²": "kilometre kare",
}

HARF_KISALTMALARI = {
    "TBMM": "Te Be Me Me",
    "ABD": "A Be De",
    "SSCB": "Es Es Ce Be",
    "KKTC": "Ke Ke Te Ce",
    "CHF": "Ce He Fe",
    "CHP": "Ce He Pe",
    "BM": "Be Me",
    "AB": "A Be",
    "AET": "A E Te",
    "AGİT": "Agit",
    "NATO": "Nato",
    "SEATO": "Seato",
    "CENTO": "Sento",
    "UNESCO": "Unesko",
    "İTC": "İ Te Ce",
    "MEB": "Me E Be",
    "ÖSYM": "Ö Es Ye Me",
    "KPSS": "Ke Pe Es Es",
    "TTK": "Te Te Ke",
    "TDK": "Te De Ke",
    "TCK": "Te Ce Ke",
    "AKPM": "A Ke Pe Me",
    "NAFTA": "Nafta",
    "OPEC": "Opek",
    "IMF": "İ Me Fe",
    "İKÖ": "İ Ke Ö",
    "İİT": "İ İ Te",
    "ECO": "Eko",
    "KEİ": "Ke E İ",
    "ASALA": "Asala",
    "PKK": "Pe Ke Ke",
    "DP": "De Pe",
    "SCF": "Se Ce Fe",
    "EOKA": "Eoka",
    "TMT": "Te Me Te",
    "TCF": "Te Ce Fe",
}


# Yabancı adların Türkçe ses modeline uygun okunuşu
SOYLENIS = {
    "Vasco da Gama": "Vasko da Gama",
    "Bartolomeu Diaz": "Bartolomeu Diyaz",
    "Martin Luther": "Martin Luter",
    "Thomsen": "Tomsen",
    "Calthorpe": "Kaltorp",
    "Lloyd George": "Loyd Corc",
    "Curzon": "Körzın",
    "Wilson": "Vilson",
    "Churchill": "Çörçil",
    "Roosevelt": "Ruzvelt",
    "Truman": "Truman",
    "Marshall": "Marşal",
    "Johnson": "Conson",
    "Eisenhower": "Ayzınhavır",
    "Kennedy": "Kenedi",
    "Pearl Harbor": "Pörl Harbır",
    "San Francisco": "San Fransisko",
    "Locarno": "Lokarno",
    "Kellogg": "Kellog",
    "Briand": "Briyan",
    "Washington": "Vaşington",
    "New York": "Nüyork",
    "Comte de Bonneval": "Kont dö Bonval",
    "Baron de Tott": "Baron dö Tot",
    "Franz Ferdinand": "Frants Ferdinand",
    "Goeben": "Goben",
    "Breslau": "Breslav",
    "Ouchy": "Uşi",
    "Saint-Germain": "Sen Jermen",
    "Saint Jean de Maurienne": "Sen Jan dö Moriyen",
    "Sykes-Picot": "Sayks Piko",
    "Neuilly": "Nöyi",
    "Versailles": "Versay",
    "Trianon": "Triyanon",
    "Sevres": "Sevr",
    "Montreux": "Montrö",
    "Brest-Litovsk": "Brest Litovsk",
    "Glasnost": "Glasnost",
    "Perestroika": "Perestroyka",
    "Helsinki": "Helsinki",
    "Dayton": "Deytın",
    "Annan": "Annan",
    "Chamberlain": "Çemberleyn",
    "Bellini": "Bellini",
    "Hasan Tahsin": "Hasan Tahsin",
    "Hiroshima": "Hiroşima",
    "Nagasaki": "Nagazaki",
}


def seslendirme_metni(metin):
    """Yazılı metni sesli okumaya uygun hâle getirir (sayılar, kısaltmalar...)."""
    t = metin.replace("**", "")
    t = t.replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("’", "'").replace("‘", "'")
    for k, v in KISALTMALAR.items():
        t = t.replace(k, v)
    for k, v in SOYLENIS.items():
        t = t.replace(k, v)
    for k, v in HARF_KISALTMALARI.items():
        t = re.sub(rf"(?<![\wÇĞİÖŞÜçğıöşü]){k}(?:'([a-zçğıöşü]+))?(?![\wÇĞİÖŞÜçğıöşü])",
                   lambda m, v=v: v + (m.group(1) or ""), t)
    # Binlik ayraçlı sayılar: 40.000 -> 40000
    t = re.sub(r"\b(\d{1,3})((?:\.\d{3})+)\b(?!\.\d)", lambda m: m.group(1) + m.group(2).replace(".", ""), t)
    # Yüzde
    t = re.sub(r"%\s?(\d+)", lambda m: "yüzde " + sayi_oku(int(m.group(1))), t)
    # Aralıklar: 1299-1453 -> 1299 ile 1453
    t = re.sub(r"(\d+)\s*[-–]\s*(\d+)", r"\1 ile \2", t)
    t = re.sub(r"\s[-–]\s", " ile ", t)
    t = re.sub(r"(?<=[^\W\d_])-(?=[^\W\d_])", " ", t)
    # Romen rakamlı sıra sayıları: II. Mahmut -> İkinci Mahmut
    def roma(m):
        s = sira_oku(roma_coz(m.group(1)))
        return s[0].upper().replace("I", "İ") + s[1:] + " "
    t = re.sub(r"\b([IVXLC]+)\.\s", roma, t)
    # Arap rakamlı sıra sayıları: 19. yüzyıl -> on dokuzuncu yüzyıl
    t = re.sub(r"\b(\d+)\.(?=\s+[\wÇĞİÖŞÜçğıöşü(])", lambda m: sira_oku(int(m.group(1))), t)
    # Ekli sayılar: 1071'de -> bin yetmiş birde
    t = re.sub(r"\b(\d+)'([a-zçğıöşü]+)", lambda m: sayi_oku(int(m.group(1))) + m.group(2), t)
    t = re.sub(r"\b(\d+)\b", lambda m: sayi_oku(int(m.group(1))), t)
    # Kesme işaretleri okunmaz: Anadolu'nun -> Anadolunun
    t = re.sub(r"(?<=[\wÇĞİÖŞÜçğıöşü])'(?=[\wçğıöşü])", "", t)
    for a, b in (("â", "a"), ("Â", "A"), ("î", "i"), ("Î", "İ"), ("û", "u"), ("Û", "U")):
        t = t.replace(a, b)
    t = t.replace("(", ", ").replace(")", ", ").replace("—", ", ").replace(" – ", ", ")
    t = t.replace("/", " ve ").replace("→", ", ").replace("&", " ve ").replace("•", ", ")
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r",\s*,+", ",", t)
    t = re.sub(r",\s*([.:;!?])", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def cumlelere_bol(metin):
    parcalar = re.split(r"(?<=[.!?:;])\s+", metin)
    return [p.strip() for p in parcalar if p.strip()]
