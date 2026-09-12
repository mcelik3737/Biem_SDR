# Tasarım prototipi doğrulaması

Tarih: **12 Eylül 2026**.

## Tamamlanan kontroller

Yerel HTML prototipi Chromium ile açıldı. Üç ana görünüm, 1366 × 768 görünümü ve kanal ayar panelinin ekran görüntüleri alındı. Operasyon, Gece konsolu, Arşiv odaklı ve dar ekran görünümü görsel olarak incelendi. Son kayıtlar ve oynatıcı için yerleşim sıkılaştırıldı.

| Kontrol | Sonuç |
|---|---|
| Başlangıçta altı kanal kartı | Geçti |
| Kanal / ID araması (1002) | Bir ilgili kanal |
| Yalnız aktif filtresi | İki örnek aktif kanal |
| Yerel sesi kapatma | İki örnek aktif kayıt durumu korunuyor |
| DMR → NFM ayar paneli | Analog squelch alanı gösteriliyor |
| Arşivde ID araması (1002) | İki örnek kayıt |
| Analog / slotsuz filtre | Üç örnek kayıt |
| Örnek veri dışındaki tarih | Açıklamalı boş sonuç |
| Kayıt seçme / oynatımı önizleme / duraklatma | Doğru örnek kayıt ve oynatıcı durumu |
| Kayıttan spektruma geçiş | Onay gösteriliyor; kayıt ve ölçüm durumları ayrılıyor |
| Ölçümden yeniden alıma geçiş | Ölçüm durumu kapanıyor |
| Tarayıcı JavaScript hataları | Yok |
| JavaScript sözdizimi ve token JSON | Geçti |
| Python paketi: `python -m uv build` | Wheel ve kaynak paketi başarıyla oluştu |

Yerel sesi kapatmanın kaydı etkilememesi ve kaynak paylaşımı kontrolleri **prototip durum modeli** üzerindedir; gerçek kayıt motoru/hardware testi değildir.

| Tarayıcı çalışma alanı | Sayfa, başlık ve ana içerikte yatay taşma |
|---|---|
| 1920 × 1080 | Yok |
| 1366 × 768 | Yok |
| 1093 × 614 | Yok |
| 911 × 512 | Yok |
| 800 × 800 | Yok |

Küçük/yüksekliği az pencerelerde içerik dikey kayar. Bazı kayıt tablolarının kendi yatay/dikey kaydırma alanı vardır. Kontrol sonuçları tablonun tüm sütunlarının her küçük ekranda aynı anda göründüğü anlamına gelmez.

## Ayrı doğrulama gerektirenler

- Tarayıcı boyutları Windows %125/%150 ölçek testinin yerine geçmez. Gerçek Tk uygulamasında Windows DPI, Segoe UI, klavye ve ekran okuyucu kontrolü yapılmalı.
- `Check-Radia.ps1` bu Linux ortamında PowerShell bulunmadığı için çalıştırılmadı. Python uygulama kaynakları bu pakette değiştirilmedi. Windows uygulama değişikliği sonrası bu kapı çalıştırılmalı.
- USB/rtl_tcp/Hytera bağlantısı, DMR ses/metadata, anlaşılır RF sesi, WAV kaydı ve gerçek oynatma bu tasarım işi kapsamında sınanmadı.
- Dalga biçimi, zaman çizelgesi, sinyal seviyesi, disk bilgisi ve tarih örnektir. Gerçek verilerle doğrulama uygulama aşamasına aittir.
- Bilinmeyen yerel proje notlarının tasarımla uyumu doğrulanmış değildir; kullanıcının belirttiği yerel not dosyası uygulamadan önce okunmalıdır.

## Ekran dosyaları

- [01-operasyon.png](previews/01-operasyon.png)
- [02-gece-konsolu.png](previews/02-gece-konsolu.png)
- [03-arsiv-odakli.png](previews/03-arsiv-odakli.png)
- [04-1366x768.png](previews/04-1366x768.png)
- [05-kanal-ayarlari.png](previews/05-kanal-ayarlari.png)

BIEM özgün PNG SHA-256: `5fb885a9283ea26dd3d319796f05fe78855c9e8d98a5ae71fa36652e74fa5493`.
