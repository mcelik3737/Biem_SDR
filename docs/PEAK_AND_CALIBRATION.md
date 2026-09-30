# Canlı tepe frekansı ve SDR PPM kalibrasyonu — 2026-09-30

## Canlı kanal kartı

**Güncel ek:** Aynı gün eklenen isteğe bağlı yakın sinyal takibi, RF kilidi varken
buradaki ham tepe göstergesi yerine `RF ... MHz / Δ ... kHz · KİLİT` gösterir.
±2 kHz dahil yeşil, bunun dışında kırmızıdır. Alım kaybı beklemesinde gri `BEKLE`
görünür. Kilit yokken aşağıdaki `Tepe` ölçümü gösterilir. RF takip davranışı,
sınırları ve doğrulaması: [SIGNAL_FOLLOW.md](SIGNAL_FOLLOW.md).
Bu bölümdeki salt ölçüm açıklamaları ham `Tepe` göstergesine aittir.

Kanalın girilen MHz / mod satırının sağında iki satırlık gösterge vardır:

```text
Tepe ≈ 427.55450 MHz
Δ +4.50 kHz
```

Fark = ölçülen tepe − girilen kanal frekansı. Örnekte girilen frekans 427.55000 MHz'tir.
Artı işareti daha yüksek, eksi işareti daha düşük ölçülen frekanstır. Alım durunca,
kanal değişince veya belirgin sinyal bulunamayınca `Tepe: — MHz / Δ — kHz` gösterilir.
Bu gösterge ayarlanan frekansı, PPM değerini, kayıt eşiğini veya çözücü seçimini değiştirmez.

Ölçüm tüm modlarda ortak I/Q akışından yapılır; ayrıca USB açılmaz. En fazla 250 ms
gözlem biriktirilir, yaklaşık 5 Hz arayüz güncellemesinde ortak Hann FFT hesaplanır.
8192 nokta / 960 kHz ile FFT bin aralığı yaklaşık 117 Hz'tir. Dar tepe için alt-bin
enterpolasyonu vardır; ekrandaki ondalık basamaklar kalibrasyon doğruluğu iddiası değildir.

Her kanal yalnız kendi filtre bandında aranır; Otomatik modda TETRA'yı kapsamak için
25 kHz kullanılır. En güçlü tüm-bant sinyaline atlama yapılmaz. Kanal gücü squelch
altındaysa, yerel gürültü referansından en az 12 dB yüksek bir tepe yoksa veya maksimum
bandın kenarındaysa sonuç boş kalır. Yakındaki yapılandırılmış kanallar ve tuner DC
çevresi gürültü referansına katılmaz. Gürültü referansı için yeterli boş bin yoksa da
sonuç verilmez. Bu yüzden zayıf ama çözülebilen bir yayında gösterge boş kalabilir.

DMR/TETRA gibi modülasyonlarda en yüksek spektral nokta hareket edebilir ve taşıyıcı
merkezine eşit olmayabilir. `Tepe` bir protokol kilidi, AFC veya kalibre RF ölçümü değildir.
İki komşu sinyal aynı arama bandına düşerse gösterge en yüksek tepeyi seçer;
kimlik ayrımı veya komşu-kanal kalite alarmı bu değişikliğin kapsamında değildir.

## Bilinen referansla kalibrasyon

Alıcı / kanal ayarları → **SDR FREKANS KALİBRASYONU**:

1. Bilinen gerçek frekansı MHz olarak girin.
2. Aynı sinyalin gözlenen **merkezini** girin; dijital modülasyonun rastgele tepesini kullanmayın.
3. Ölçüm sırasında kullanılan PPM değerini girin. Sonraki hesaplanan PPM ile karıştırmayın.
4. `Hesapla` sonucu önizler. Alım / spektrum / FM Radio durmuşken `PPM kaydet` kullanın.
5. Sonraki alıcı açılışında kayıtlı değer sürücüye uygulanır. Kanal MHz değerleri otomatik değişmez.
   Daha önce kaymayı telafi etmek için değiştirilmiş kanal değerlerini bilinen nominal değerlerine
   kullanıcı geri getirir. Yeni kalibrasyon ölçümünde ölçüm PPM alanı tekrar güncellenmelidir.

Hesap, librtlsdr'nin `xtal × (1 + ppm / 1e6)` modeline göre:

```text
yeni PPM = yuvarla(((1 + ölçüm PPM / 1e6) × gerçek Hz / gözlenen Hz − 1) × 1e6)
```

Ölçüm PPM = +2 iken gerçek 427.55000, gözlenen 427.55450 MHz ise yeni değer yaklaşık
−8.53 PPM, tam sayı sürücü ayarı **−9 PPM** olur. Gözlenen 427.54450 MHz ise sonuç
**+15 PPM** olur. Bu iki örnek zıt yönlü düzeltmedir; kullanıcının gözlenen frekansı
netleştirmeden çalışan ayara bunlardan biri yazılmaz.

Kalıcı ayar `data/receiver.json` içinde saklanır. USB her açıldığında
`rtlsdr_set_freq_correction` çağrılır ve `rtlsdr_get_freq_correction` ile sürücü değeri
karşılaştırılır. Sürücünün "zaten aynı değer" anlamındaki −2 dönüşü yalnız geri okunan
PPM de eşleşiyorsa kabul edilir. PPM = 0 da bu yoldan geçer. Sürücü geri okuması,
RF frekans doğruluğunun ölçüldüğü anlamına gelmez. rtl_tcp mevcut 0x05 komutunu kullanır;
bu protokolde eşdeğer geri okuma bulunmaz. Frekans değiştiren spektrum yolu aynı USB kontrolünü kullanır.

Bu bir fabrika otomatik kalibrasyonu veya EEPROM yazımı değildir. SDR açılırken uygulanır;
yalnız arayüz açıldığı için boşta USB tutulmaz. Mevcut yapı tek seçili alıcı için ortak PPM
kullanır; başka SDR takıldığında o cihaza uygun değer seçilmelidir. Sıcaklık değişiminde
kararlı ve frekansı bilinen kaynakla yeniden kontrol gerekir.

Sürücü davranışı kaynak: [Osmocom librtlsdr](https://github.com/osmocom/rtl-sdr/blob/master/src/librtlsdr.c),
`rtlsdr_get_xtal_freq`, `rtlsdr_set_freq_correction`, `rtlsdr_get_freq_correction`.

## Doğrulama kapsamı

- Uygulandı: tepe/fark telemetrisi, kart göstergesi, referans hesabı, kalıcı PPM ve USB geri okuması.
- Donanımsız testler: artı/eksi/merkez frekansı, gürültü, daha güçlü komşu kanal,
  TDMA benzeri aralıklı sinyal, eski ölçümün temizlenmesi, değişmeyen I/Q/kanal ayarı,
  PPM yönü/yuvarlama, tekrar kayıtta birikmeme, sıfır ve negatif PPM ile her USB açılışında komut.
- Bekleyen: gerçek RF üzerinde yeni tepe göstergesi ve kalibrasyon kabulü.
- Kaynak sürüm değiştirildi; önceden kurulmuş bağımsız EXE bu işlemle yenilenmez.

## 424 MHz el telsizi ölçümü — 2026-09-30

Kullanıcı el telsizini 424.00000 MHz'e ayarladı. +2 PPM ile nominal frekansta
Otomatik/DMR çözümleme olmadığını, 423.99450 MHz girince DMR'nin çözüldüğünü bildirdi.
Bu ayarda tepe farkı yaklaşık 0,15 kHz olarak bildirildi; işareti belirtilmedi.
Bu, önceki 427 MHz gözlemindeki yön belirsizliğinden ayrı, yeni referans ölçümüdür.

424000000 / 423994500 oranından yeni düzeltme +14,9719 PPM, sürücü ayarı **+15 PPM**
hesaplandı. ±150 Hz artık sapma varsayımlarının ikisi de +15 PPM'e yuvarlanır.
Uygulama kapalıyken alıcı/kanal ayarları yedeklendi; `receiver.json` +15 PPM yapıldı,
birinci kanal nominal **424.00000 MHz / DMR** değerine geri getirildi. Diğer kanallar,
kazanç ve kayıt davranışı değiştirilmedi.

Yedek: `data/backups/calibration-424MHz-20260930-094327`.
Ölçüm geçmişi: `data/calibration-history.jsonl`.
Bu kullanıcı ölçümüne dayalı başlangıç kalibrasyonudur; düzeltilmiş ayarda gerçek RF
senkronu ve anlaşılır kayıt henüz doğrulanmadı. Otomatik protokol kabulü ayrıca kontrol edilir.

Ardından aynı sırada açılmış diğer pencerenin belleğindeki eski ayarı geri yazdığı görüldü:
09:43:41 yerel saatli alım olayı hâlâ +2 PPM bildiriyor. Kullanıcıdan açık pencerede
alımı durdurup PPM'yi 15 yaparak 424.000 MHz / DMR'de yeniden başlatması istendi.
+15 PPM ile RF kabulü bu yeniden başlatmaya bağlıdır. Arşivde önceki +2 PPM /
423.9945 MHz denemelerine ait iki kayıt doğrulandı (3,24 ve 1,80 sn; ID 3737,
grup 3737, CC 1); bunlar düzeltilmiş ayarın kabulü sayılmaz.

### Aynı gün 09:48 canlı RF sonucu

09:48:11 yerel saatli alım olayı USB / +15 PPM / 424.100 MHz tuner merkezini
doğruladı; izlenen kanal nominal 424.000 MHz'tir. Üç yeni korumalı DMR kayıt dosyası
oluştu ve dosyaların varlığı/boyutu doğrulandı: 09:48:15 / 3,96 sn,
09:48:32 / 2,88 sn, 09:48:36 / 6,84 sn. Her üçünde ID 3737, grup 3737, CC 1
bulundu. Fiziksel slot bildirilmediği için boş bırakıldı.

Kullanıcının yeni ekranında tepe 423.99921 MHz ve fark −0,79 kHz idi.
Tepe, modülasyonun en güçlü FFT noktası olduğundan bu kalan fark tek başına ek
PPM düzeltmesi için kullanılmaz; çalışan +15 PPM korundu. Manuel DMR'de nominal
frekansla gerçek RF çözümleme ve kayıt doğrulandı. Sesin anlaşılırlığı bu kontrolde
dinlenmedi; Otomatik mod aynı kalibrasyonla ayrıca RF kabul testi bekliyor.
