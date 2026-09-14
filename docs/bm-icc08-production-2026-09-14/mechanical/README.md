# BM-ICC-08 mekanik paket / Rev A

**Özgün BİEM önerisi - RFQ / EVT.** Numune uyumu ve imalatçı kontrolünden sonra üretim revizyonu verilir. DXF'lerde `CUT`, `BEND`, `HOLD` ve `TEXT` katmanları ayrıdır. `HOLD` konnektör/PC numunesiyle doğrulanmamıştır; otomatik kesime dahil edilmez. Bu paket bir STEP montaj modeli içermez; OpenSCAD parametrik yerleşim ve DXF parçalar içerir.

## Ana ölçüler ve malzeme

| Parça | Ölçü / malzeme | İmalat |
|---|---|---|
| C01 U şasi | 360 genişlik, 254 derinlik, 84 yükseklik; 2 mm Al 5052-H32 | İki 90° büküm. İç R=2 mm, K=0,33 başlangıç hesabı; numune bükümüyle düz açılım düzeltilecek. |
| C02 ön panel | 360 × 86 × 3 mm Al 5005 | CNC/lazer, naturel eloksal/saten görünüş, BIEM özgün baskısı. |
| C03 arka panel | 360 × 86 × 3 mm Al 5005 | RF/data/güç bölgeleri; iki 60 mm fan, tel ızgara. |
| C04 üst kapak | 360 × 254 × 2 mm Al 5052-H32 | Sökülebilir 6 vida; iç L köşeler/nutplate ile bağlantı. |
| C05 kulak L/R | 86 yükseklik; ön kanat 61,3; yan dönüş 60; 3 mm çelik | 90° büküm; iç R=3 mm, K=0,33 başlangıç. İki kulakla toplam 482,6 mm. |
| C06 iç tabla | 300 × 200 × 2 mm Al | 6 yükseltici, slotlu PC/SDR tutucular. |
| Toplam gövde | 360 × 260 × 86 mm | Derinliğe ön/arka 3'er mm dahil; 10 mm ayaklar hariç. |

Grafit gövde için RAL 7024 görsel hedef; nihai boya/eloksal numunesi BIEM ile eşlenir. Ön panel doğal metal, sınırlı bordo vurgu. Gerçek logo oranları korunur. Ürün adı **BİEM Radio Integrated Solution**, model **BM-ICC-08**. `ICC` açılımı veya `08 = kanıtlanmış 8 kanal` yazısı eklenmez.

### Rack

Ön kanatlar gövdeye her yanda 4×M4 vida ve somun plakayla bağlanır. 2 mm alüminyuma kısa diş açıp taşıma yükü bırakılmaz. Toplam ön genişlik 482,6 mm; nominal rack delik merkez aralığı 465,1 mm. Kulaklarda 9 × 10 mm dikey oval delikler iki sıra; delik yüksekliği gövde altından yaklaşık 20,8 / 65,2 mm. Bu yerleşim hedef rack ile fiziksel olarak denenir. Ayaklar çıkarılır. Raf/arka destek zorunlu tasarım koşuludur; yalnız kulakla konsol yükü rating'i verilmez. Raf kalınlığı ve komşu cihaz boşluğu birlikte kontrol edilir.

7 inç ekranın tipik yüksekliği bu 86 mm ön panele sığmayabilir. Ekranlı ürün **ayrı 3U kasa revizyonu veya harici ekran** olarak ele alınır; bu 2U panele doğrudan 7 inç kesit açılmaz.

## İç yerleşim

Ön soldan koordinat başlangıcı: X sağa, Y arkaya, Z yukarı. Tabla (30,26,7) konumunda. PC için ayrılan gövde 117 × 112 × 49,2 mm, hedef konum X=208, Y=45, Z=12. Minimum üst hava boşluğu yaklaşık 22,8 mm. Gerçek kasa toleransı, kablo kıvrımı ve portlar numunede kontrol edilir.

Sol RF bölgesinde iki V3 için her biri 105 × 35 × 22 mm **ayrılan hacim** vardır; bu rakamlar üretici kesin V3 ölçüsü değildir. Kelepçeler numuneye ayarlanır. PC/RF arasında çıkarılabilir metal bölücü ve kısa panel bağlantı örgüsü kullanılır. SDR metal gövdesi çıkarılmaz. Fanlar arka panelde X=250/320, Z=43; 50 × 50 mm vida merkezleri. PC'nin kendi fanı korunur, hava girişleri kapatılmaz; sıcak çıkışın girişe kısa devresi önlenir.

Kablo güzergâhı: SMA'dan SDR'ye 25-30 cm 50 ohm RG316; USB ve fan besleme kablolarından uzak kenar. RF1 ve RF2 ayrı anten beslemeleridir. Splitter ve LNA standart donanım değildir. USB hub yerine alıcılar PC'nin ayrı portlarında başlatılır; ortak kök hub/akım sınırları yük testinde görülür.

## Güç ve servis

İlk prototip, PC'nin **orijinal harici adaptörü** ile beslenir. Güç kablosu kesilmeden bölünebilir geçiş ve iç kelepçeden geçirilir. Cihaza 12-24 V etiketi basılmaz. Gerilim, akım, polarite ve DC uç ölçüsü PC/adaptör numunesinden doğrulanınca seri etikete aktarılır. Kilitli DC konnektör sonraki revizyonda; giriş akımı, kablo kesiti ve temas kaybı hesabıyla seçilir.

Her 5 V fan en fazla 0,26 A çeker. Yeterli 5 V USB port beslemesi ve doğru güç kablosu numunede kontrol edilir; iki fan için 0,52 A bütçe vardır. USB-C kullanılıyorsa uygun CC sonlandırmalı yalnız 5 V besleme adaptörü gerekir; yüksek gerilim isteyen PD tetikleyici kullanılmaz. Fanlar bir pasif USB 2.0 hattına birlikte yüklenmez. Yetersiz port gücü durumunda fanlar ayrı sertifikalı 5 V beslemeye alınır ve güç/RF testi tekrarlanır.

Ön güç aktüatörü PC'nin gerçek düğmesine mekanik basar; header pinout tahmini yapılmaz. Delik, plunger stroku ve serbest bırakma numune ile belirlenir. LED kartı RP2040 tabanlı USB CDC'dir; gerçek kayıt/servis/link durumu yazılımdan gelir. Ön küçük servis kapağı altında HDMI uzatma yuvası ayrılır. Üst kapağın açılmasıyla SSD ve alıcılar tek tek değiştirilebilir.

## Proses ve kalite notları

- İç kablo yolları çapaksız; görünür keskin köşe kırma 0,3-0,5 mm hedef. Kaplama öncesi gerekli şasi bağlama yüzeyleri maskelenir. Harici şasi saplaması işlevsel bağlama içindir; cihazın koruma sınıfı test olmadan ilan edilmez.
- Dış ölçü hedef toleransı ±0,5 mm; konnektör delikleri üretici veri sayfasına göre; büküm açısı ±0,5° hedef. Fabrikanın proses yeterliliğiyle kesinleştirilir. Düz açılım K hesabı deneme bükümünün yerine geçmez.
- M3/M4 vidaların torku somun/kaplama/üretici tablosuna göre seçilir. Vidalarda pullar, sökülebilir servis erişimi; raf destekli rack montajında kulak esnemesi ölçülür.
- İç L köşeler, somun plakaları ve PC/SDR kelepçeleri ilk DFM kontrolünde detaylandırılır. Parametrik model bunların hepsinin bitmiş imalat modelini temsil etmez.
- Önce boyasız uyum numunesi; ardından delik revizyonu, boya/baskı, 24 saat termal/RF testi; sonrasında imalat serbest bırakma. Kasa IP derecesi veya sıcaklık sınıfı test olmadan basılmaz.

## Çizimler

`BM-ICC-08_Genel_Yerlesim.svg`: ölçekli ön/üst/arka görünüş ve rack dönüşümü.

`BM-ICC-08_RevA.scad`: parametrik gövde ve iç hacim yerleşimi; hazır mini PC görseli montaj hacmidir.

`C01_tray_flat_review.dxf`, `C02_front.dxf`, `C03_rear.dxf`, `C04_top.dxf`, `C05_ear_flat_review.dxf`, `C06_carrier.dxf`: mm birimli özgün tasarım; flat_review dosyalarında büküm payı imalatçıya teyit ettirilir. Bunlar Altınkaya/Hammond kasasına ait OEM çizimleri değildir.

Kaynaklar: [V3 veri sayfası](https://www.rtl-sdr.com/wp-content/uploads/2018/02/RTL-SDR-Blog-V3-Datasheet.pdf), [Noctua teknik ölçüler](https://www.noctua.at/en/products/nf-a6x25-5v/specifications), [PC paketi](https://www.minikpc.com/geekom-mini-it13-intel-13-nesil-i9-13900hk-32gb-ddr4-1tb-m-2-ssd-wi-fi-6e-1x-ethernet-2x-hdmi-win11-pro-mini-pc). RF performansı veya bitmiş cihaz uygunluğu bu parçaların katalog verisinden türetilmez.
