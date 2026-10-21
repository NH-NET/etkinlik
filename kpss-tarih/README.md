# KPSS Tarih Konu Anlatımı: PDF ve Sesli Anlatım (MP3)

KPSS Genel Kültür tarih müfredatını 15 ünitede anlatan düzenli bir PDF ders notu ve bu notu baştan sona okuyan MP3 dosyaları.

Seslendirmede ücretsiz ve açık kaynak **Piper** Türkçe sesi (`tr_TR-dfki-medium`) kullanıldı. Ses, internet bağlantısı olmadan bilgisayarda üretiliyor; ElevenLabs gibi ücretli bir hizmete ya da hesaba gerek yok.

## Dosyalar

| Dosya | Açıklama |
| --- | --- |
| `cikti/KPSS-Tarih-Konu-Anlatimi.pdf` | Kapak, içindekiler, yer imleri, KPSS notu kutuları ve kronoloji tablolarıyla tüm üniteler |
| `cikti/mp3/01-...mp3` ... `15-...mp3` | Her ünitenin ayrı ses dosyası (PDF'teki metnin birebir okunuşu) |
| `metin/*.md` | Ünite metinleri (PDF de ses de buradan üretilir) |
| `araclar/` | PDF ve MP3 üreten betikler |

## Üniteler

1. İslamiyet Öncesi Türk Tarihi
2. İlk Türk-İslam Devletleri
3. Türkiye Selçuklu Devleti ve Anadolu Beylikleri
4. Osmanlı Devleti Kuruluş Dönemi (1299-1453)
5. Osmanlı Devleti Yükselme Dönemi (1453-1579)
6. Osmanlı Kültür ve Medeniyeti
7. 17. Yüzyılda Osmanlı Devleti (Duraklama)
8. 18. Yüzyılda Osmanlı Devleti (Gerileme)
9. 19. Yüzyılda Osmanlı Devleti (Dağılma)
10. 20. Yüzyıl Başlarında Osmanlı ve Birinci Dünya Savaşı
11. Kurtuluş Savaşı Hazırlık Dönemi
12. Kurtuluş Savaşı: Cepheler ve Antlaşmalar
13. Atatürk İlke ve İnkılapları
14. Atatürk Dönemi Türk Dış Politikası
15. Çağdaş Türk ve Dünya Tarihi

## Yeniden Üretmek

```bash
pip install reportlab sherpa-onnx soundfile numpy
python3 araclar/pdf_olustur.py      # PDF
python3 araclar/seslendir.py        # tüm ünitelerin MP3'leri ve birleşik tek MP3
python3 araclar/seslendir.py 05 13  # yalnızca seçilen üniteler
```

Ses modeli ilk çalıştırmada otomatik indirilir (yaklaşık 65 MB). `ffmpeg` kurulu olmalıdır.

Metinde bir düzeltme yapmak için `metin/` altındaki ilgili dosyayı değiştirip iki komutu yeniden çalıştırmak yeterli.

## Kendi PDF'ini Seslendirmek

Elindeki herhangi bir Türkçe PDF'i (örneğin kendi indirdiğin bir ders notunu) düzenli bir PDF'e ve MP3'e çevirmek için:

```bash
python3 araclar/pdf_seslendir.py ders-notu.pdf cikti/
```

PDF'in içinde seçilebilir metin olmalıdır. Taranmış resim hâlindeki PDF'ler için önce OCR gerekir.
