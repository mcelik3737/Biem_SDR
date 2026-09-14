# Hızlı prototip tedarik planı ve teklif taslakları

14.09.2026 / Rev A. Sipariş verilmedi, stok rezerve edilmedi, tedarikçilere mesaj gönderilmedi. Aşağıdaki talepler parça/numune ve fiyat teyidi için hazırdır. Bütçedeki ödenekler satıcı fiyatı değildir. Teslim hedefleri Türkiye içi planlama varsayımıdır.

## Satın alma sırası

| Dalga | BOM | Kaynak ve işlem | Beklenen çıktı |
|---|---|---|---|
| 1 - İlk gün | B01 | [MinikPC, GKM-MINI-IT13-G32-T1](https://www.minikpc.com/geekom-mini-it13-intel-13-nesil-i9-13900hk-32gb-ddr4-1tb-m-2-ssd-wi-fi-6e-1x-ethernet-2x-hdmi-win11-pro-mini-pc) | 1 adet için fiziksel stok, KDV dahil fiyat, fatura/OEM kaydı, 24/7 kullanım garanti şartı ve gönderim tarihi. Görünen fiyat 53.999,17 TL. |
| 1 - İlk gün | B02 | [Beti V3 / 151.02](https://www.beti.com.tr/urun/rtl-sdr-blog-v3-rtl2832u-software-defined-radio) | 2 aynı revizyon gerçek V3; ilk testte birini kullan. 6.430,13 TL/adet gözlemi; sepete açık, stok sayısı açıklanmıyor. |
| 1 - Paralel teklif | B03-B08, B21, B23-B24, B26 | [Altınkaya](https://www.altinkaya.com/tr), 0312 395 27 68; özgün tasarım için yerel lazer/büküm atölyesi alternatifi | 1 EVT numunesi ve 10 adet fiyat; büküm, boya, baskı, kulak seti ve CAD kontrolü ayrı. |
| 2 - Numuneden önce | B09-B11, B13, B15, B18, B20, B22, B25, B30 | Beti + [Direnç](https://www.direnc.net/) / yerel RF ve kablo imalatçısı | Konnektör fotoğrafı, ölçüsü, kablo boyu, 50 ohm ve USB veri/güç özellikleri; fiyat ve stok teyidi. Katalog ana sayfası fiyat kanıtı değildir. |
| 2 - Termin kritik | B12, B14 | [Mouser Türkiye](https://www.mouser.com.tr/) / Neutrik satıcısı | NE8FDX-P6, NAUSB-W için Türkiye teslimli stok/kargo/ithalat toplamı. İthal ise BOM nakliye ödeneği artırılır. |
| 2 - Termin kritik | B16-B17 | [Noctua ürün kaynağı](https://www.noctua.at/en/products/nf-a6x25-5v/specifications) ve bayi | 2 adet 5 V fan. Stok kanıtlanmadı. Gecikirse eşdeğer 5 V, 60 mm, rulmanlı fanla termal/RF test tekrarı. |
| 2 | B19 | [Robotistan Pico](https://www.robotistan.com/raspberry-pi-pico) / RP2040 kart satıcısı | Pico detayında tükendi. Stoklu USB RP2040 eşdeğeri talep; pinout/firmware kontrolü. LED modülü ilk RF testini bloke etmez. |
| 3 - Montaj | B27-B29 | BİEM montaj, yerel rack tedarikçisi, yurtiçi kargo | İşçilik, raf derinliği/yük ve montaj ölçüleri, tek konsolide sevkiyat. |
| Ticari öncesi | L01-L03 | DVSI, mevcut TETRA bileşeninin hak sahibi, Microsoft IoT dağıtıcısı | Yazılı ticari hak ve fiyat. Ücretler bilinmiyor; bütçe dışında açık kalem. |

**İlk fiziksel doğrulama:** mevcut geliştirme PC'si kullanılabiliyorsa yalnız bir gerçek V3 + uygun kısa USB kabloyla başlanabilir. Tam cihaz alışverişinden önce en kritik alıcı/kalibrasyon riski böyle kapanır. İkinci alıcı, kasa ve hazır PC beklenirken RF kabul notları tutulur.

## Hazır kasa yedeği

Özgün kasa gecikirse [Altınkaya RM-120-360-A-S-H](https://www.altinkaya.com/tr/products/19-2u-rack-tipi-aluminyum-kutu-2440) için 360 mm seçeneği istenir. İlanın 66 mm başlangıç ölçüsü alınmaz. Masaüstü gövdesine sökülebilir kulak takılabilmesi yazılı teyit edilmelidir. Bu modelin kendi CAD'i ve yeni panel revizyonu kullanılmalıdır.

[Hammond RM2U1913SBK](https://www.hammfg.com/part/RM2U1913SBK) ikinci alternatiftir; [RM serisi](https://www.hammfg.com/electronics/small-case/rack-mount/rm) sökülebilir kulakları ve ayakları açıkça tanımlar. Yaklaşık 422 × 330 × 89 mm gövde, özgün tasarımın 360 × 260 × 86 mm ölçüsüyle karıştırılmamalıdır. Türkiye teslimli fiyat/termin doğrulanmadı.

## RFQ-01 - PC tedarikçisi

Konu: BİEM BM-ICC-08 prototipi - GKM-MINI-IT13-G32-T1, 1 ve 10 adet teklif

BİEM Radio Integrated Solution kayıt cihazımızın ilk prototipinde kullanmak üzere GKM-MINI-IT13-G32-T1 / i9-13900HK / 32 GB DDR4 / 1 TB / Windows 11 Pro paketine teklif rica ederiz. Farklı IT13 Max veya 2026 Edition varyantı teklif edilirse ayrıca belirtiniz. 1 adet fiziksel stok, Türkiye içi gönderim tarihi, KDV hariç/dahil fiyat, ödeme/geçerlilik ve 10 adet terminini bildiriniz. Orijinal adaptörün çıkış gerilimi/akımı, DC uç ölçüsü/polaritesi, USB port sayıları, güç geldikten sonra otomatik açılış BIOS desteği, VESA plakası ve işletim sisteminin lisans/fatura kaydını paylaşınız. 24/7 kayıt, metal dış kasa içinde belirtilen sıcaklık sınırlarında kullanım ve OEM ürün içinde satışın garanti/lisans koşullarını yazılı belirtiniz. SSD üretici/model/firmware ve yazma dayanıklılığı ile ürünün tedarik ömrünü de rica ederiz.

## RFQ-02 - RF alıcı ve kablo

Konu: Gerçek RTL-SDR Blog V3 ve SMA ara kablo - prototip 2 adet

2 adet aynı revizyon gerçek RTL-SDR Blog V3 (1 ppm TCXO, metal gövde, standart SMA) için teklif rica ederiz. USB-A / USB-C revizyonunu ve tuner modelini bildiriniz; V4 veya markasız RTL2832U eşdeğerini ayrı seçenek olarak yazınız. Antene ihtiyacımız yoktur; yalnız alıcı bulunmuyorsa 151.02 setli ürünün fiyatını belirtiniz. 2 adet 25-30 cm RG316 / 50 ohm / SMA erkek - standart SMA dişi panel somunlu ara kablo, 2 toz kapak ve 2 ekranlı 0,3 m USB veri uzatması da ekleyiniz. Fiziksel stok, gerçek ürün fotoğrafı, seri numarası/orijinallik kanıtı, KDV, teslim ve 10 cihaz için 20 alıcı tedarik sürekliliğini paylaşınız.

## RFQ-03 - Kasa ve mekanik imalat

Konu: BM-ICC-08 özgün 2U masaüstü/rack kasa, Rev A - 1 numune / 10 adet

Ekli `mechanical/` paketine göre 360 × 260 × 86 mm masaüstü gövde, sonradan sökülebilir 19 inç kulak seti ve 300 × 200 mm iç taşıyıcı için fiyat rica ederiz. Şasi/kapak 2 mm Al 5052-H32, ön/arka 3 mm Al 5005, kulak 3 mm çelik; muadil malzeme önerinizi ayrı belirtiniz. Grafit gövde, saten/naturel ön panel ve özgün BIEM baskısı hedefleniyor. 1 adet numune ve 10 adet fiyatlarını; lazer, büküm, yüzey, baskı, kaynak/somun plaka, bağlantı köşeleri ve montajı ayırınız. Büküm K faktörü ve ölçü toleranslarını atölye prosesinize göre geri bildiriniz. `HOLD` katmanındaki delikler konnektör/PC numunesi teyit edilmeden kesilmemelidir. Teknik kontrol, DFM geri bildirimi, numune termininin başlangıç şartı ve tekrar sipariş süresini paylaşınız. Alternatif olarak RM-120-360 kasanızın kulaksız gövde + sonradan takılan kulak seçeneğini ayrı fiyatlayınız.

## RFQ-04 - Panel geçiş ve fan

Konu: BM-ICC-08 - Neutrik panel geçişleri ve 5 V fanlar

1×NE8FDX-P6, 1×NAUSB-W, 2×Noctua NF-A6x25 5V, 2×60 mm parmak ızgarası için Türkiye teslimli teklif rica ederiz. Fanın 12 V/PWM farklı sürümüyle değiştirilmemesi önemlidir. USB'den 5 V fan güç kablosunun konnektör/pinout ve akım uygunluğunu ayrıca belirtiniz. Stok bulunduğu ülke, kur/kargo/gümrük/KDV dahil toplam maliyet ve gerçek gönderim tarihi yazılmalıdır. Üretici panel PDF/DXF revizyonunu da ekleyiniz. Muadiller ayrı satır ve ayrı teknik belgeyle sunulmalıdır.

## RFQ-05 - DVSI (İngilizce taslak)

Subject: Commercial decode-only AMBE solution for BIEM BM-ICC-08 - 8 / 16 simultaneous voice streams

We are preparing a receive-only VHF/UHF radio recording appliance for customers' authorized radio systems in Türkiye. The prototype is Windows x86-64 with a local recording service. Please quote a licensed decode-only AMBE+2 solution suitable for DMR, for 8 and 16 concurrent voice streams, including SDK and any hardware alternative. Please identify codec modes, supported interfaces, sustained channel capacity, latency, offline operation, redistribution/OEM rights, territorial restrictions, development fees, per-device royalties, minimum order, support and lead time for 1 prototype and a 10-device pilot. We are not requesting the removal of air-interface encryption. A USB hardware alternative must specify the exact real-time stream capacity and the number of units required.

Kaynak/teklif kanalı: [DVSI](https://www.dvsinc.com/products/price.shtml), sales@dvsinc.com. Taslak gönderilmedi.

## RFQ-06 - TETRA / Windows OEM / uygunluk

**TETRA hak sahibi:** Kullanılan DLL'nin dosya adı, sürümü, SHA-256 ve geldiği paket ile başvurulur. Ticari yeniden dağıtım, decode kanal sınırı, Windows servisinde kullanım, x86/x64 arayüzü, update/support ve ücret yazılı istenir. Hak sahibi belirlenmeden tahmini bir firmaya müşteri DLL'si gönderilmez.

**Microsoft IoT yetkili dağıtıcı:** Yeni BIEM cihazı için Windows 11 IoT Enterprise LTSC OEM, 1 EVT ve 10 cihaz; işlemci sınıfı, gerekli OEM sözleşmesi, aktivasyon, kurtarma imajı, çevrimdışı kullanım, yeniden markalama ve birim lisans bedeli istenir. Yol haritası: [Microsoft lisanslama](https://learn.microsoft.com/en-us/windows/iot/iot-enterprise/commercialization/licensing).

**Uygunluk laboratuvarı:** Türkiye iç pazarı, yalnız alıcı işlevi, x86 PC + iki V3 + harici orijinal DC adaptör + metal kasa kombinasyonu bildirilir. Nihai ürün sınıflandırması, uygulanabilir standart/sürüm, numune sayısı, EMC/RF/güvenlik testleri, ön test + nihai test ayrı fiyatları, tekrar test bedeli ve sıra tarihi istenir. RF/VHF/UHF aralıkları ve yazılım modları teklif ekinde verilir; anten sisteme dahil değildir. Yetki/akreditasyon kapsamı test bazında kontrol edilir.

## Sipariş öncesi kapanacak kayıtlar

Her satır için firma, teklif no/tarih, ürün tam kodu/revizyonu, miktar, net/KDV/brüt fiyat, stok ülkesi, garanti, teslim tarihi ve muadil izni doldurulur. 14 Eylül web fiyatı tek başına proforma yerine kullanılmaz. Bu bilgiler geldiğinde `bom.json` ve Excel'deki mavi hücreler güncellenir. Tedarik ve lisans açığı kapatılmadan seri parti siparişi toplamı kesin kabul edilmez.
