# BM-ICC-08 — mini PC yapılandırması

Tarih: 22 Eylül 2026. Durum: numune/teklif önerisi; satın alınmış veya bu donanımla performansı doğrulanmış sistem değildir.

## Karar önerisi

İlk cihaz: Intel/AMD x86-64 mimarisinde endüstriyel mini PC, Intel Core i5-1235U sınıfı veya daha yüksek bir işlemci, 32 GB RAM, 1 TB SSD ve lisanslı Windows 11 Pro 64 bit. 16 GB daha düşük maliyetli başlangıç seçeneğidir; 32 GB önerisi çoklu çözücü, harita ve sonraki geliştirmeler için pay bırakır, ölçülmüş minimum gereksinim değildir. Harici ekran kartı mevcut iş yükü için satın alma şartı değildir.

İlk numuneye Linux kurarak mevcut bütün özelliklerin aynen çalışacağını varsaymıyoruz. Donanım Linux destekli seçilebilir; uygulamanın Linux uyarlaması ayrı iştir.

## Yerel kodda doğrulanan işletim sistemi bağımlılıkları

- `src/biem_radia/protection.py`: Windows DPAPI; Windows dışında hata verir. Kullanıcıya bağlı korumalı kayıtlar yeni bilgisayara yalnız dosya kopyasıyla taşınmış sayılmaz. Yetkili aktarım/anahtar kurtarma planı ve eski PC'de örnek kayıt açılması korunmalıdır.
- `src/biem_radia/tetra.py` ve `Setup-TETRA.ps1`: TetraBridge.exe, Windows .NET Framework derlemesi ve SDR# DLL'leri; mevcut köprü Windows'a bağlıdır.
- `src/biem_radia/dmr.py` ve `Setup-DMR.ps1`: şu anki adaptör DSD-FME Windows EXE paket yoluna göre hazırlanmıştır. Linux çözücüsünü derlemek, tek başına adaptörün tamamen taşınması değildir.
- Yönetici erişimi, cihaz erişimi ve paketleme de hedef işletim sisteminde yeniden doğrulanmalıdır.

Linux için x86-64 Ubuntu LTS, ancak çözücü/koruma/izinler ve paketleme uyarlaması tamamlandıktan sonra değerlendirilir. ARM tabanlı kart, mevcut Windows ikilileri için doğrudan yerine takılacak PC değildir.

## Teklifte istenecek donanım

| Parça / özellik | Önerilen koşul |
|---|---|
| İşlemci | i5-1235U veya benzeri güncel U sınıfı; tam işlemci kodu teklif üzerinde yazmalı |
| Bellek | 32 GB (uygunsa 2×16 GB); ekonomik alternatif 16 GB; üreticinin onayladığı RAM |
| SSD | 1 TB; tercihen NVMe TLC, SMART ve yazma ömrü/TBW bilgisi açık; ürün arayüz desteği teyit edilmeli |
| USB | En az dört, tercihen altı fiziksel Type-A port; iki SDR, dokunmatik, servis bağlantısı için yer |
| USB yapısı | İki SDR ile sürekli IQ aktarımında test; port sayısı bağımsız USB denetleyicisi sayısı değildir |
| Ağ | İki kablolu Gigabit Ethernet tercih; tesis ağı ve sonraki röle ağı için ayrılabilir |
| Görüntü | HDMI; ekran için USB dokunmatik desteği; ilk masa testinde normal harici monitör |
| Soğutma | Endüstriyel fansız aday; kasaya yerleşince ölçülmüş sıcaklık ve sürdürülebilir performans gerekir |
| Güç | Üreticinin uygun adaptörü ve kesin DC giriş bilgisi; UPS sonradan toplam yükle boyutlandırılır |
| BIOS | Elektrik geri gelince açılma, TPM 2.0 ve Win11 desteği; varsa belgeli watchdog ve yazılım arayüzü |
| Servis | Değişebilir RAM/SSD, yerel garanti, sürücü/BIOS erişimi, tedarik sürekliliği |
| Mekanik | Ölçülü çizim, montaj delikleri, konnektör ve kablo çıkışları; 320×240×150 mm öneri kasaya henüz fit doğrulaması yok |

RTL-SDR'ler için ilk bağlantı doğrudan PC portlarından yapılmalı. Ortak pasif USB hub varsayılan çözüm değildir. USB 2.0 uyumlu alıcıda USB 3.x port bulunması alıcıyı hızlandırmaz; bağlantı kararlılığı ve RF paraziti ölçülür.

## Gerçek ürün adayları

### 1. Technopc TPC105F — öncelikli teklif adayı

[Üretici sayfası](https://technopc.com.tr/technopc-endustriyel-pc-tpc105f/): 12. nesil Core i3/i5/i7 seçenekleri, 32 GB'a kadar DDR4 seçenekleri, 1 TB/2 TB dahil SSD seçenekleri, iki Gigabit LAN, dört USB 2.0 ve iki USB 3.2 Type-A, fansız gövde, Windows/Linux desteği listeleniyor. İşletim sistemi satırı FreeDOS; Windows lisansı dahil varsayılmamalı.

İstenecek: i5'in **tam kodu**, 32 GB RAM, 1 TB SSD'nin marka/modeli ve arayüzü, Windows 11 Pro lisansı, DC giriş/adaptör, mekanik çizim ve numune fiyatı. Genel “12. nesil i5” adı yeterli değil. Numune doğrulaması öncesi seri alım önerilmez.

### 2. Genova GW-N3161 — karşılaştırmalı teklif adayı

[Satıcının ürün sayfası](https://www.genovadonanim.com.tr/products/intel-core-i5-1235u-fansiz-aluminyum-endustriyel-mini-pc-ddr4-6-lan-1-com): i5-1235U, iki DDR4 SO-DIMM, üç USB 3.1 + üç USB 2.0, altı LAN, 12 V, Windows/Linux ve barebone yapı ilan ediliyor. Altı LAN bizim ilk cihaz için zorunlu değil.

Araştırmada indekslenmiş satıcı ilanında **27.671 TL + KDV** çıplak sistem bedeli görüldü. Doğrudan sayfa erişimi bu araştırmada başarısız oldu; güncel stok/fiyat teyidi yok. RAM/SSD/OS dahil değil; toplam sistem maliyeti olarak kullanılamaz. Ana kart modeli, SSD arayüzü, lisans, adaptör ve çizim için yazılı teklif gerekir.

### 3. ASUS NUC 14 Pro — masaüstü geliştirme alternatifi

[ASUS teknik sayfası](https://www.asus.com/be-nl/displays-desktops/nucs/nuc-mini-pcs/asus-nuc-14-pro/techspec/): Core Ultra 5 125H seçeneği ve kit için Windows 11 / Ubuntu 24.04 LTS desteği listeleniyor. 32 GB ve 1 TB ile teklif alınabilir; seçilen SKU'nun RAM/SSD/OS içeriği teyit edilmeli. Endüstriyel fansız gövde yerine geçeceği varsayılmaz; özel kasaya montaj/soğutma ayrı tasarımdır. Türkiye stok/fiyatı bu notta doğrulanmadı.

Ekonomik sınıf için [Technopc Nano Fanless3](https://technopc.com.tr/technopc-mini-pc-nano-fanless-3/) N100, 16 GB'a kadar RAM seçenekleri ve çift Ethernet ile adaydır. Üretici sayfasında SSD seçenekleri 512 GB'a kadar listeleniyor; 1 TB desteği teyit gerektirir. N100/N150 ile bizim çoklu dijital çözücü yükümüz ölçülmediğinden bu sınıfa sekiz kanal kapasitesi sözü verilmez.

## İlk numune kurulum ve kabul sırası

1. Windows 11 Pro x64; üreticinin BIOS ve çipset/USB/LAN sürücüleri. Mevcut geliştirme PC'si değiştirilmeden ayrı numune kurulur.
2. Çalışan BİEM sürümü ve aynı çözücü sürümleri; cihaz bazında USB sürücü kontrolü. Eski korumalı kayıtların taşınması ayrı doğrulanır.
3. Kontrollü masaüstü oturumu; kayıt sırasında uyku kapalı, saat eşitlemesi etkin. Uygulama açılışı ve elektrik dönüşü davranışı test edilir. Mevcut GUI, oturumsuz Windows servisiymiş gibi kabul edilmez; UAC/yetki kontrolü devre dışı bırakılmaz.
4. Önce bir SDR ile analog/DMR/TETRA regresyonu, sonra iki SDR entegrasyonu. Yazılımda çoklu alıcı yönetimi ayrıca tamamlanmalı; iki port takmak otomatik eşzamanlı alım sağlamaz.
5. Hedef kanallarla sürekli trafik testi; işlemci tek çekirdek/toplam yükü, RAM, USB örnek kaybı, sıcaklık, çözücü senkronu ve arşiv bütünlüğü kaydedilir. Önce açık masa, sonra kapalı prototip kasa.
6. En az 24–72 saat ilk dayanıklılık denemesi; daha uzun ürün kabulünün yerine geçmez. Güç kesilip gelmesi, disk doluluk davranışı ve yetkili kayıt dinleme kontrol edilir.

BM-ICC-08 model adı tek başına sekiz RF kanalının eşzamanlı kaydedildiği anlamına gelmez. Kanal kapasitesi PC, alıcıların anlık bantları, protokoller ve yazılım entegrasyonu birlikte test edilerek belirlenir. Ham IQ sürekli kaydı bu 1 TB ses arşivi önerisinin kapsamı değildir.

Bu belgede öneri ve kaynak incelemesi yapıldı; donanım satın alınmadı, kurulmadı ve yeni performans/RF testi yapılmadı.
