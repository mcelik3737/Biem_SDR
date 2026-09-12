# BİEM Radia Dispatcher

Windows üzerinde RTL-SDR ile analog FM alımı, taşıyıcı/squelch tabanlı konuşma kaydı ve yerel ses arşivi. İlk çalışan prototiptir; saha kabul testi tamamlanmadan kurumsal kesintisiz kayıt sistemi olarak değerlendirilmemelidir.

## Başlatma

`D:\Projects\Biem\_SDR\Start-Radia.cmd` dosyasını çift tıklayın. SDR# aynı USB alıcıyı kullanıyorsa önce SDR# alımını durdurun. SDR# dosyaları ve sürücü kurulumu değiştirilmez.

Yeni kurulum için Python 3.12+ (bu PC'de 3.14, 64 bit), Tk ve uv gerekir:

```powershell
cd D:\Projects\Biem\_SDR
python -m pip install uv
.\Setup-Radia.ps1
.\Start-Radia.cmd
```

Kurulum, RTL-SDR kullanıcı alanı kütüphanesini yalnızca projenin `vendor` klasörüne indirir; Windows USB sürücüsü kurmaz veya değiştirmez. Bu PC'nin mevcut USB sürücüsüyle donanım erişimi doğrulandı.

## İlk canlı test

1. Kanal: **PMR 01**, frekans: **446.00625 MHz**, aralık: **12500 Hz**, filtre: **12500 Hz**.
2. **Alımı başlat** düğmesine basın; `ALIM HAZIR` ve kanal dBFS ölçümünü bekleyin.
3. USB kazancı başlangıçta 19 dB'dir; tuner en yakın desteklenen değeri kullanır. Sabit kazanç, otomatik kazancın gürültü eşiğini kaydırmasını önler. Bu alıcıda 19 dB ile boş kanal yaklaşık −59 dBFS ölçüldü. Squelch eşiğini gürültü seviyesinin üzerinde, konuşma seviyesinin altında seçin. Eşik değişikliğini alımı durdurup **Ekle / güncelle** ile kaydedin. USB kazancı alanı rtl_tcp kaynağına uygulanmaz; o kaynak otomatik tuner kazancı kullanır.
4. 5–10 saniye konuşun, bırakın; 2–3 saniye bekleyip tekrar konuşun.
5. Squelch kapandıktan yaklaşık 0,6 saniye sonra kayıt arşive eklenir. Kanal adı ve `YYYY-MM-DD` yerel tarihle arayın. Kaydı seçip **Seçili kaydı dinle** düğmesine basın veya çift tıklayın.

Alıcı açıkken giriş kutularını değiştirmek çalışan kanal ayarlarını değiştirmez. Listede görünen kanallar alımda kullanılır. 0,3 saniye ön tampon ve 0,6 saniye son bekleme kayda dahildir; süre, WAV dosyasının gerçek süresidir. Bu algoritma insan konuşması tanımaz; eşik üstü taşıyıcı/gürültü de kayıt açabilir. Sürekli taşıyıcı 180 saniyelik parçalara bölünür.

## Kayıtların konumu

- `data/recordings/YYYY-MM-DD/`: 16 kHz, 16 bit, mono WAV; kullanıcı kanal adı dosya yolu olarak kullanılmaz.
- `data/radia.sqlite3`: UTC başlangıç zamanı, kanal, frekans, süre, kaynak ve kapanma nedeni. Ekran ve tarih araması PC'nin yerel saatini kullanır.
- `data/radia.log`: teknik hatalar; SQLite `events` tablosu alım başlangıcı ve hata olaylarını içerir.
- `data/channels.json`: kaydedilen kanal ayarları.
- `data/receiver-status.json`: en son alıcı telemetrisi; geçmiş izleme servisi değildir.

Açık kayıt `.wav.part` uzantısıyla tutulur; normal durdurma veya yakalanan bağlantı hatasında WAV tamamlanır. Ani elektrik kesintisinden kalan `.part` veya veritabanına eklenememiş WAV dosyaları otomatik kurtarılmaz; silmeyin. İlk sürüm kayıt silmez, saklama süresi uygulamaz, disk kotası veya kullanıcı yetkilendirmesi sunmaz. Yedekleme ve disk kapasitesi saha aşamasında ayrıca yapılandırılmalıdır.

## Eşzamanlı kanallar ve Ethernet

Listede 1–8 analog kanal tanımlanabilir. Hepsi aynı 960 kS/s I/Q akışından çözülür. Kanallar alıcının güvenli bant sınırına sığmıyorsa başlatma reddedilir. Aynı USB tuner ile birbirinden uzak VHF ve UHF kanallarını eşzamanlı almak mümkün değildir; ayrı alıcı gerekir. İki eşzamanlı kanal sentetik sinyalle test edildi; sekiz kanal için donanım performans kabul testi bekliyor.

`rtl_tcp` kaynağı Ethernet üzerinden **RTL-SDR I/Q** alır. Kaynak PC'de rtl_tcp sunucusu çalışmalı; adres ve port girilmelidir. Bu protokol Hytera repeater ses/veri protokolü değildir. rtl_tcp bağlantısı kimlik doğrulama/şifreleme sağlamaz; uygulama bir ağ dinleme portu açmaz. Yerel protokol test sunucusunda başlık, komutlar, parçalı veri ve bağlantı kopması test edildi; gerçek Ethernet cihazı testi henüz yapılmadı.

## DMR ve dispatcher kapsamı

Analog FM akışında otomatik DMR ID, grup veya slot bulunmaz. Veritabanındaki bu alanlar analog kayıtlar için **NULL** bırakılır, arayüzde `—` gösterilir. DMR ses çözücü, ID/alias eşlemesi ve üretici repeater entegrasyonu henüz uygulanmadı. DMR, yalnızca daha dar FM filtresi seçilerek çözülemez; kanal aralığı, hava arayüzü ve ses kodlayıcı ayrı konulardır. 6,25 kHz kanal seçeneği tek başına dPMR veya DMR desteği anlamına gelmez.

Sonraki aşama için gerçek telsiz/repeater modeli, analog/DMR modu, izinli test kanalı ve üreticinin ses/olay arayüz belgesi gerekir. Dijital metadata gerçek çözücüden gelmeden kimlik ataması yapılmayacak.

Bu kapsam (DMR dijital çözme, Hytera repeater network entegrasyonu, Qt6
masaüstü GUI) ayrı, bağımsız bir repoda (C++/Qt) tamamlayıcı bir hat
olarak sürüyor: [mcelik3737/Biem_SDR_V1](https://github.com/mcelik3737/Biem_SDR_V1).
İki teknoloji/araç karışmasın diye bu repodan tamamen ayrıldı — burada bu
repoyla dosya/dal paylaşmıyor.

## Geliştirme

```powershell
python -m uv sync --locked
.\Check-Radia.ps1
python -m uv build
```

Testler donanımdan bağımsızdır; gerçek USB'yi açmaz ve canlı yayınları test verisi olarak kullanmaz. Kaynak kod `src/biem_radia`, testler `tests` altındadır. `data`, `vendor` ve `external` Git dışında tutulur.

Git deposu bu proje klasöründe, çalışma dalı `codex/analog-mvp`. `origin`: https://github.com/mcelik3737/Biem_SDR.git . İlk teslimde bağlantı ve yerel commit hazırlanır; uzak depoya push yapılmaz. Ses kayıtları ve çalışma verileri Git dışında kalır.

## Referanslar ve lisans sınırı

- [Hytera Smart Dispatch Plus](https://www.hytera.com/eu/products/smart-dispatch-plus.html): ürün kapsamı referansı; bu prototip Hytera uyumluluğu iddia etmez.
- [SDR++](https://github.com/AlexandreRouma/SDRPlusPlus): `external/SDRPlusPlus` altında bağımsız referans klonu, doğrulanmış commit kimliği için `docs/THIRD_PARTY.md` dosyasına bakın. SDR++ kodu uygulamaya kopyalanmadı.
- [librtlsdr API](https://github.com/osmocom/rtl-sdr/blob/master/include/rtl-sdr.h) ve [rtl_tcp protokolü](https://github.com/osmocom/rtl-sdr/blob/master/src/rtl_tcp.c).

Üçüncü taraf bağımlılıkların sürüm ve dağıtım bilgileri `docs/THIRD_PARTY.md` içindedir.
