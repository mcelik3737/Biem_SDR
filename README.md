# BİEM Radio Integrated Solution — BM-ICC-08

**1 Ekim 2026 — BIEM-ICC-SERVER:** Bu dal, mevcut masaüstünü koruyarak şifreli yönetici/kullanıcı girişi, ekran ve kanal bazlı yetkilendirme, merkezi alım ve tarayıcı istemcileri ekler. Yeni başlatıcı `Start-BIEM-ICC-SERVER.cmd`. [Sunucu kurulum ve kullanım kılavuzu](docs/SERVER_CLIENT.md). Aşağıdaki masaüstü talimatları eski uygulama için geçerlidir.

Güncel ürün adı budur. Eski `biem_radia` paket adı, `.radia` kayıt biçimi ve mevcut başlatıcılar geriye uyumluluk için korunur. Yeni başlatıcı: `Start-BM-ICC-08.cmd`; yönetici: `Start-BM-ICC-08-Admin.cmd`. Model adı kapasite doğrulaması değildir.

Windows üzerinde RTL-SDR ile analog FM ve DMR alımı, konuşma kaydı ve yerel ses arşivi. Analog ses ve gerçek RF'den çözülen DMR sesinin anlaşılırlığı kullanıcı tarafından doğrulandı. Saha kabulü tamamlanmış kesintisiz kayıt sistemi değildir.

**30 Eylül 2026 güncellemesi:** Etkin kanala göre yerleşen dokunmatik konsol, açık/koyu tema, kanal başına canlı dinleme ve ses göstergesi, mesaj sayacı, arşivde slot/CC ayrıntıları ve Türkiye çevrimdışı yol/uydu haritaları. [Güncel kullanım ve doğrulama](docs/TOUCH_CONSOLE_2026-09-30.md), [yedek ve geri yükleme](docs/BACKUP_2026-09-30.md), [tarih etiketli konuşma arşivi](docs/conversations/BIEM_SDR_KONUSMALAR_2026-09-12_2026-09-30.md). Canlı dinlemenin yeni akışı gerçek RF kabul testi bekliyor.

## Başlatma

`D:\Projects\Biem\_SDR\Start-BM-ICC-08.cmd` dosyasını çift tıklayın. SDR# aynı USB alıcıyı kullanıyorsa önce SDR# alımını durdurun. SDR# dosyaları ve sürücü kurulumu değiştirilmez.

Yeni kurulum için Python 3.12+ (bu PC'de 3.14, 64 bit), Tk ve uv gerekir:

```powershell
cd D:\Projects\Biem\_SDR
python -m pip install uv
.\Setup-Radia.ps1
.\Setup-DMR.ps1
.\Setup-TETRA.ps1
.\Start-BM-ICC-08.cmd
```

Kurulum, RTL-SDR kullanıcı alanı kütüphanesini yalnızca projenin `vendor` klasörüne indirir; Windows USB sürücüsü kurmaz veya değiştirmez. Bu PC'nin mevcut USB sürücüsüyle donanım erişimi doğrulandı.

## İlk canlı test

1. Kanal: **PMR 01**, frekans: **446.00625 MHz**, aralık: **12500 Hz**, filtre: **12500 Hz**.
2. **Alımı başlat** düğmesine basın; `ALIM HAZIR` ve kanal dBFS ölçümünü bekleyin.
3. USB kazancı başlangıçta 19 dB'dir; tuner en yakın desteklenen değeri kullanır. Sabit kazanç, otomatik kazancın gürültü eşiğini kaydırmasını önler. Bu alıcıda 19 dB ile boş kanal yaklaşık −59 dBFS ölçüldü. Squelch eşiğini gürültü seviyesinin üzerinde, konuşma seviyesinin altında seçin. Eşik değişikliğini alımı durdurup **Ekle / güncelle** ile kaydedin. USB kazancı alanı rtl_tcp kaynağına uygulanmaz; o kaynak otomatik tuner kazancı kullanır.
4. 5–10 saniye konuşun, bırakın; 2–3 saniye bekleyip tekrar konuşun.
5. Squelch kapandıktan yaklaşık 0,6 saniye sonra kayıt arşive eklenir. Kanal adı ve `YYYY-MM-DD` yerel tarihle arayın. Kaydı seçip **Seçili kaydı dinle** düğmesine basın veya çift tıklayın.

Alıcı açıkken giriş kutularını değiştirmek çalışan kanal ayarlarını değiştirmez. Etkin kanallar alımda kullanılır. 0,3 saniye ön tampon ve 0,6 saniye son bekleme analog kayda dahildir; süre, ses dosyasının gerçek süresidir. Eşik üstü taşıyıcı/gürültü de kayıt açabilir. Kayıt en fazla 90 saniye; sonra 2 saniye ara verilir. TETRA sessiz taşıyıcı beklemesi en fazla 20 saniyedir.

## Kayıtların konumu

- `data/recordings/YYYY-MM-DD/`: analog 16 kHz, DMR 8 kHz; 16 bit, mono ses. Masaüstünde tamamlanan kayıtlar `.wav.radia` biçiminde Windows DPAPI ile korunur.
- `data/radia.sqlite3`: UTC başlangıç zamanı, kanal, frekans, süre, kaynak ve kapanma nedeni. Ekran ve tarih araması PC'nin yerel saatini kullanır.
- `data/radia.log`: teknik hatalar; SQLite `events` tablosu alım başlangıcı ve hata olaylarını içerir.
- `data/channels.json`: kaydedilen kanal ayarları.
- `data/receiver.json`: PPM, USB kazancı ve kaynak ayarları.
- `data/receiver-status.json`: en son alıcı telemetrisi; geçmiş izleme servisi değildir.

Açık kayıt ve çözücünün geçici WAV dosyaları tamamlanana kadar düz ses içerebilir. Ani elektrik kesintisinden kalan `.part` veya veritabanına eklenememiş WAV dosyalarını silmeyin. Arşiv dinlemek için uygulama aynı Windows hesabıyla yönetici olarak açılır. DPAPI koruması Windows profiline bağlıdır; yalnız dosyayı başka PC'ye kopyalamak oynatmayı garanti etmez. Ayrıntılar: [kayıt koruması](docs/SECURITY_AND_DIGITAL_DATA.md). Saklama süresi ve disk kotası henüz uygulanmaz.

## Eşzamanlı kanallar ve Ethernet

**Alım biçimi → Tarama**, etkin kanalları liste sırasıyla gezer; uzak frekanslar da eklenebilir. Kanalın **Squelch / dBFS** eşiği aşılınca orada kalır; sinyal **Eşik altı bekle / sn** boyunca düşük kalınca devam eder. **Kanalı dinle / sn** boş kanaldaki gözlem süresidir. Kanal değişimi ve DMR çözücüsünün açılıp kapanması ek zaman alır. Başka kanallarda başlayan konuşmalar kaçırılabilir. **Sabit** modu önceki eşzamanlı bant içi alımdır. Ayar değişikliklerini alımı durdurup kaydederek uygulayın.

Listede 1–8 analog kanal tanımlanabilir. Hepsi aynı 960 kS/s I/Q akışından çözülür. Kanallar alıcının güvenli bant sınırına sığmıyorsa başlatma reddedilir. Aynı USB tuner ile birbirinden uzak VHF ve UHF kanallarını eşzamanlı almak mümkün değildir; ayrı alıcı gerekir. İki eşzamanlı kanal sentetik sinyalle test edildi; sekiz kanal için donanım performans kabul testi bekliyor.

`rtl_tcp` kaynağı Ethernet üzerinden **RTL-SDR I/Q** alır. Kaynak PC'de rtl_tcp sunucusu çalışmalı; adres ve port girilmelidir. Bu protokol Hytera repeater ses/veri protokolü değildir. rtl_tcp bağlantısı kimlik doğrulama/şifreleme sağlamaz; uygulama bir ağ dinleme portu açmaz. Yerel protokol test sunucusunda başlık, komutlar, parçalı veri ve bağlantı kopması test edildi; gerçek Ethernet cihazı testi henüz yapılmadı.

## DMR ve dispatcher kapsamı

DMR için ayrı discriminator ve DSD-FME backend'i, çağrı WAV'ları, kaynak/hedef ID, color code ve sistem bazında isim eşleştirmeleri eklendi. Arşiv tarih, isim, ID ve bildirilen slot üzerinden aranabilir. Ayrıntılı kullanım ve kabul durumu: [DMR kılavuzu](docs/DMR.md).

Analog kayıtların kimlikleri boş kalır. DMR simplex olayında çözücü fiziksel slot bildirmezse slot tahmin edilmez. Aynı ID ve saniyeyle iki slota birden eşleşen dosyalar otomatik atanmaz; özgün dosya korunur. Gerçek eşzamanlı iki slot ve Hytera repeater IP entegrasyonu henüz doğrulanmadı. 6,25 kHz seçimi dPMR desteği sağlamaz.

## Geliştirme

```powershell
python -m uv sync --locked
.\Check-Radia.ps1
python -m uv build
```

Testler donanımdan bağımsızdır; gerçek USB'yi açmaz ve canlı yayınları test verisi olarak kullanmaz. Kaynak kod `src/biem_radia`, testler `tests` altındadır. `data`, `vendor` ve `external` Git dışında tutulur.

Git deposu bu proje klasöründe; `origin`: https://github.com/mcelik3737/Biem_SDR.git . Doğrulanmış analog sürüm `analog-verified-2026-09-12` etiketiyle korunur. Eski C++ taslağı `working-before-cleanup-2026-09-30` etiketinden geri alınabilir. Ses kayıtları, ID ayarları ve çalışma verileri Git dışında kalır. Büyük haritalar ayrı Release ekleridir.

## Referanslar ve lisans sınırı

- [Hytera Smart Dispatch Plus](https://www.hytera.com/eu/products/smart-dispatch-plus.html): ürün kapsamı referansı; bu prototip Hytera uyumluluğu iddia etmez.
- [SDR++](https://github.com/AlexandreRouma/SDRPlusPlus): araştırma referansı; kullanılmayan klon yerel arşive taşındı. Commit kimlikleri `docs/maps/REMOVED_REFERENCE_CHECKOUTS_2026-09-30.json` içinde. SDR++ kodu uygulamaya kopyalanmadı.
- [librtlsdr API](https://github.com/osmocom/rtl-sdr/blob/master/include/rtl-sdr.h) ve [rtl_tcp protokolü](https://github.com/osmocom/rtl-sdr/blob/master/src/rtl_tcp.c).

Üçüncü taraf bağımlılıkların sürüm ve dağıtım bilgileri `docs/THIRD_PARTY.md` içindedir.
