# DMR alımı

Önce `Setup-Radia.ps1`, ardından `Setup-DMR.ps1` çalıştırın. DMR çözücü proje içindeki `vendor` klasöründe tutulur. Kanal modunu DMR, kanal aralığını 12500 Hz seçin; frekans, sistem adı ve biliniyorsa color code girin. Yalnızca etkin kanallar alınır. PPM ve alıcı ayarları `data/receiver.json` içinde saklanır; değişiklikler alımı yeniden başlatınca uygulanır.

I/Q akışı ayrı DMR discriminator yolundan 48 kHz S16LE olarak yerel DSD-FME sürecine gönderilir. Analog ses filtresi, de-emphasis ve squelch dijital yola uygulanmaz. Çözücünün tamamladığı 8 kHz mono konuşma WAV'ları ve eşleşen olay metadata'sı SQLite arşivine alınır. İsim eşleştirmeleri sistem bazında cihaz veya grup ID'sine uygulanır. Tarih, kanal, isim, ID ve slot üzerinden arama yapılabilir. Analog kayıtların kimlik alanları boş kalır.

## Doğrulama ve sınırlar

Arşivden DMR dinlerken ses +6 dB yükseltilir; yüksek tepelere yumuşak sınırlama uygulanır. Dinleme kopyası `data/dmr-playback.wav` dosyasına yazılır. Özgün kayıt ve RF/discriminator kazancı değiştirilmez.

- Analog ses kullanıcı tarafından doğrulandı. Gerçek RF'den yakalanıp frekans sapması düzeltilmiş DMR kaydının anlaşılır olduğu da kullanıcı tarafından doğrulandı. Kaynak ID, hedef grup ve color code çözüldü. Kalıcı tuner düzeltmesiyle canlı alımdan arşive kayıt testi de 2026-09-12 tarihinde geçti; iki tamamlanmış WAV ve isim eşleştirmesi doğrulandı.
- İki slotun dosya ve metadata ayrımı otomatik testlerle doğrulandı; aynı anda iki gerçek RF slotu kabul testi bekliyor.
- DSD-FME bazı simplex/DMO olaylarında fiziksel slot bildirmez. Eşleşen çözücü günlüğü varsa ekranda `1 (çözücü)` gösterilir; bu değer ayrı `decoder_slot` alanında tutulur. Fiziksel `slot` boş kalır ve slot filtresi bu çağrıları içermez. Günlük eşleşmezse dijital kayıtta `Doğrulanmadı` gösterilir; telsizde ayarlanmış değerden tahmin edilmez.
- Çözücünün dosya adında slot yoktur. Aynı saniyede aynı ID/CC değerleriyle iki slot olayı eşleşirse kayıt yanlış kişiye/slot'a bağlanmaz; özgün dosya oturum klasöründe korunur ve uyarı yazılır. Bu durum için ek çözücü entegrasyonu gereklidir.
- Başlangıç zamanı çözücünün son olay zamanı eksi WAV süresidir; saniye çözünürlüğündeki bu tahmin örnek hassasiyetinde çağrı başlangıcı değildir.
- Şifreli olaylar içe alınmaz. Hytera repeater IP protokolü entegrasyonu yoktur; Ethernet seçeneği rtl_tcp I/Q içindir.
- `data/dmr-sessions` çözücü olaylarını, günlükleri ve özgün dosyaları tutar. TEMP dosyaları tamamlanmış kayıt sayılmaz ve silinmez. Otomatik saklama/kota henüz yoktur.
- İsteğe bağlı `BIEM_DMR_DIAGNOSTIC=1` her oturumun ilk 120 saniyesinde discriminator WAV'ı saklar. Normal kullanımda kapalıdır.

## Arşivde slot ve CC düzeltmesi — 2026-09-30

Arşivde `ID / Grup`, `Slot`, `CC / NAC / RAN` ayrı sütunlardır. CC 0 dahil
veritabanına kaydedilmiş kodlar gösterilir; P25 NAC ve NXDN RAN değerleri CC diye
etiketlenmez. TETRA protokol slotu varsa önceliklidir. Dar pencerede yatay kaydırma
vardır. Yeni bir sinyal değeri önceki kaydın metadata'sını değiştirmez.

Çözücü-slot eşlemesindeki `Color Code=1` / `Color Code=01` farkı düzeltildi.
Sıfır dolgulu kodlar sayısal karşılaştırılır; FEC/CRC hata senkronu kabul edilmez.
Kimlik, hedef, CC ve olay saati eşleşmesi; çelişen slotları reddetme sürer.

10:24:23 / 5,76 sn ve 10:30:06 / 5,40 sn kayıtları: ID 3737, grup 3737, CC 1.
Oturum günlüğü her ikisi için `MS/DM MODE/MONO` ve `SLOT 1` veriyor. Dağıtılan
DSD-FME `sourcecode/src/dmr_ms.c` içinde `currentslot = 0` zorlanıyor (satır 65,
419; 239 ve 544'te slot 1 açıklaması). Bu yüzden bunlar fiziksel slot 1 kabulü
değildir. İki kayıt, dosya kimliği/çağrı zamanı/ID/hedef/CC kanıtı eşleştirilerek
yalnız `decoder_slot=1` ile tamamlandı; fiziksel slot boş kaldı. Ses dosyaları
değiştirilmedi. Yeniden oynatım veya iki gerçek slot testi bu düzeltmede yapılmadı.

134 donanımsız test ve kalite kontrolleri başarılı; wheel/sdist derlendi.
CC 0/1/9/11/15, sıfır dolgu, hata reddi, arşiv sütunları ve fiziksel slot filtresi
kapsandı. Kaynak yedeği `data/backups/archive-metadata-20260930-103423`;
SQLite yedeği ve onarım manifesti `data/backups/archive-metadata-db-20260930-103425`.

## Sabitlenmiş bağımlılık

[DSD-FME 20260715](https://github.com/lwvmobile/dsd-fme/releases/tag/20260715), Windows Cygwin portable; sürüm çıktısı `AW 2026-34-g69d3115`, MBElib 1.3.4. ZIP SHA256: `006cfa420e79033b51ded97ed4d2d0a9715e350ffcfe35c41e89b9e6ef00e9f8`. Dağıtım kaynak kodunu ve lisanslarını içerir; üçüncü taraf ikili dosyalar bu Git deposunda yayımlanmaz. Windows backend'i upstream tarafından deneysel olarak tanımlanır.
