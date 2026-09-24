# Ticari dağıtım, lisans ve uygunluk planı

Rev A - 14.09.2026. Bu belge karar ve kontrol planıdır; hak sahibinden lisans verilmiş veya ürün uygunluğu onaylanmış değildir. Yazılım telifi, vokoder teknolojisinin ticari kullanım hakkı, işletim sistemi ve nihai cihaz uygunluğu ayrı iş paketleridir.

## Bileşen matrisi

| Bileşen | Bulunan durum | Prototip / ticari çıkış için yapılacak iş |
|---|---|---|
| BIEM özgün kodu | Depodaki THIRD_PARTY, dağıtım lisansının seçilmediğini söylüyor | Hak sahipliği kayıtları, katkı sözleşmeleri, müşteri EULA ve üçüncü taraf istisnaları hazırlanacak. Otomatik olarak tüm kod kapalı kaynak ilan edilmeyecek. |
| Python / NumPy / SciPy / SQLite / Tcl-Tk | pyproject: Python >=3.12, NumPy >=2.2, SciPy >=1.15. Tam paket sürümleri sabitlenmiş dağıtım envanteri değil | Gerçekte kurulu sürüm ve wheel/DLL hash'leriyle SBOM; ilgili PSF/BSD/Tcl ve SQLite bildirimleri. Eklenmiş Pillow/kriptografi paketleri ayrıca tespit edilecek. |
| rtl-sdr-blog | THIRD_PARTY kaydında V1.4.0 GPL bileşeni; DLL kullanım yolu mevcut | Dağıtılan derlemenin COPYING ve karşılık gelen kaynak/build dosyaları saklanacak. BIEM ile doğrudan DLL bağlamanın yükümlülükleri uzmanla incelenecek. Sadece ayrı süreç yapmak veya çalışma anında indirmek tek başına lisans çözümü olarak sunulmayacak. |
| DSD-FME | COPYRIGHT: ISC tabanı, bazı dosyalarda GPL-2.0 ve başka projelerden bileşenler | 20260715 taşınabilir paketin bütün EXE/DLL paketleri ve kaynak kökenleri kontrol edilecek. Tek bir MIT/ISC etiketi yeterli değil. Sürümle eşleşen kaynak ve bildirim paketi oluşturulacak. |
| Cygwin | Güncel resmi metin API kitaplığı için LGPL-3.0-or-later + bağlama istisnası; yardımcı paketler farklı | Dağıtılan sürüm ve her paketin koşulu doğrulanacak. Eski “tüm Cygwin GPL” genellemesi kullanılmayacak. Kaynak sağlama ve LGPL yükümlülükleri paket bazında karşılanacak. |
| mbelib / AMBE | mbelib telif metni ISC. Bunun DVSI ticari teknoloji izniyle eşdeğer olduğu doğrulanmadı | DVSI'den decode-only, Windows x86, 8 ve 16 eşzamanlı ses akışı için yazılı lisans/SDK veya donanım çözümü teklifi. Ülke/patent kapsamı uzman incelemesi. Şimdilik bedel bilinmiyor. |
| TETRA DLL / ses kodeği | Güncel yerel DLL'nin kaynak/dağıtım hakkı depodan doğrulanamadı | DLL dosya adı/sürüm/hash/hak sahibi; ticari dağıtım izni ve güncelleme hakkı bulunacak. Alternatif lisanslı SDK incelenecek. Hava arayüzü standardının açık olması DLL dağıtım izni vermez. |
| Windows 11 Pro prototip | Seçilen PC satıcı paketinde dahil | Fatura, orijinal etkinleştirme/OEM kaydı ve kurtarma hakkı istenecek; başka cihazlara klonlama hakkı varsayılmayacak. |
| Windows IoT Enterprise seri üretim | Microsoft yeni cihazlarda OEM yolunu tanımlıyor | Yetkili IoT dağıtıcıdan cihaz üreticisi sözleşmesi, işlemci SKU fiyatı, aktivasyon, imaj/recovery ve yeniden markalama koşulları. Pro paketinin otomatik IoT hakkı yok. |
| SDR++ | Referans checkout; GPL-3.0 | İlk ürüne eklenmeyecek. Kod alınacaksa lisans etkisi yeniden incelenecek. |
| Harita / GPS / PoC / Hytera API | Yerel ekrandaki alanlar erişim hakkı veya saha doğrulaması değil | Harita verisi ve tile hizmeti ayrı; sağlayıcı atfı/offline kullanım koşulları. Hytera/HyTalk/PoC API sözleşmesi ve kanal ücretleri ayrı teklif. |

Dayanaklar: [repo THIRD_PARTY](../THIRD_PARTY.md), [DSD-FME COPYRIGHT](https://github.com/lwvmobile/dsd-fme/blob/audio_work/COPYRIGHT), [mbelib](https://github.com/szechyjs/mbelib/blob/master/COPYRIGHT), [Cygwin](https://www.cygwin.com/licensing.html), [Microsoft](https://learn.microsoft.com/en-us/windows/iot/iot-enterprise/commercialization/licensing), [DVSI](https://www.dvsinc.com/products/price.shtml).

### Yayın paketinde bulunacaklar

`manifest.json` (dosya adı/sürüm/SHA-256/kaynak/lisans), SPDX veya CycloneDX SBOM, `THIRD_PARTY_NOTICES`, gerekli tam lisans metinleri, lisans koşuluna göre karşılık gelen kaynak ve yeniden derleme talimatı, BIEM EULA, imzalı yükleyici, sürüm değişiklikleri ve kurtarma imajı özeti. Kullanıcı sesleri, anahtarlar ve müşteri kimlik verileri build paketine girmez.

## BIEM ürün lisansı önerisi

**Tek cihaz, çevrimdışı çalışan kalıcı çekirdek lisans** önerilir. Satılabilir kanal hakkı yalnızca testle kabul edilmiş kapasite kadar açılır. Analog, DMR ve TETRA yetenekleri ayrı capability bayraklarıdır; bunların açılması üçüncü taraf lisansının yerine geçmez. `RF channel limit` ile `simultaneous voice stream limit` ayrı alanlardır.

İmzalı lisans dosyasında ürün/model, seri, edition, RF/voice sınırları ve izinli özellikler bulunur. İmza özel anahtarı cihazlara konmaz. TPM/sistem kimliği değişiminde kontrollü servis yeniden bağlama uygulanır; SSD arızası müşterinin arşivini ve lisansını otomatik kaybettirmez. Destek süresinin bitmesi temel kayıt hizmetini durdurmaz. Lisans hatasında arşive erişim ve veri dışa aktarma korunur. Bu davranış henüz uygulanmış değildir.

EULA; müşteri verisinin mülkiyetini, kayıt yetkilendirmesini, destek kapsamını, üçüncü taraf bildirimlerini, cihaz değişimini, yedeklemeyi, yetkili servis erişimini ve sorumluluk sınırlarını açıklamalı. Kritik İSG sisteminin tek kayıt noktasına dayanacağına ilişkin garanti verilmez. Önerilen satış fiyatı; BOM + garanti/servis payı + geliştirme amortismanı + lisans + kanal marjı görülmeden kesinleştirilmez.

## Nihai cihaz uygunluğu

| İş | İstenen çıktı | Yayın durumu |
|---|---|---|
| Ürün sınıflandırması | Telsiz alıcı işlevi ve hedef pazar için RED / Türkiye Telsiz Ekipmanları Yönetmeliği kapsam görüşü | Laboratuvar görüşü bekliyor |
| EMC ve RF | Nihai kasa/PC/SDR/adaptör/kablo kombinasyonuyla emisyon, bağışıklık ve uygulanabilir alıcı test planı | Ön test ve resmi test yapılmadı |
| Elektrik / mekanik / sıcaklık | Harici adaptör belgeleri, erişilebilir parça sıcaklıkları, keskin kenar, kablo tutma, rack desteği, servis riski | Numune testi bekliyor |
| Teknik dosya | Çizimler, şemalar, BOM, risk değerlendirmesi, yazılım sürümü, test raporları, izlenebilir seri/etiket, Türkçe kılavuz | Bu paket başlangıç girdisi |
| Uygunluk beyanı / CE | İmalatçının nihai ürün değerlendirmesi ve imzası | Koşullar kapanmadan işaret basılmaz |
| Çevre / atık | Hedef pazarda uygulanabilir RoHS/AEEE, paketleme ve üretici kayıt yükümlülüklerinin teyidi | Sınıflandırma/uzman teyidi bekliyor |
| Kişisel veri | Müşteri bazlı amaç/hukuki dayanak/aydınlatma/erişim/saklama-silme/yedekleme düzeni | KVKK değerlendirmesi müşteri bazında |

Uygulanacak standartların sürümleri laboratuvarla seçilir; EN 300 113/EN 300 086, EN 301 489 ailesi ve EN IEC 62368-1 yalnızca görüşmeye götürülecek aday başlıklardır. Bu belge bunların tümünün uygulanabilir veya sağlanmış olduğunu söylemez. Adaptör ve SDR üzerindeki işaretler yeni birleşik ürünün uygunluk işlemini ortadan kaldırmaz. Masaüstü metal kutu satın almak da ürün için otomatik IP derecesi sağlamaz.

Kaynak: [BTK RED](https://www.btk.gov.tr/en/radio-equipment-directive-red), [BTK SSS](https://www.btk.gov.tr/en/market-surveillance-and-supervision-frequently-asked-questions), [KVKK](https://www.kvkk.gov.tr/). Türkiye iç pazar ilk kapsamdır; ihracat ülkesinin ilave siber güvenlik/çevre şartları ayrı incelenir.

## Ticari sevkiyatı durduran üç açık konu

1. DSD-FME/rtl-sdr dağıtım envanteri ile GPL/diğer koşulların ürün lisansıyla uyumu.
2. AMBE ve yerel TETRA bileşenleri için yazılı ticari hak/fiyatlandırma sonucu.
3. Son donanım kombinasyonu için kabul ve uygunluk dosyası.

Bu maddeler fiyatlandırılmadan Excel'deki prototip bütçesi “tam lisanslı seri ürün maliyeti” olarak kullanılamaz.
