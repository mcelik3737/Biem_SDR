# Yakın sinyale kilitlenme — 30 Eylül 2026

## Kullanıcının istediği davranış

- Girilen kanal frekansının en fazla 6,5 kHz altında veya üstünde kalan uygun sinyale
  otomatik kilitlenerek çözümleme yapmak.
- Girilen kanal frekansını ve ortak SDR PPM ayarını korumak.
- Kilit frekansını ve girilen frekanstan işaretli farkını kanal kartında göstermek.
- Fark ±2 kHz içindeyse (sınırlar dahil) yeşil; dışındaysa kırmızı göstermek.
- Kullanıcı frekans veya referans PPM ayarını elle düzelttiğinde yeni farkın rengini
  yeniden değerlendirmek. Otomatik telafi gerçekleşmesi kırmızı farkı gizlemez.

## Kullanım

Yerel kaynak sürümü: `D:\Projects\Biem\_SDR\Start-BM-ICC-08.cmd`.
Önceden dağıtılan bağımsız EXE bu değişiklikle yenilenmedi.

Alım durmuşken **Canlı izleme → Kanal ayarları → Yakın sinyale kilitlen (±6,5 kHz)**
seçeneğini kullanın. Yeni ve eski kanal ayarlarında alan yoksa açık kabul edilir.
Tercih kanal başına kaydedilir; alım sırasında düzenlenmez. Manuel Analog, DMR,
TETRA ve diğer mevcut modlar ile Otomatik modun önündeki ortak I/Q yoluna uygulanır.
Her protokol için canlı RF kabulü yapılmış olduğu anlamına gelmez.

Örnek: girilen 424.00000 MHz, sinyal merkezi 423.99450 MHz:

```text
RF 423.99450 MHz
Δ -5.50 kHz · KİLİT
```

Bu kırmızı gösterilir; çözücüye verilen sinyal yine de merkezlenir. Fark -0,79 kHz
olduğunda yeşildir. `KİLİT` RF merkezine kilidi belirtir; başarılı DMR/TETRA senkronu,
anlaşılır ses veya doğru ID bilgisi için çözücü çıktısı ayrıca gerekir.
Kilit alınmamışsa mevcut ham FFT `Tepe ≈ ...` ölçümü gösterilebilir. Kilit geçici
olarak sinyal bekliyorsa gri `BEKLE` görünür; eski bir kilit aktif gibi gösterilmez.

## Teknik kurallar

1. Ortak PeakMonitor FFT'si kullanılır; yeni USB bağlantısı açılmaz. Kilit, tek
   bir FSK tepesinden değil gürültü üstündeki sinyal bölgesinin güç ağırlıklı
   merkezinden hesaplanır. Böylece modülasyon loblarını takip etme azaltılır.
2. Kanal eşiği, yerel gürültünün en az 12 dB üstünde tepe ve uygun bant genişliği
   gerekir. Gürültü, arama sınırına değen ve aşırı geniş/birleşmiş bölgeler reddedilir.
   Yerel yüzde 20 gürültü tahmini, 9 bin yumuşatma ve 1,5 kHz'e kadar bölge
   birleştirme kullanılır. Bunlar sezgisel ölçütlerdir; kalibre RF kalite ölçümü değildir.
3. Aday merkez nominal frekanstan en fazla ±6500 Hz uzakta olmalıdır. Başka bir
   yapılandırılmış kanalın frekansına daha yakın aday seçilmez. İlk edinimde uygun
   adayların en güçlü toplam güce sahip olanı seçilir. Yakın sinyallerin kimliği
   spektrumdan doğrulanamaz; kalabalık bantta manuel seçim gerekebilir.
4. 0,5 saniye içinde iki ölçümün merkezleri 750 Hz içinde uyuşmalıdır. Kilit alındıktan
   sonra başka güçlü sinyal geldi diye çağrı ortasında ona atlanmaz. Aynı sinyal
   merkezinin 1,5 kHz çevresindeki gözlem kilidi sürdürür. 0,8 saniye sinyal kaybında
   kilit bırakılır, nominal alıma dönülür ve yeniden arama yapılır.
5. Faz sürekliliğini koruyan kompleks sayısal karıştırıcı, sadece ilgili kanalın
   çözücüye giden I/Q kopyasını kaydırır. Ortak tuner, PPM ve diğer kanalların
   akışı değiştirilmez. Tek alıcının kullanılabilir RF bandı hesabı bu payı içerir.
6. Kayıtların nominal kanal frekansı korunur. Kilit/bırakma ve fark arşiv olay
   günlüğünde `RF takip` olarak yazılır. Otomatik protokol günlüğündeki
   `tuning_changed: false` yapılandırılmış/donanım frekansının korunmasını anlatır.
7. Kalibrasyon ayrı kalır: doğru referansla PPM düzeltmesi tüm alıcıyı düzeltir;
   burada yapılan kanal başına sınırlı telafidir. Çalışan +15 PPM değiştirilmedi.
   ±12,5 kHz komşu sinyal/kalite alarmı bu uygulamaya dahil değildir.

## Doğrulama ve sınırlar

- Ayrı hazırlık kopyasında `Check-Radia.ps1`: Ruff, biçim, ty, basedpyright ve
  **128 test başarılı**. Faz sürekliliği, ±6,2 kHz'e kadar sentetik FSK/QPSK
  merkezleme, ±7/12,5 kHz reddi, gürültü, komşu kanal, kilit tutma/bırakma,
  güçlü aday seçimi, ±2 kHz renk sınırları ve ayarların değişmemesi kapsandı.
- Gerçek kurulu DSD-FME/TetraBridge ile kamuya açık DMR discriminator örneğinden
  I/Q yeniden oluşturuldu. Ayrı ayrı -5,5 ve +5,5 kHz kayma uygulandı.
  Her ikisinde 0,2 saniyede kilit alındı, Otomatik mod DMR tanıdı ve üç korumalı
  ses kaydı oluştu (2,16 / 5,76 / 11,16 sn); analog kayıt oluşmadı.
  Bu **yeniden oynatım testidir**, canlı RF veya dinlenmiş anlaşılır ses kabulü değildir.
  Sonuç: `data/validation-follow/run-20260930-100038/validation.json`.
- 1120/1280/1600/1920 piksel pencere genişliklerinde gösterge taşması/örtüşmesi
  Tk geometrisiyle kontrol edildi. Yerel kaynak ve wheel/sdist derlemesi başarılı.
- Kaynak dosyalar ana projeye SHA256 eşleştirmesiyle aktarıldı. Öncesinin yedeği:
  `data/backups/signal-follow-20260930-100439`.
- Yeni RF takip özelliğinin gerçek USB/telsiz kabulü, zayıf/kalabalık bantlar,
  uzun süre ve çok kanallı işlemci yükü testi bekliyor. Önceki +15 PPM manuel
  DMR kayıt başarısı yeni takip özelliğinin canlı kabulü olarak sayılmaz.

### İlk gerçek USB gözlemi — aynı gün 10:07

Yeniden açmadan önce son kayıtlı kanalın kullanıcı tarafından 427.550 MHz / AUTO
yapıldığı görüldü; önceki 424 MHz test ayarına geri çevrilmedi. Uygulama +15 PPM
ile açıldı. Olay günlüğü 10:07:45'te 427.548131 MHz RF kilidi / -1869 Hz farkı
doğruladı. Telemetride AUTO → TETRA, CC 18, Main_Carrier 1094 ve değişken BER
(örneklerde %0–1,9) görüldü. Fark yeşil aralıktadır. Tür göstergesinde aralıklı
bilinmiyor/TETRA geçişleri de görüldü; kesintisiz ses başarısı çıkarılmadı.

0,06 sn'lik bir korumalı TETRA dosyası oluştu (1241 bayt, protocol_slot 4,
ID/grup boş). Bu kısa çıktı anlaşılır konuşma kabulü sayılmaz. Gerçek USB'de
RF kilidi ve TETRA verisi gözlendi; ±5,5 kHz kontrollü DMR canlı testi ve
anlaşılır konuşma kabulü halen bekliyor.

## Canlı kabul denemesi

Önce telsiz ve ekran 424.00000 MHz, mevcut +15 PPM ile tek etkin DMR kanalında
bir kısa konuşma denenir. Kontrollü takip denemesinde telsiz frekansı sabit
tutularak kullanıcı ekran frekansını geçici olarak 423.99450 MHz yapabilir:
beklenen fark yaklaşık +5,5 kHz, kırmızı RF kilidi ve çözülen kayıttır. Gerçek
artık sapma bu farkı etkiler. Ardından ekran 424.00000 MHz'e geri getirilir;
±2 kHz içinde yeşil beklenir. Otomatik mod ayrıca seçilerek denenebilir.
Kullanıcının çalışan frekansı test amacıyla kendiliğinden değiştirilmez.
