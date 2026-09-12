# DMR alımı

Önce `Setup-Radia.ps1`, ardından `Setup-DMR.ps1` çalıştırın. DMR çözücü proje içindeki `vendor` klasöründe tutulur. Kanal modunu DMR, kanal aralığını 12500 Hz seçin; frekans, sistem adı ve biliniyorsa color code girin. Yalnızca etkin kanallar alınır. PPM ve alıcı ayarları `data/receiver.json` içinde saklanır; değişiklikler alımı yeniden başlatınca uygulanır.

I/Q akışı ayrı DMR discriminator yolundan 48 kHz S16LE olarak yerel DSD-FME sürecine gönderilir. Analog ses filtresi, de-emphasis ve squelch dijital yola uygulanmaz. Çözücünün tamamladığı 8 kHz mono konuşma WAV'ları ve eşleşen olay metadata'sı SQLite arşivine alınır. İsim eşleştirmeleri sistem bazında cihaz veya grup ID'sine uygulanır. Tarih, kanal, isim, ID ve slot üzerinden arama yapılabilir. Analog kayıtların kimlik alanları boş kalır.

## Doğrulama ve sınırlar

- Analog ses kullanıcı tarafından doğrulandı. Gerçek RF'den yakalanıp frekans sapması düzeltilmiş DMR kaydının anlaşılır olduğu da kullanıcı tarafından doğrulandı. Kaynak ID, hedef grup ve color code çözüldü. Kalıcı tuner düzeltmesiyle canlı alımdan arşive kayıt testi de 2026-09-12 tarihinde geçti; iki tamamlanmış WAV ve isim eşleştirmesi doğrulandı.
- İki slotun dosya ve metadata ayrımı otomatik testlerle doğrulandı; aynı anda iki gerçek RF slotu kabul testi bekliyor.
- DSD-FME bazı simplex/DMO olaylarında fiziksel slot bildirmez. Bu durumda slot `—` kalır; telsizde ayarlanmış değerden tahmin edilmez.
- Çözücünün dosya adında slot yoktur. Aynı saniyede aynı ID/CC değerleriyle iki slot olayı eşleşirse kayıt yanlış kişiye/slot'a bağlanmaz; özgün dosya oturum klasöründe korunur ve uyarı yazılır. Bu durum için ek çözücü entegrasyonu gereklidir.
- Başlangıç zamanı çözücünün son olay zamanı eksi WAV süresidir; saniye çözünürlüğündeki bu tahmin örnek hassasiyetinde çağrı başlangıcı değildir.
- Şifreli olaylar içe alınmaz. Hytera repeater IP protokolü entegrasyonu yoktur; Ethernet seçeneği rtl_tcp I/Q içindir.
- `data/dmr-sessions` çözücü olaylarını, günlükleri ve özgün dosyaları tutar. TEMP dosyaları tamamlanmış kayıt sayılmaz ve silinmez. Otomatik saklama/kota henüz yoktur.
- İsteğe bağlı `BIEM_DMR_DIAGNOSTIC=1` her oturumun ilk 120 saniyesinde discriminator WAV'ı saklar. Normal kullanımda kapalıdır.

## Sabitlenmiş bağımlılık

[DSD-FME 20260715](https://github.com/lwvmobile/dsd-fme/releases/tag/20260715), Windows Cygwin portable; sürüm çıktısı `AW 2026-34-g69d3115`, MBElib 1.3.4. ZIP SHA256: `006cfa420e79033b51ded97ed4d2d0a9715e350ffcfe35c41e89b9e6ef00e9f8`. Dağıtım kaynak kodunu ve lisanslarını içerir; üçüncü taraf ikili dosyalar bu Git deposunda yayımlanmaz. Windows backend'i upstream tarafından deneysel olarak tanımlanır.
