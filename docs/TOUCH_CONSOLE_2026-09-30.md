# BM-ICC-08 — Dokunmatik konsol ve çevrimdışı haritalar

30 Eylül 2026. BİEM Radio Integrated Solution / BM-ICC-08.

## Kullanım ve uygulananlar
- Etkin kanala göre 1/2/3 sütun. Kanal düzeni tüm kanalları gösterir. Küçük ekran: dört ana menü + ☰ tüm sayfalar; ▲/▼ ve tekerlekle kartları kaydırma. Teknik ayrıntılar kart dişlisinde. 800×480 desteklenir; altı kart bu boyutta kaydırılır.
- BİEM bordo/lacivert, turuncu vurgu; kalıcı açık/koyu tema. Başlat/Durdur ve Hızlı Ayarlar üstte. Kazanç/AGC, PPM ve tarama alanları mevcut değişkenlere bağlıdır.
- RF ve PCM ses göstergeleri ayrı dBFS ölçümleridir; kalibre dBm değildir. Taşıyıcı var/ses yok: kırmızı. Çözülen ses veya yayın bekleme: yeşil. SDR yok: tüm kart gri. Durum ayrıca metinle yazılır.
- Dinle / Sustur bir kanalın tek ses akışını çalar; iki slotun sesi karıştırılmaz. Dinleme ve arşiv kaydı bağımsızdır. Gecikmiş dinleme örnekleri atılabilir; kayıt örnekleri değiştirilmez. Ses aygıtı/DSP izleme hatası kaydı durdurmaz. PCM etkinliği anlaşılır insan konuşmasının kanıtı değildir.
- Analog izleme ton/squelch kapısından sonra; TETRA izleme mevcut şifresiz ses/CC/slot doğrulamasından sonra; DMR izleme açık TEMP mono PCM dosyalarından salt okunur yapılır. DMR CC filtresi ve otomatik protokol doğrulaması korunur. Akış dosya adından fiziksel slot tahmin edilmez.
- Zarf: okunabilir mesaj sayısı, kanal adına göre mesaj arama. Ham veri satırları SMS sayılmaz. Mesaj ayrıntısını açmak okundu bilgisini kalıcı yapar.
- Arşivde tarih, kanal, ID/grup, slot, CC ve süre; seçilen satırın frekans/kaynağı ayrıntıda. Yönetici denetimi ve şifreli arşiv oynatımı korunur.

## Harita paketleri
- Yeni varsayılan: Türkiye geneli çevrimdışı yol haritası (Geofabrik Shortbread / OpenStreetMap, z0–14). Yakınlaştırma, taşıma ve şehre yaklaşma. Çizim arka planda ve eski istek iptal edilebilir. Gerçek son telsiz konumu aynı coğrafi dönüşümle işaretlenir.
- Uydu: EOX 2016 mozaiği, 2016–2017 Sentinel verisi, CC BY 4.0. Güncel görüntü değildir. Türkiye geneli z12; İstanbul, Ankara, İzmir, Konya ve Van merkezlerinde z14 için ayrı küçük parça indirmesi. Hazır kapsam ve boyutun yetkili kaydı paketin manifest.json dosyasıdır. Uydu ve yol haritası ayrıntısı aynı çözünürlükte değildir.
- data/map-packs Git dışında, kurulumdan ayrı tutulur. Önceki harita paketleri 30 Eylül temizliğinde proje dışındaki yerel arşive taşındı. Yeni yol ve uydu paketleri katman listesinden seçilir. Kullanım sırasında ağ erişimi yoktur.
- Kaynaklar: https://download.geofabrik.de/europe/turkey.html ; https://cloudless.eox.at/license-non-commercial (2016 CC BY bölümü).

## Korunan kurallar
SDR#, USB sürücüleri, kanal frekansları, PPM, eşikler, tonlar, alias ve kayıtlar korunur. 90 saniye kayıt / 2 saniye ara; TETRA sessiz taşıyıcı 20 saniye; sinyal takip ±6,5 kHz ve yeşil sapma ±2 kHz. ID/grup/slot/CC bilinmiyorsa boş bırakılır. Canlı dinleme arşiv erişim denetimini atlatmaz. Dağıtım öncesi çalışan alıcı güvenle kapatılır; yedek ve dosya hashleri tutulur.

## Doğrulama
144 donanımsız test; ruff, ty, basedpyright kontrolü başarılı. Büyüyen WAV, akış ayrımı, bayat kuyruk, çıkış hatası, mesaj okundu durumu, tema, ayarların korunması, küçük ekran düğmeleri ve harita koordinatları test edildi. Native Tk'da açık/koyu ve 800×480 görünümü incelendi. Yeni canlı dinleme için gerçek RF/hoparlör kabul testi kullanıcıyla yapılacak; simülasyon bu kabul yerine geçmez.

Windows Python 3.14 / Tcl'da aynı süreçte çok sayıda Tk kökü açılan testlerde aralıklı tk.tcl/icons.tcl başlatma hatası görüldü; başarısız koşular başarı sayılmadı. Temiz süreçle tekrar yapılan son tam kontrol 144/144 geçti. Harita verilerinin kaynak paketine yanlışlıkla girmemesi için sdist kapsamı açıkça src/docs/tests ile sınırlandı.

## Tasarım araştırması
Hytera Smart Dispatch Plus, Motorola CommandCentral AXS ve DCX9000'ın çağrı/kayıt/mesaj/harita akışları incelendi; ekranları kopyalanmadı. Desteklenmeyen PTT, telsiz gönderme veya trunk kanal takibi varmış gibi sunulmaz.
- https://www.hytera.com/en/product-new/digital-radio/dmr-system/smart-dispatch-plus.html
- https://www.motorolasolutions.com/en_us/products/dispatch/dispatch-consoles/commandcentral-axs.html
- https://www.motorolasolutions.com/en_xu/products/dispatch/dispatch-consoles/dcx9000.html
