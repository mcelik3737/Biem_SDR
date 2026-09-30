# BİEM Radia — Proje notları, kurallar ve arayüz tasarım brifi

**Durum tarihi:** 12 Eylül 2026 — birleştirilmiş son durum, telsiz görseli dahil  
**Amaç:** Bu tek dosya, projeyi tanımayan ChatGPT'ye arayüz tasarımı için verilebilir.  
**Ürün:** BİEM Radia Dispatcher Software — Windows masaüstü uygulaması.  
**Geliştirme:** Yerel Windows Codex oturumunda yürütülüyor.  
**Sürüm:** 0.2.0 geliştirme sürümü; saha doğrulaması devam ediyor.

> Bu metin bir tasarım ve devir belgesidir. “İstek/hedef”, “uygulandı” ve “doğrulandı” ifadeleri birbirinden ayrılmıştır. Bir düğmenin bulunması, ilgili protokolün bütün özelliklerinin sahada doğrulandığı anlamına gelmez. Diğer eski proje notlarıyla çelişirse bu tarihli durum özeti esas alınmalı, uygulama kodu ayrıca kontrol edilmelidir.

## 1. Ürün neden geliştiriliyor?

BİEM'in hizmet verdiği firmalarda, güvenlik ve iş sağlığı/güvenliği operasyonları için izinli telsiz kanallarının konuşmalarını kaydetmek, kimliklendirmek ve daha sonra kolayca bulup dinlemek amaçlanıyor.

Kaynaklar USB SDR, Ethernet üzerinden SDR I/Q akışı ve ileride Hytera röle IP Dispatch bağlantısı olacak. Öncelik alım, anlaşılır ses ve güvenilir arşivdir. RF gönderimi/PTT mevcut ürün kapsamına eklenmiş değildir.

Başlangıçta analog FM çalıştırıldı. Ardından DMR ses/kimlik kaydı, diğer dijital modlar, tarama ve yönetici spektrumu geliştirildi. Hytera Smart Dispatch Plus işlevsel bir referanstır; arayüzünün birebir kopyalanması istenmiyor.

## 2. Kullanıcının tasarım beklentisi

- Windows masaüstü programı gibi anlaşılır, açık renkli, düzenli ve sade görünüm.
- BİEM logoları ve kurumsal kimliği kullanılmalı.
- Operatör günlük işini teknik ayarlarla boğuşmadan yapabilmeli.
- Alım, kayıt, bekleme, tarama, cihaz hatası ve devre dışı durumları açıkça ayrılmalı.
- Altı kanal ayrı kutularda görülebilmeli; her kutuda sinyal seviyesi ve gelen veri bulunmalı.
- RF kazancı, AGC, eşikler ve bant ayarları gerektiğinde kolay ulaşılabilir olmalı.
- Spektrum, SDR# benzeri frekans/seviye grafiği ve şelale sunmalı; sağ/sol sürgülerle ayarlanabilmeli.
- FM RADIO üstte açılıp kapanabilen yardımcı bölüm olmalı; ana telsiz işini etkilememeli.
- Yeni özellikler eklenmeye devam edeceğinden tasarım büyümeye uygun olmalı.

## 3. Değiştirilmemesi gereken temel kurallar

1. Çalışan analog ve DMR alımı korunmalı; görsel değişiklikler ses/kayıt hattını bozmamalı.
2. Kullanıcının çalışan SDR# kurulumu, DLL'leri, ayarları ve USB sürücüleri korunmalı.
3. Cihaz ID, grup, fiziksel slot veya çağrı adı tahminle doldurulmamalı. Bilinmeyen değer açıkça bilinmiyor gösterilmeli.
4. Analog FM'de cihaz ID/grup/slot bulunmuş gibi gösterilmemeli.
5. Yapılandırılmış kanal modu ile RF'den gerçekten çözülen protokol birbirinden ayrılmalı.
6. dBFS, dBm olarak etiketlenmemeli. Kalibre edilmiş güç ölçümü henüz yok.
7. FFT tepe eşiği, kanal gücü/squelch eşiği, RF kazancı ve ses seviyesi ayrı kavramlardır; arayüz bunları karıştırmamalı.
8. Sentetik test, gürültü kaydı veya örnek dosya başarısı gerçek saha konuşması doğrulaması sayılmamalı.
9. Aynı fiziksel USB alıcı iki farklı iş tarafından habersizce yeniden ayarlanmamalı.
10. Kayıtlar aynı dosya adı nedeniyle ezilmemeli. Kapanışta devam eden kayıtlar güvenle tamamlanmalı; kurtarılabilir dosyalar silinmemeli.
11. RF ses/metadata çözülemediğinde sahte başarı gösterilmemeli. Hata, bilinmiyor ve bekliyor durumları ayrılmalı.
12. TETRA'da şifreleme durumu belirsiz/şifreli çağrılar açık ses kaydı gibi içe alınmamalı; güvenli çağrı kimliği eşleşmesi olmadan SSI/GSSI atanmamalı.
13. Önemli kod değişikliklerinde `Check-Radia.ps1` ve `python -m uv build` çalıştırılmalı. Donanımsız testler gerçek SDR açmamalı.
14. Çalışan alıcı kodunu değiştirmeden önce uygulama normal yolla durdurulmalı/kapatılmalı.
15. Üçüncü taraf uygulamalara mesaj/veri gönderimi ayrıca yetkilendirilmelidir. Bu brifin hazırlanması otomatik ChatGPT yüklemesi anlamına gelmez.

## 4. Mevcut ekran yapısı

Üst başlıkta BİEM logosu, RADIA adı, çalışma durumu ve açılır **FM RADIO** paneli var.

| Sekme | Mevcut içerik |
|---|---|
| Canlı Kanallar | Alımı başlat/durdur, kanal kaydet, RF gain/AGC, Sabit/Tarama, altı kanal kutusu |
| Kayıt Arşivi | Yerel gün ve metin/kimlik araması, fiziksel/protokol slot filtresi, kayıt tablosu, yönetici yetkili dinleme |
| Alıcı / Gelişmiş Ayarlar | USB/rtl_tcp, adres/port, PPM/gain, kanal aralığı/filtre ve isim eşleştirmeleri |
| Hytera Ethernet | HR659 için çevrimdışı bağlantı ayarları; gerçek IP ses sürücüsü henüz yok |
| SDR Cihazları | USB ürün/seri/index listesi, seçilen cihaz, Ethernet adres bilgileri |
| Spektrum / Yönetici | Frekans aralığı, FFT/şelale, kazanç/eşik/ölçek, tepeler ve fare kilidi |
| Harita | Son geçerli DMR konumu, çevrimdışı paketler, zoom ile ölçeklenen telsiz görseli |
| Dijital Veri Günlüğü | DMR/TETRA ham çıktı ve veri metinleri; kategori filtresi |
| BİEM | Logo, şirket bilgileri ve web bağlantısı |

Bu sekmeler mevcut uygulamanın fotoğrafıdır; tasarımcı daha iyi bir bilgi mimarisi önerebilir. İşlevler kaybolmamalıdır.

## 5. Kanal kutuları ve protokoller

Her kanal kutusunda etkinlik, kanal adı, mod, frekans, erişim kodu, eşik, sinyal göstergesi ve veri satırı bulunur. Kanal düzenleme alım sırasında kilitlenir; donanım kazancı ayrı kontrolle alım sırasında değişebilir.

| Mod | Ayar | Gerçek durum |
|---|---|---|
| Analog / NFM | CSQ, CTCSS, DCS, ters DCS | Analog konuşma kullanıcı tarafından anlaşılır bulundu. Ton filtreleri sentetik test edildi; bütün ton seçenekleri için saha kabulü yok. |
| DMR | Color code 0–15 veya tümü | Gerçek RF konuşma anlaşılır bulundu; ID ve hedef/grup değişimleri görüldü. Bütün iki-slot/eşzamanlı senaryolar doğrulanmış değil. |
| TETRA | Color code 0–63 veya tümü | Yerel çözücü çalışıyor. Kullanıcı ses duydu; kesik ses ve çok kısa kayıt problemi açık. Tam kabul edilmiş özellik sayılmamalı. |
| APCO25 | NAC 0–4095, ondalık giriş | Phase 1 örnek dosyada ses/kimlik testi yapıldı. Phase 2 ve saha testi yok. |
| NXDN | RAN 0–63 | NXDN96 örnek dosyada test edildi. NXDN48 ve saha kabulü bekliyor. |

CTCSS seçenekleri standart 67–254,1 Hz tonlarıdır. DCS ve ters DCS birbirine otomatik çevrilmez. Kanal aralıkları 6,25 / 12,5 / 25 kHz seçenekleriyle, protokole uygun olarak kullanılır. Kanal aralığı, RF filtre genişliği ve frekans adımı aynı şey değildir.

### DMR kimlik ve slot ayrımı

- Cihaz ID, grup ID, özel çağrı hedefi ve isim eşleştirmeleri ayrı tutulur.
- İsim eşleştirmesi sistem/müşteri kapsamına bağlıdır; farklı firmaların aynı ID'leri karışmamalı.
- Fiziksel TDMA slotu ile çözücünün dahili ses kanalı/lane bilgisi ayrıdır.
- Simplex kayıtta yalnız çözücü kanalı biliniyorsa `1 (çözücü)` gibi işaretlenir; fiziksel slot doğrulanmış gibi sunulmaz.
- Aynı zaman/ID için slot eşleştirmesi belirsizse yanlış otomatik eşleştirme yapılmaz; kaynak dosya korunur.

### XPT ve Capacity Plus

Ses için mevcut DMR çözümü temel alınabilir. DSD-FME kaynaklarında Hytera XPT ve Motorola Capacity Plus kontrol verisi ve trunk takip desteği görüldü. Ancak **Radia'da frekans/slot yönlendirmelerini izleyen otomatik trunk entegrasyonu yok**. Bu sistemlerde başarılı saha testi yapılmış değildir. Yerel iki ham örnekten biri boş, diğerinden XPT/Capacity Plus tanıması elde edilmedi.

## 6. Kayıt ve arşiv kuralları

**Kural:** En fazla 90 saniye kayıt → 2 saniye kayıt arası → sinyal/ses devam ediyorsa yeni kayıt.

- Analog: süre örnek sayısıyla uygulanır; iki saniyelik ara ön kayıt tamponuna geri alınmaz.
- TETRA: dört slotun tamponları ayrıdır; her slotta 90 saniye sınırı ve iki saniye ara uygulanır.
- DMR/APCO25/NXDN: DSD-FME dosyayı çağrı bitince teslim eder. Arşive aktarımda 0–90, 92–182, 184–274… saniye aralıkları ayrı dosyalar olur. **Arşiv parçaları çağrı bitince görünür.** Canlı 90 saniyelik dosya teslimi henüz yok.
- DSD-FME'nin kaynak/teşhis WAV'ları bu arşiv sınırıyla kesilmiyor.
- Doğal konuşma bitişinde ayrıca zorunlu iki saniye ara eklenmez; ara maksimum süre kesiminden sonradır.
- Eski kayıtlar bu yeni süre kuralıyla topluca değiştirilmedi.

### Dosya adları

```text
Analog: analog_2026-09-12_17_20_30_4.68sn.wav.radia
DMR:    3737_3411_2026-09-12_17_20_30_4.68sn.wav.radia
        cihazID_grupID_tarih_saat_dakika_saniye_süre.wav.radia
```

- Tarih/saat PC'nin yerel saatidir; veritabanında UTC bilgisi tutulur.
- Süre gerçek WAV süresidir. Aynı isimde dosya varsa `_02` benzeri ekle çakışma önlenir.
- Bilinmeyen ID/grup `bilinmiyor` olarak kalır. Özel çağrı hedefi grup alanına yazılmaz.
- TETRA'da kimlik eşleştirmesi henüz güvenilir kurulmadığı için ses kayıtlarında kimlikler bilinmiyor kalabilir; gerçek slot ayrı saklanır.
- Tarih, kanal/başlık, isim ve ID ile bulunup dinleme ürünün ana işlevlerinden biridir.
- DMR arşiv dinlemesinde RAM içinde +6 dB ve yumuşak sınırlama uygulanır; düz geçici dinleme dosyası oluşturulmaz, orijinal kayıt değiştirilmez.
- Daha önce 27 kaydın adları yedek/manifest ile dönüştürüldü, ses baytlarının değişmediği hash kontrolüyle doğrulandı.

## 7. Tarama davranışı: iki farklı tarama var

### A. Konuşma kanallarını tarama

- Kullanıcının belirlediği etkin kanallar sırayla alınır; ilk hedef beş frekansı altı kutu üzerinden denemektir.
- Varsayılan kanal gözlem süresi 1 saniye; eşik altı bekleme de 1 saniyedir. Ayarlanabilir.
- RF seviyesi eşik üzerinde kaldığında kanalda beklenir; eşik altında kesintisiz süre dolunca geçilir.
- Bu 1 saniye, toplam tur garantisi değildir. Alıcı/çözücü açılış-kapanışı ayrıca zaman alır.
- Tek alıcı tararken başka frekanstaki kısa/eşzamanlı konuşmayı kaçırabilir.
- Sabit mod, tek I/Q bant penceresine sığan yakın kanalları birlikte işlemeye uygundur; tüm yük senaryoları sahada doğrulanmış değildir.

### TETRA'ya özel kontrol kanalı sınırı

- Güçlü RF olsa bile açık ses çözülmeden 120 saniye geçerse sonraki kanala gidilir.
- Hatasız sistem bilgisinin üç kez çözülmesi ve bildirilen ana taşıyıcının dinlenen frekansla eşleşmesi halinde, son iki saniyede ses yoksa daha erken geçilir.
- Sadece color code görmek kontrol kanalı kanıtı değildir.
- Sabit modda otomatik frekans atlama yoktur.
- Kontrol taşıyıcısında daha sonra ses başlayabilir; tarama başka yerdeyken kaçabilir.

### B. Spektrum bandını tarama

- Konuşma taramasından ayrı bir işlevdir. Kayıt oluşturmaz ve bu yolda protokol çözümü çalışmaz.
- USB artık bütün spektrum turu boyunca açık tutulur; senkron okuma ve frekans değişimi sonrası tampon temizleme kullanılır.
- Bant geçişinde Hızlı 60 ms / Dengeli 120 ms / Kararlı 250 ms bekleme seçilebilir.
- Değişmeyen dar tek bantta yeniden yerleşme beklenmez. Arayüz yaklaşık 200 ms'de yenilenir.
- Gerçek hız; bant sayısı, tuner, USB ve işleme yüküne bağlıdır. Yeni hızlı yol için gerçek cihaz denemesinde USB açılışı -3 döndü; **ölçülmüş hızlanma oranı yok**.

## 8. Spektrum / şelale: mevcut özellikler ve kritik ayrımlar

- Windows yönetici yetkisiyle açılan ölçüm sekmesi.
- Başlangıç/bitiş frekansı; bir taramada en fazla 24 MHz aralık.
- Hamming, Hann, Blackman ve dikdörtgen FFT pencereleri. Bunlar modülasyon türü değildir.
- Spektrum, şelale veya birlikte gösterim.
- Mevcut örnekleme 960 ksps, FFT 2048 nokta; bin aralığı yaklaşık 468,75 Hz.
- Geniş aralık parçalar halinde ölçülür. Şelalede üç piksel bir tam taramayı temsil eder, üst satır en yenidir. Henüz ölçülmeyen geçmiş koyu kalır.
- RF kazancı, Tuner AGC, PPM; değişiklik sonraki tam taramaya uygulanır.
- Üst seviye, görünüm aralığı, otomatik ölçek; 1/2/4/8 tarama ortalaması; tepe tut/sıfırla.
- Ayarlanabilir turuncu tepe eşiği; belirgin ve eşik üstündeki en güçlü altı tepenin MHz/dBFS etiketi.
- Fareyle seviye/frekans/eşik farkı; sol tıkla yakın tepeye kilit, sağ tıkla kilit kaldırma.
- 6,25/12,5/25/200 kHz işaretli bant: **yalnız görsel seçim**, donanım filtresi veya kanal gücü ölçümü değil.
- Durdurulduğunda kilit çevresinde 250 kHz ölçüm aralığı hazırlama.
- Solda eşik, üst seviye ve dikey aralık sürgüleri; sağda 1–20× yakınlık ve bant içi merkez sürgüleri.
- Yakınlık spektrum/şelale/marker eksenlerini birlikte değiştirir; yeni RF örneği veya daha yüksek FFT çözünürlüğü üretmez.
- `Tam bandı göster` görünümü sıfırlar. `Görünen bandı ölçüm aralığı yap` durdurulmuş ölçümün başlangıç/bitişini değiştirir; yeniden başlatma gerekir.
- Gain/aralık/FFT değişince eski tepe geçmişi temizlenir. Fare hareketi veya yeniden çizim sahte şelale satırı üretmez.

### Sinyal türü ve seviye

Bu görünümde otomatik DMR/TETRA/analog tanıması yoktur. Yakın tanımlı kanal varsa adı/modu gösterilir ve RF'den doğrulanmadığı yazılır; yoksa tür bilinmiyor denir. FFT şeklinden kesin protokol adı üretilmez.

Gösterim dBFS/FFT bin'dir. Kalibre dBm, anten giriş gücü veya kayıt squelch değeriyle doğrudan eşit değildir. AGC/gain/FFT penceresi/görünüm değişiklikleri ile gerçek sinyal değişimi kullanıcıya karıştırılmamalıdır.

## 9. SDR cihazları ve kazanç

Mevcut fiziksel alıcı: Terratec T Stick PLUS, E4000 tuner; USB ürünü Realtek RTL2838UHIDIR. Testte seri `00000001` görüldü.

- Manuel tuner kazancı ve Tuner AGC bulunur; +10 dB ve uygula düğmeleri vardır.
- Cihazın desteklediği en yakın kazanç adımı kullanılır; istenen değer ile gerçek uygulanan değer farklı olabilir.
- Gerçek cihazda 19 → 29 dB, Tuner AGC ve tekrar manuel 29 dB başarıyla denendi. Bu, ses kalitesinin mutlaka arttığının kanıtı değildir. Kullanıcı sonradan ayarları değiştirebilir; 29 dB sabit ürün zorunluluğu değildir.
- RTL AGC, tuner AGC ve ses AGC farklıdır. Mevcut Radia kontrolü **Tuner AGC**'dir; SDR#'taki bütün AGC seçenekleri eklenmiş değildir.
- USB cihaz adı, ürün/üretici, seri ve USB sıra kodu listelenir. Durum son listeleme anına aittir; canlı tak/çıkar gözetimi değildir.
- Benzersiz seriyle yeniden eşleme vardır. Aynı serili cihazlarda index/kod kontrol edilmelidir.
- Bir cihazın listede görünmesi, başka yazılım tarafından kullanılmadığını kanıtlamaz.
- Seçilen tek USB cihazı ana alım, FM RADIO veya spektrum için kullanılır. Bu işler mevcut sürümde birbirini kilitler; iki ayrı cihaz seçerek birlikte çalıştırma henüz yoktur.

**Gelecek hedef:** 2–3 bağımsız SDR, kullanıcı cihaz kodu/ismi, fiziksel USB bağlantı yolu, seri çakışması uyarısı, otomatik tak/çıkar durumu, cihaz başına kanal grubu ve ayrı alıcı işçileri.

## 10. Ethernet ve Hytera HR659

- Mevcut `rtl_tcp`, Ethernet üzerinden SDR I/Q kaynağıdır; Hytera röle ses protokolü değildir.
- Hytera hedef cihaz HR659 UHF. Kullanıcının “2.5” bilgisi firmware alanına ön dolduruldu; cihaz üzerinde henüz doğrulanmadı.
- Röle/PC IPv4 adresleri ve iki slotun kontrol/ses portları kaydedilir. Boş IP ile hazırlık yapılabilir.
- Örnek kontrol portları 30009/30010, ses portları 30012/30014; gerçek HR659 ayarlarıyla doğrulanmış değildir.
- Röle bağlı değildi. IP sürücüsü, oturum kurulumu, ses alma ve iki slot saha testi sonraki aşamadır.
- Yerel HytBridge incelemesinde IP Dispatch üzerinden G.711 μ-law ve çağrı metadata örneği bulundu. IPSC desteği yok. Kod erken aşamada; Python `audioop` uyumsuzluğu ve kayıt/çağrı ilişkilendirme eksikleri var.
- HytBridge'de gönderim/PTT de bulunuyor; örnekler kontrolsüz çalıştırılmamalı. İnceleme sırasında röleye gönderim yapılmadı. GPLv3 lisanslı bu kod mevcut uygulamaya kopyalanmadı.

## 11. FM RADIO

88,5–108 MHz, 100 kHz frekans adımı, WFM mono dinleme; kayıt üretmez. 100 kHz, filtre genişliği değildir. Paneli gizlemek sesi kapatmaz; Kapat düğmesi radyo alımını durdurur. Ana kayıt/spektrum ile aynı USB'yi paylaşamaz. Gerçek cihazda WFM/ses çıkış yolu sessiz çıkışla test edildi; kullanıcı tarafından kapsamlı yayın dinleme kabulü kaydedilmedi.

## 12. Test durumu ve açık sorunlar

**Son kod kontrolleri:** 71 test geçti; Ruff, biçim denetimi, ty, basedpyright ve paket derleme başarılı. Bu sayı her özelliğin RF sahasında doğrulandığı anlamına gelmez.

Özellikle açık kalanlar:

1. TETRA kesik ses/kısa kayıt: kullanıcı ses duyduğunu bildirdi. İncelenen kayıtlarda 0,06–1,92 saniyelik parçalar görüldü. Bir oturumda 234 ses çerçevesinin 4'ü hatalıydı. 0,8 saniyelik ses boşluğunda kayıt kapanması ve iki saniyelik açık çağrı metadata süresi katkıda bulunabilir; tek nedenin sinyal olduğu kanıtlanmadı. Henüz çözülmüş sayılmamalı.
2. TETRA güvenilir SSI/GSSI/çağrı ilişkilendirmesi ve çoklu gerçek slot kabulü.
3. DMR'de uzun konuşma sırasında arşiv dosyasını canlı teslim etme.
4. XPT/Capacity Plus otomatik frekans/slot takibi ve gerçek test verisi.
5. Hytera HR659 IP Dispatch sürücüsü ve bağlı röle testi.
6. 2–3 cihazın bağımsız eşzamanlı yönetimi.
7. Yeni hızlı spektrum yolunun canlı hız/kararlılık ve bant geçiş doğrulaması.
8. Analog ton filtrelerinin ve APCO25/NXDN modlarının saha testleri.
9. Tasarımda ekran boyutu/Windows ölçeklendirme, klavye erişimi, tablo okunabilirliği ve hata durumları için daha kapsamlı kabul testi.

## 13. Teknik çalışma alanı ve dosyalar

```text
Kanonik proje:       D:\Projects\Biem\_SDR
Korunacak SDR#:      D:\Depo\SDR\sdr-install\sdrsharp
Yerel SDR kaynakları:D:\Depo\SDR
HytBridge:          D:\Projects\HytBridge-master
GitHub:             https://github.com/mcelik3737/Biem_SDR.git
Yerel dal:          codex/dmr-receiver
Normal açılış:      Start-Radia.cmd
Yönetici açılışı:   Start-Radia-Admin.cmd
Kontroller:         Check-Radia.ps1
```

Uygulama Python/Tkinter/ttk masaüstü yazılımıdır. DSP'de NumPy/SciPy, arşivde SQLite ve korumalı WAV içeriği, harita görsellerinde Pillow kullanılır. DMR/APCO25/NXDN için ayrı DSD-FME süreci; TETRA için yerel DLL'lere bağlı ayrı x86 yardımcı süreç kullanılır.

Spektrum yönetici erişimi Windows yükseltilmiş süreç yetkisidir; henüz uygulama içi kullanıcı/parola/rol sistemi değildir. Yönetici açılışı Windows UAC onayı gerektirir.

Çalışma verileri `data` altında; ayarlar arasında `receiver.json`, `channels.json`, `device.json`, `hytera.json` bulunur. Kayıtlar, çalışma ayarları, üçüncü taraf binary ve check-out'lar Git'e eklenmez.

**Git durumu uyarısı:** Bu belge hazırlanırken son özelliklerin önemli bölümü yerelde değiştirilmiş/yeni dosyalar halindeydi, commit edilmemişti. GitHub'ın çalışan son yerel sürümle eşleştiği varsayılmamalı. Bu belgeyi kaydetmek bir Git commit/push veya tam proje yedeği değildir.

## 14. BİEM markası

Şirket: **BİEM Teknoloji Elektronik**  
Web: https://biemelektronik.com/  
GSM: +90 532 524 40 37  
Ofis: +90 216 807 24 36–37  
E-posta: proje@biemelektronik.com  
Adres: Barbaros Mah. Begonya Sok. Batı Nida Kule No:1, Ataşehir / İstanbul.

Bu iletişim bilgileri önceki proje brifinden aktarılmıştır; bu doküman turunda yeniden web doğrulaması yapılmadı. Müşteri yayını öncesi resmî kaynakla kontrol edilmelidir.

Orijinal logolar:

```text
D:\BIEM\BIEM_FILES\yeni_logo\biem-logo.png
D:\BIEM\BIEM_FILES\yeni_logo\jjj.png
```

Uygulama içi kopyalar `src/biem_radia/assets` altındadır. Büyük yatay logo üst başlıkta, amblem pencere simgesinde kullanılır. Marka logosu değiştirilmemeli veya yeniden üretilmemelidir. Tasarımda koyu lacivert/kırmızı marka renkleri vurgu olarak kullanılabilir; ana çalışma alanı açık ve sakin kalmalıdır.

## 15. Kayıt güvenliği ve yetkiler — güncel durum

Kullanıcının talebi: yönetici olmadan kayıtlar dinlenmesin; kayıtlar mümkün olduğunca yalnız Radia içinde dinlensin. İkinci madde mutlak garanti olarak sağlanmış değildir.

- Uygulama arşiv oynatımında Windows yönetici yetkisini kontrol eder. Normal süreç arşiv sesini açamaz. Bu, uygulama içinde kullanıcı/parola/rol yönetimi olduğu anlamına gelmez.
- Tamamlanan kayıtlar Windows kullanıcısına bağlı DPAPI ile korunur; uzantı `.wav.radia` olur. Standart medya oynatıcısı bu dosyayı WAV olarak açamaz.
- Ses RAM içinde çözülüp oynatılır. DMR dinleme kazancı +6 dB ve yumuşak sınırlama uygulanır; eski geçici dinleme WAV kopyası artık oluşturulmaz.
- Geçişte 102 eski WAV şifrelendi ve geri çözülerek hash karşılaştırmaları doğrulandı. Bu, o andaki geçiş sonucudur; ileride bütün geçici dosyaların şifreli olacağı garantisi değildir.
- Aktif analog `.wav.part`, üçüncü taraf çözücünün açık WAV'ı veya çökme kalıntıları düz ses içerebilir. Hata durumunda kurtarılabilir kaynak silinmez.
- DPAPI süreç adına bağlı değildir. Aynı Windows kullanıcı bağlamındaki başka yazılıma veya yerel sistem yöneticisine karşı “yalnız bu program açabilir” güvencesi verilmez.
- Normal ve yükseltilmiş uygulama aynı Windows hesabıyla kullanılmalıdır. Başka hesapla yükseltme ve profil/anahtar kaybı çözmeyi engelleyebilir. Dosyayı başka PC'ye kopyalamak taşınabilir bir dışa aktarma değildir.
- Ayrı anahtar hizmeti, uygulama içi roller, şifreli geçici depolama, doğrulanmış anahtar yedekleme ve güvenlik denetim izi sonraki çalışmalardır.
- Dijital veri günlükleri ve son konum JSON'u düz metindir; ses korumasıyla korunmuş kabul edilmemelidir.

**Tasarım gereği:** normal kullanıcıda dinleme kontrolünün kilit nedeni anlaşılır olmalı. Arşiv listesi görünürlüğü ile sesi dinleme yetkisi ayrı davranışlardır. Tasarımda bütün sayfayı erişilemez varsaymayın. Yönetici durumu renk yanında metinle gösterilsin. Otomatik Windows yükseltme veya UAC onayı taklit edilmesin. “Korumalı kayıt” ifadesi kullanılabilir; “kırılamaz / yalnız Radia açar” kullanılmamalı.

## 16. Dijital veri günlüğü ve gerçek konum testi

Yeni **Dijital Veri Günlüğü** sekmesi, yalnız ses değil çözücünün sunduğu veri satırlarını da incelemek içindir. DMR'de ham payload, çağrı başlıkları, olası GPS/LRRP/SDS satırları; TETRA'da köprünün açığa çıkardığı ham alanlar bulunur.

| Kaynak | İçerik ve sınır |
|---|---|
| DMR `decoder.log` | Ham çözücü çıktısı; payload ayrıntısı açık |
| DMR `digital.jsonl` | PC gözlem zamanı UTC, kanal, frekans, protokol, kategori, özgün satır |
| DMR `events.log` | Çağrı olayları |
| DMR `lrrp.tsv` | Çözücü uygun çıktı üretirse oluşan dosya; varlığı tek başına doğruluk garantisi değil |
| TETRA `events.jsonl` | Zaman, kanal/frekans, senkron, slot, hatalar ve mevcut ham alanlar; PCM metne yazılmaz |
| `locations/latest.json` | Son kabul edilen konumun kalıcı önbelleği |

Ekran son oturumlardan en fazla 1000 satır gösterir. Mevcut metin filtresi bundan sonra gelen satırlara uygulanır; dosya geçmişini silmez. Yeni tasarımda geçmişe dönük arama önerilebilir fakat uygulanmış sayılmamalıdır. GPS/SDS kategorisi anahtar kelime eşleşmesidir; geçerli koordinat veya tam protokol çözümü anlamına gelmez. Ham konsol çıktısı tam RF I/Q kaydı değildir; bütün havadaki bitlerin saklandığı iddia edilmemeli.

### Testte gerçekten görülenler

- 427.500 MHz DMR testinde kaynak ID **3737** ve özel çağrı hedefi çözüldü. Başlangıçtaki kullanıcı ayarı CC 11 idi; sonraki konum mesajlarında alınan CC **1** oldu. Eski ayar güncel alınan değer diye gösterilmemeli.
- Türkçe UTF-16LE kısa veri metninde enlem/boylam, mesaj saati/tarihi, hız, yükseklik ve uydu sayısı alanları görüldü. Son konum testi özel hedef **5** içindi; hedef 5 grup 5 olarak etiketlenmemeli.
- Çözücü slotu 1 görüldü. Simplex durumda bu bilgi bağımsız fiziksel TDMA slot doğrulaması değildir.
- Birden fazla mesajdan güncelleme alındı; son geçerli mesajın otomatik okunması ve haritada gösterilmesi doğrulandı. Bu nedenle eski belgelerdeki “GPS testi bekleniyor” ifadesi bu test için artık güncel değildir.
- Yanlış LOCN yorumunda çıkan `Source 153 / 0,0` kabul edilmedi. Kimlik veri başlığından, koordinat UTF-16LE metninden alındı.
- Tam konum ve oturum dosyaları bu tasarım teslimine konmadı. Tasarım örneklerinde açıkça temsili kimlik/konum kullanın.

Mevcut harita ayrıştırıcısı test edilmiş Türkçe DMR UTF-16LE konum metnini destekler. Eksik başlık, uygunsuz koordinat ve hata satırlarında yeni nokta kabul edilmez. Genel LRRP/NMEA, TETRA SDS konum desteği veya bağımsız GPS doğruluğu/CRC doğrulaması iddia edilmez. Hız/yükseklik/uydu sayısı ham metinde görülmüş olması, bunların ayrı doğrulanmış gösterge olarak uygulandığı anlamına gelmez.

## 17. Harita — son uygulanan özellikler

**Kapsam kararı:** bu harita sunum/demo içindir. Son müşteri harita ürünü değildir. İleride çevrimiçi harita değerlendirilebilir; sağlayıcı ve mimari henüz seçilmedi. Şimdiki uygulama çevrimdışıdır; online servis ya da API anahtarı etkin değildir.

- Harita sekmesi son geçerli telsiz konumunu gösterir; uygulama açılışında önbellekten geri yükler. Eksik/bozuk veri son noktayı silmez.
- ID, enlem/boylam, alınma yaşı, mesaj saati, CC, çözücü slotu, hedef ve kanal bilgisi vardır. Mesaj saati ile PC'nin gözlem zamanı ayrıdır.
- Sürekli canlı GPS takibi, güzergâh geçmişi, çoklu telsiz filosu, geofence, rota veya adres araması henüz yoktur. Eski konum “şu anda burada” diye sunulmamalı.
- Standart çevrimdışı haritada Türkiye ve çevresi, 81 il sınırı, 83 yerleşim noktası, göller; il/şehir/ızgara açma-kapama bulunur. Natural Earth verisi sokak haritası değildir.
- Türkiye görünümü, son telsize yaklaş, paket alanına yaklaş, +/−, tekerlekle yakınlaştırma ve sürükleyerek kaydırma vardır. Kuzey oku ve yaklaşık yerel mesafe ölçeği gösterilir.
- Eski `googlemaps.zip`: z1–4, 10 JPEG. Konum bilgisi dosyanın `z/x/y` yolundadır; EXIF gerektirmez.
- Yeni `turkey_9_katman.zip`: adına rağmen z1–11, **3396 PNG**. Bu paket etiketli yol haritasıdır; her katmana “uydu” denmemeli. Üst ayrıntı düzeyleri yalnız belli bölgeleri kapsar; Konya çevresinde ayrıntı vardır, bütün Türkiye için aynı ayrıntı garantisi yoktur.
- Eksik yüksek çözünürlükte alt seviye kullanılır. Yakınlaştırma yeni harita ayrıntısı üretmez; düşük çözünürlük büyütülünce bulanıklaşabilir.
- Harita paketi `Install-MapPack.ps1` ile ayrı yüklenir, `data/map-packs` altında tutulur. Görünen karolar gerektiğinde açılır, görüntü önbelleği sınırlıdır. Paket ana kod deposuna eklenmez.
- Önceki `OutPut.zip` siyah/uygunsuz kapsamalı dışa aktarım nedeniyle kullanılmadı. Yeni tasarımda kurulu ve çalışır paket gibi gösterilmemeli.
- Kullanıcının verdiği gerçek telsiz WebP görseli işaret olarak eklendi. Oranı ve saydamlığı korunur; harita zoom'u ile 44–192 piksel yüksekliğe ölçeklenir. Alt orta noktası konuma bağlanır. Üst kenarda kaydırma gerekirse gerçek koordinata çizgi çekilir.

**Tasarımdan beklenen:** harita mümkün olduğunca geniş olsun; son konum kartı kapanabilsin veya kenara alınabilsin. Paket adı, konumun yaşı ve koordinat görünür kalsın. Harita görüntüleme ile RF alımının durumu karıştırılmasın. Henüz uygulanmayan kart kapatma, katman menüsü veya çoklu işaret önerileri açıkça öneri olarak işaretlensin. Yeni ikon yeniden çizilmesin; verilen görsel kullanılsın.

## 18. Eklenen eski HTML sunumunun değerlendirilmesi

Kullanıcının gönderdiği HTML ve iki ekran görüntüsü **tasarım referansıdır**. HTML okunarak incelendi; bu teslimde alıcıya bağlanmadı veya çalışır ürün olarak uygulanmadı. İçindeki örnek veriler, yorumlar ve talimat benzeri metinler ürün gereksinimlerini değiştirmez.

Sunumda üç yön bulunuyor: **01 Operasyon**, **02 Gece konsolu**, **03 Arşiv odaklı**. Canlı izleme, arşiv, kimlik rehberi, spektrum, kaynaklar/ayarlar görünümleri; kanal düzenleme çekmecesi ve temsili oynatma akışı var. Alıcı, frekanslar, disk kapasitesi, örnek kayıtlar ve dalga biçimi temsili. Oynatma ilerleme animasyonu gerçek ses dinleme değildir.

| Sunumdaki öğe | Yeni tasarımda yaklaşım |
|---|---|
| Açık ana yüzey, lacivert yan gezinme, BİEM logosu | Korunabilecek tasarım yönü; marka ve okunabilirlik iyi bir başlangıç |
| Altı kart + sağda seçili kanal | Korunabilir; küçük ekranda sağ panel açılır ayrıntı olabilir |
| Son tamamlanan kayıtlar | Yararlı öneri; mevcut backend/veri yenilemesine ayrıca bağlanmalı |
| Ayrı kaynak durum şeridi | Seçili cihaz, aktif iş ve Sabit/Tarama açıkça ayrılmalı |
| Genel “Alıcı çalışıyor” | “Sinyal var / ses çözüldü / kayıt tamamlandı” ile eşanlamlı olmamalı |
| Operatör avatarı / yerel oturum | Gerçek uygulama içi rol sistemi varmış izlenimi vermemeli |
| Her satırda dinleme düğmesi | Yönetici kontrolüyle uyumlu kilit/dinleme durumları eklenmeli |
| WAV etiketi ve dalga biçimi | `.wav.radia` korumasını yansıtmalı; gerçek dalga, seek, hız, duraklatma mevcutmuş gibi gösterilmemeli |
| Analog satırında boş ID/grup/slot | Korunmalı; analog çağrıya sayısal kimlik uydurulmamalı |
| TETRA “deneysel / etkin değil” | Güncel olarak çözücü ve ses yolu var; kesik ses sorunu açık. Tümüyle yok saymak da tam çalışıyor demek de yanlış |
| Sabit modda eşzamanlı izleme | Yalnız tek alıcının I/Q bandına sığan kanallar ve desteklenen işleme için; uzaktaki bantlar birlikte alınmış gibi gösterilmemeli |
| 186 GB / 500 GB kapasite | Sunum örneği. Üründe gerçek disk ölçümüyle bağlanmadan sabit sayı gösterilmemeli |
| Harita ve dijital günlük | Eski navigasyonda eksik; yeni öneriye eklenmeli |
| FM RADIO, Hytera, cihaz envanteri | Yeni gezinmede kaybolmamalı; teknik ayarlar altında düzenlenebilir |

Eski HTML'nin mobil benzeri daralma kuralları, küçük puntoları ve tablo/oynatıcı alanı ayrıca gözden geçirilmeli. Masaüstü kullanımında bütün etiketleri küçülterek sığdırmak yerine kart sütunu azaltma ve ayrıntı panelini katlama tercih edilebilir. Üç temayı tamamlanmış ürün şartı saymayın; önce açık Operasyon görünümünü olgunlaştırın.

## 19. Yeni arayüz için bilgi mimarisi öneri çerçevesi

Bu bölüm uygulanmış ekran düzeni değildir; tasarımcıdan beklenen kapsamı tanımlar.

| Bölüm | Günlük iş | Teknik ayrıntı |
|---|---|---|
| Canlı izleme | Altı kanal, aktif çağrı, kayıt durumu, seçili kanal | Kanal düzenleme, mod, frekans, ton/CC ve eşik |
| Kayıt arşivi | Tarih/metin arama, sonuç seçme, yetkili dinleme | Kimlik/slot kaynağı, koruma/hata, kaynak bilgisi |
| Harita | Son geçerli telsiz konumu ve yaşı | Paket/katman, koordinat ve veri kaynağı |
| Kimlik rehberi | ID ve ad eşleştirme | Sistem/müşteri kapsamı, cihaz ve grup türü |
| Dijital veri günlüğü | Gelen veri/konum mesajı inceleme | Ham satır, protokol, gözlem zamanı, oturum |
| Spektrum | Yönetici ölçümü | FFT, RF gain/AGC, PPM, eşikler, bant ve hız |
| Kaynaklar ve ayarlar | Kaynak seçimi ve bağlantı | SDR envanteri, rtl_tcp, Hytera hazırlığı |
| BİEM / Hakkında | Marka ve sürüm bilgisi | Destek bilgileri |

FM RADIO üstte yardımcı açılır alan olarak kalabilir. Harita/günlük sekme değişimi alımı gizlice başlatmamalı veya durdurmamalı. Tek USB için ana alım, FM RADIO ve spektrum arasında sahiplik açık olmalı. Yeni çalışmaya geçişte kullanıcıya hangi işin duracağı gösterilmeli; her zararsız tıklamaya onay penceresi eklenmemeli.

### Kanal kartında veri hiyerarşisi

Birinci düzey: kanal adı, seçili mod, durum. İkinci: frekans, sinyal seviyesi/birimi ve kayıt süresi. Üçüncü: gelen kaynak ID/isim, grup veya özel hedef, CC ve slotun türü. Sürekli düzenleme alanları yerine ayrı ayarlar yüzeyi önerilebilir. Alım sırasında kanal düzenleme kilidi korunmalı; desteklenen RF kazanç değişimi ayrı ele alınmalı.

Analog seçildiğinde erişim türü aktif olur: CSQ ton istemez; CTCSS standart Hz listesi; DCS ve ters DCS kod seçimi. Dijital seçildiğinde analog tonlar pasif. DMR'de CC alanı boş/tümü otomatik keşfe izin verir, ancak frekansı yazmak metadata üretmez; geçerli yayın gelmesi gerekir. “CC filtresi: tümü” ile “Alınan CC: 1” aynı alana yazılmamalı.

### Durum dili

| Durum | Kullanıcıya söylenecek | Söylenmemesi gereken |
|---|---|---|
| Alım kapalı | Alıcı durduruldu | Sinyal yok |
| Tarama sırasında sıra bekliyor | Sırada / şu an ölçülmüyor | Eski seviye yeni ölçümmüş gibi |
| RF eşik altında | Bekliyor | Cihaz bağlı değil |
| RF var, ses çözülmüyor | Sinyal var; ses henüz çözülemedi | Konuşma kaydediliyor |
| Ses kaydı açık | Kaydediliyor | Kaydedildi |
| Maksimum süre arası | 2 saniyelik kayıt arası | Bağlantı koptu |
| DSD dosyası bekleniyor | Çağrı tamamlanınca arşive aktarılacak | Dosya hemen arşivde |
| Korumalı dosya tamamlandı | Kayıt tamamlandı | Her düz/geçici dosya şifrelendi |
| Dinleme yetkisi yok | Dinlemek için yönetici yetkisi gerekli | Kayıt bozuk |
| Anahtar/okuma hatası | Kayıt açılamadı; nedeni göster | Kayıt yok |
| Eski harita konumu | Son alınan konum ve yaşı | Canlı konum doğrulandı |

Bunlar hedef durum sözlüğüdür. Backend'in ayrı olay olarak sunmadığı durumlar için gereken veri/olay eklemesini ayrıca listeleyin. Renklere mutlaka metin veya ikon eşlik etsin.

## 20. Kritik etkileşim senaryoları

1. **Analog ayarı:** operatör kanalı seçer, NFM seçer; CSQ/ton alanları uygun hale gelir. Alım başlayınca yapılandırma kilidi görünür. Bekleme ile kayıt ayrı gösterilir.
2. **DMR otomatik bilgi:** frekans girilir, CC tümü seçilir. Yayın gelene kadar ID/CC/hedef bilinmiyor kalır. Çağrı başlığı gelince kaynak ve özel/grup türüyle hedef görünür. Son çağrı kimliği yeni bilinmeyen çağrıya aktarılmaz.
3. **Tarama:** hangi kanalın ölçüldüğü belli olur. Diğer kartların son ölçüm verisi güncel veri gibi sunulmaz. Eşik aşılınca bekleme, eşik altına düşünce devam etme anlaşılır.
4. **Arşiv dinleme:** kayıt seçilir; normal süreçte kilit nedeni görünür. Yönetici süreçte korumalı dosya RAM'de açılır. Sesi kesmek alıcıyı veya kayıt işlemini durdurmaz.
5. **Konum:** geçerli veri geldiğinde son nokta güncellenir. Bozuk mesajda eski nokta korunur ve yaşı artar. Harita yok/eksik paket durumunda koordinat bilgisi kaybolmaz.
6. **Spektrum:** yönetici yetkisi ve cihaz sahipliği kontrol edilir. Gain, squelch, FFT eşiği ve görünüm ölçeği ayrı alanlardadır. Sadece grafiği yakınlaştırmak RF çözünürlüğünü artırmaz.
7. **Kapanış:** alıcı normal durdurulur ve devam eden dosyalar tamamlanır. Ekranı kapatma, dosya işlemlerini habersiz kesen zorla süreç sonlandırmaya dönüşmez.

## 21. Tasarım teslimi ve kabul ölçütleri

ChatGPT'den yalnız güzel ekran değil, geliştiricinin uygulayabileceği açıklamalı tasarım isteniyor:

- Önce mevcut HTML'de korunacak/değişecek yerlerin kısa değerlendirmesi.
- Güncellenmiş navigasyon, ana ekran, arşiv, harita, günlük, yönetici spektrumu ve kaynak ayarlarının wireframe/HTML önizlemesi.
- 1280×920, 1920×1080 ve mümkünse 1366×768; Windows %100/%125/%150 ölçekleme davranışı. Alt düğmeler ve oynatıcı ekran dışında erişilemez kalmamalı.
- Renk, yazı boyutu, minimum kontrol boyu, boşluk, kart/table ölçüleri ve odak/klavye davranışı. Frekans ve sürelerde hizalı rakamlar; Türkçe karakterler sorunsuz.
- Arşivde boş sonuç, yetkisiz oynatma, dosya hatası; cihazda yok/meşgul; haritada mesaj yok/eski mesaj/eksik karo durumları.
- Mockup verileri açıkça temsili işaretlensin. Tasarım için müşteri ses kaydı veya gerçek konum paylaşılması gerekmez.
- Değişiklikleri üç gruba ayır: yalnız arayüz; ek backend/veri olayı gerekiyor; sonraki ürün aşaması.
- Python/Tkinter/ttk uygulama gerçeğini dikkate al. HTML tasarımı otomatik olarak web uygulamasına geçiş kararı değildir. Qt/WebView gibi teknoloji değişimleri ayrıca değerlendirilir.
- Waveform, ileri sarma, oynatma hızı, çoklu telsiz haritası, tarih aralığı, çoklu SDR işçileri ve uygulama içi roller öneri olabilir; bugün çalışırmış gibi yazılmamalı.
- Görsel değişiklikler DSP, protokol kimlik eşleştirmesi, 90/2 kayıt kuralı veya koruma davranışını değiştirmemeli.

### ChatGPT'ye doğrudan gönderilecek metin

> Ekli Markdown, BİEM Radia Windows masaüstü yazılımının güncel ve birleştirilmiş durum/kurallar belgesidir. Eski HTML ve iki ekran görüntüsünü tasarım referansı olarak kullan. Açık renkli “Operasyon” yaklaşımını geliştir; altı kanal, yetkili arşiv dinleme, harita ve dijital veri günlüğünü birlikte kapsayan sade bir tasarım hazırla. Harita sunum/demo içindir; final müşteri ürünü değildir. Yeni telsiz görselini kullan ve zoom ile ölçeklenmesini koru. Mevcut özellikleri, test edilmiş olanları ve önerileri karıştırma. Özellikle DPAPI sınırları, yönetici dinleme kontrolü, fiziksel/çözücü slot ayrımı, özel hedef/grup ayrımı ve dBFS/dBm ayrımı değişmesin. Önce eski tasarımın güncel sürümle farklarını çıkar; sonra ekran düzeni, durumlar, ölçüler, renkler ve etkileşimleri ver. Mümkünse tek HTML tasarım önizlemesi hazırla; bütün örnek verileri temsili olarak işaretle, gerçek alıcıya veya online haritaya bağlanma. Yalnız UI ile yapılabilecekleri, backend gerektirenleri ve sonraki aşamayı ayrı listele. Projenin mevcut teknolojisi Python/Tkinter/ttk; teknoloji göçünü kendiliğinden varsayma.

## 22. Bu belgenin doğrulama ve paylaşım kapsamı

12 Eylül 2026 son ikon değişikliğinde 71 donanımsız test geçti; Ruff, biçim, ty, basedpyright ve 0.2.0 paket derlemesi başarılı. İlk tam çalıştırmada Tk başlatma hatası görüldü; tekrar tam çalıştırma geçti. Bu, bilinen aralıklı Windows/Tk test ortamı sorununu tamamen çözmüş olduğumuz anlamına gelmez. İkon ölçekleme ve koordinat sabitliği test edildi; kullanıcının son görsel değerlendirmesi bekleniyor.

Bu teslimde yalnız doküman ve kullanıcı tasarım referansları hazırlandı; alıcı çalıştırılmadı, ayarlar değiştirilmedi, radyo yayını yapılmadı, ses veya konum günlükleri paylaşım paketine konmadı. Kod testleri doküman düzenlemesi için tekrar çalıştırılmadı. Dosya/link/paket içeriği denetlendi.

Yerel geliştirmelerin önemli bölümü henüz Git commit/push yapılmamış durumdadır. GitHub'ın en güncel çalışan sürüm olduğunu varsaymayın. ChatGPT'ye gönderim kullanıcı tarafından yapılacaktır; bu teslim otomatik yükleme değildir.


## Roadmap devam paketi — 12 Eylül 2026

Kullanıcının verdiği yolun mevcut karşılığı `D:\Desktop_Yedek\MAPS\Yeni klasör (2)\konya\googlemaps\roadmap` bulundu. Önceki turkey_9_katman verisiyle birleştirilerek **Türkiye yol haritası - genişletilmiş** seçeneği kuruldu. Önceki paket ve kaynak dosyalar korundu.

- 374,831 koordinatlı karo, z1–17; 167,716 benzersiz görüntü. Aynı görüntü farklı koordinatlarda tek içerik dosyasına bağlanır. Düz renkli karolar geçerli zemin olabileceğinden otomatik silinmedi.
- Aynı XYZ'de 0 farklı dosya saptandı; bunlarda önceki paketin görüntüsü korundu. 3396 aynı koordinat/içerik tekrarlandı. Reddedilen dosya: 0. Ayrıntılı import raporu kurulu pakette.
- Yerel `tile-index.json`, sayısal koordinatları `tiles/content/<sha256>.png` içeriğine eşler. Bu klasör kurulumu mevcut basit ZIP yükleyicisinin yeni bir dağıtım formatı desteği değildir; bu aşama sunum için yerel birleştirmedir.
- Görüntü boyutu, PNG bütünlüğü ve çözülebilirlik kontrol edildi. Her seviyeden örnek okundu. Yerel indeks yükleme ölçümü 2.77 sn; yakın görünüm sorgusu 0.16 ms, 71 görünür karo. Bu sorgu süresi çizim/FPS ölçümü değildir.
- Yakınlaştırma üst sınırı 64× yerine 8192×; görünür koordinatlar doğrudan aranır. Görüntü önbelleği 128 içerikle sınırlı kalır. Telsiz koordinatı ve ikonun 44–192 piksel sınırı değişmez.
- 73 donanımsız test, kalite kontrolleri ve 0.2.0 paket derlemesi geçti. Canlı kullanıcı ekranındaki akıcılık ve yeni kapsama görsel kabulü bekleniyor. Harita internet kullanmaz; RF alımında değişiklik yapılmadı.

Yeni paketi görmek için Radia yeniden açılır; Harita listesinden **Türkiye yol haritası - genişletilmiş (paket)** seçilir. **Paket alanı** yüksek ayrıntı bölgesine götürür; **+** veya tekerlekle yaklaşılır. Son telsiz konumu bu bölgeye taşınmaz. Yeni z17 kapsaması bütün Türkiye için sokak ayrıntısı anlamına gelmez.
