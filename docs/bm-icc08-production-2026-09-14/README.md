# BİEM Radio Integrated Solution - BM-ICC-08

**Rev A / 14 Eylül 2026 - Prototip ve üretime hazırlık paketi**

Bu çalışma, `docs/product-concept-2026-09-14/README.md` notlarına dayanır. Başlangıç noktası: `codex/dmr-receiver`, `acef9c0d68a1ccac633cfda1e36ef89795c5400a`. Windows'taki en son çalışan yazılımın tamamı depoda bulunmadığı için bu paket yazılımın saha kabulü anlamına gelmez.

## Seçilen çözüm

Ekransız, bağımsız x86/Windows kayıt cihazı; 360 × 260 × 86 mm metal masaüstü gövde; sonradan takılıp çıkarılan iki kulak ile 482,6 mm genişliğinde 19 inç / 2U rack montajı. Ayaklar rack kullanımında çıkarılır. Rack içinde arkadan destekleyen raf kullanılır; kulaklara taşıma yükü sertifikası atanmamıştır.

Hızlı prototip için GEEKOM IT13 / i9-13900HK / 32 GB / 1 TB / Windows 11 Pro hazır paket ve iki gerçek RTL-SDR Blog V3 seçildi. Bu PC bir prototip işlem modülüdür; seri üretimde uzun dönem tedarik, kurumsal garanti ve IoT OEM lisans koşulları sağlanan x86 modüle geçiş için iç taşıyıcı değiştirilebilir. `IT13 Max`, `2026 Edition` veya farklı işlemcili bir ürün aynı parça sayılmaz.

Kapasite hedefi önce 4, sonra 8 eşzamanlı **RF taşıyıcısıdır**. İki SDR, iki bağımsız frekans penceresi sağlar. 8 RF taşıyıcısında iki DMR slotunun tamamı kullanılırsa 16 ses akışı oluşabilir; bu kapasite henüz doğrulanmış değildir. Modeldeki `08` bir test sonucu değildir.

## Dosyalar

- [Tek dosyada tüm paket / ZIP](outputs/BM-ICC-08_Teknik_Paket_RevA.zip): PDF, Excel, mekanik çizimler ve tedarik/lisans notları.
- [Teknik dosya / PDF](outputs/BM-ICC-08_Uretime_Hazirlik_RevA.pdf): mimari, kasa, bağlantılar, satın alma, lisanslar, kabul planı.
- [Bütçe / Excel](outputs/BM-ICC-08_BOM_Butce_RevA.xlsx): düzenlenebilir miktarlar, fiyatlar, KDV, risk payı, geliştirme ödeneği ve disk hesabı.
- [Mekanik tasarım](mechanical/README.md): ölçülü görünüşler, özgün panel ve kulak DXF'leri, parametrik OpenSCAD yerleşimi.
- [Tedarik ve teklif taslakları](TEDARIK_VE_RFQ.md): her satın alma grubunun kaynağı, alternatif ve talep edilecek teyitler.
- [Lisans ve uygunluk](LISANS_VE_UYGUNLUK.md): ticari dağıtımdan önce kapanacak somut maddeler.
- [Yazılım ve kabul işleri](CODEX_URETIM_ISLERI.md): mevcut çalışan alıcı korunarak uygulanacak işler.
- [BOM kaynak verisi](bom.json): fiyatın gözlem mi, mühendislik ödeneği mi olduğunu koruyan veri.
- [Kaynaklar](KAYNAKLAR.md): erişim tarihi, doğrudan bağlantı ve kullanıldığı karar.
- [Dosya doğrulama kaydı](DOGRULAMA.md): hesap, görsel, CAD ve paket kontrol sonuçları.

## Bütçe özeti

| Kalem | Plan tutarı |
|---|---:|
| Bir prototip malzeme + montaj, %20 KDV varsayımı dahil | 95.227,43 TL |
| %20 risk payıyla prototip için ayrılacak bütçe | 114.272,92 TL |
| Bir defalık geliştirme / ürünleştirme / test, KDV dahil ödenek | 497.400,00 TL |
| Toplam 10 cihaz (prototip dahil) + bir defalık çalışma, risk paylı | 1.640.129,16 TL |
| AMBE / TETRA / yeni IoT OEM ticari hakları | Teklif bekliyor; yukarıdaki toplamlara dahil değil |

PC ve SDR fiyatları 14 Eylül web gözlemidir; diğer parça, işçilik ve test tutarları düzenlenebilir plan ödeneğidir. Kesin satın alma fiyatı veya taahhüt değildir. Bir defalık çalışma her cihaza tekrar eklenmez.

## Kullanım ve üretim durumu

Bu paket **RFQ / EVT prototip revizyonudur**. Ölçülü parçalar imalat teklifine uygundur. Konnektör ve PC numunesiyle uyum, büküm payı, sıcaklık/RF testleri ve üretici kontrolünden sonra imalat revizyonu serbest bırakılır. STEP onaylı seri üretim CAD'i veya CE uygunluk beyanı verilmiş değildir.

Özel kasanın terminini beklerken PC + bir V3 açık tezgâhta çalıştırılabilir. Hazır kasa alternatifi: Altınkaya `RM-120-360-A-S-H`; kulaksız gövde ve sonradan sökülebilir kulak seti teklif sırasında teyit edilir. Bu hazır kasanın ölçüleri özgün BİEM kasasının ölçülerinden farklıdır; bu paketin panel DXF'leri doğrudan RM-120'ye uygulanmaz. Kesin olarak sökülebilir kulak sunan ikinci hazır seçenek Hammond `RM2U1913SBK`'dır.

14 Eylül fiyat gözlemleri sipariş veya stok rezervasyonu değildir. Açık fiyatı olmayan parçalar tahmini ödenektir. Teklif bekleyen AMBE/TETRA/OEM bedelleri toplamda ücretsiz varsayılmamıştır; ticari toplam bu kalemler kapanana kadar eksiktir. Tedarikçilere mesaj gönderilmemiş ve ödeme yapılmamıştır.

## Değiştirilmeyen sınırlar

SDR#, çalışan sürücüler ve alıcı kodu bu çalışmada değiştirilmedi. Anten, LNA, RF splitter, dokunmatik ekran ve UPS ana bütçeye eklenmedi. Müşterinin mevcut anten tesisatı kullanılır; ortak anten istenirse ayrı RF tasarımı yapılır. Şifreli hava arayüzünün çözülmesi veya Hytera API yetkisi sağlanmış değildir.
