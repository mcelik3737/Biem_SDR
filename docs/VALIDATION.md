# Doğrulama — 12 Eylül 2026

## Gerçek ortam

- Proje: `D:\Projects\Biem\_SDR`; önceki Codex çalışma klasörü boş bir Git deposuydu.
- İstenen `BIEM_Radia_Codex_Proje_Talimati.md` dosyası belirtilen konumlarda bulunamadı. Bu uygulama kullanıcının mesajlarındaki analog FM önceliğine göre hazırlandı; bulunmayan dosyanın okunmuş olduğu iddia edilmez.
- Mevcut SDR# kurulumu okunarak incelendi; dosyaları ve sürücüsü değiştirilmedi.
- USB PnP: `VID_0CCD&PID_00D7`, iki Bulk-In arayüzü, Windows durumu OK.
- librtlsdr: `Terratec T Stick PLUS`, `Elonics E4000` tuner.
- Gerçek örnek akışı: 960 kS/s; merkez 446,10625 MHz; çözülen kanal 446,00625 MHz.
- USB açma, örnek okuma, asenkron alım iptali ve tekrar açma gerçek cihazla doğrulandı.
- Otomatik kazançla başlangıç gürültüsü −60 dBFS'den yaklaşık −46 dBFS'ye yükselerek sürekli kayıt açtı. Sabit 19 dB kazançla boş kanal yaklaşık −59 dBFS'de kaldı; −48 dBFS eşikte kayıt bekleme durumuna geçti.
- İlk kazanç denemesinin 180,012 ve 48,077 saniyelik WAV dosyaları arşive yazıldı. Bunlar doğrulanmış konuşma kayıtları değildir; test RF/gürültü kayıtları olarak korunuyor.
- Windows arayüzü açıldı; canlı seviye, durdurma, arşivde iki WAV satırı ve yeni kazanç kontrolü görsel olarak doğrulandı.

## Otomatik kontroller

17 test: bilinen FM tonunun çözülmesi, düzensiz bloklarda filtre sürekliliği, iki eşzamanlı kanalın ayrılması, bant dışı taşıyıcının bastırılması, iki ayrı konuşma parçası, ön/son tampon, WAV başlığı ve PCM verisi, gün/kanal araması, açık kaydın hata veya durdurmada tamamlanması, maksimum süre bölünmesi, parçalı rtl_tcp başlığı/komutları, ağ kopması, hatalı kanal/bant sınırları, arşiv yol güvenliği, gerçek uygulama motorundan arşive sentetik I/Q akışı, USB kuyruk taşması bildirimi, masaüstü kanal düzenleme ve kayıt seçme/dinleme dosya yolu.

Ruff, biçim kontrolü, ty ve basedpyright geçiyor. Wheel ve kaynak paketi oluşturuldu. Test kapsamı raporunda toplam yaklaşık %71; gerçek DLL ve kullanıcı etkileşimlerinin tüm hata dalları otomatik kapsamda değildir. Sayısal test kapsamı saha kabulü yerine kullanılmaz.

## Henüz doğrulanmayan veya uygulanmayan işler

- Analog ses kullanıcı tarafından doğrulandı. DMR güncel doğrulama durumu aşağıdadır.
- Aynı cihazla çok kanallı gerçek yayın performansı ve 24 saat kesintisiz çalışma.
- Ethernet üzerinde gerçek rtl_tcp sunucusu: adaptör mevcut, yerel protokol testi geçti; gerçek ağ cihazı testi bekliyor.
- DMR eşzamanlı iki gerçek RF slotu kabul testi bekliyor; simplex ses ve metadata doğrulandı.
- Hytera repeater entegrasyonu uygulanmadı; rtl_tcp bu entegrasyon değildir.
- Crash recovery, disk kotası, saklama süresi, kullanıcı yetkileri ve kurumsal yedekleme sonraki aşama.

## Sonraki kabul ölçütü

DMR röle üzerinden iki eşzamanlı slotun ayrı dosyalara ve doğru kimliklere bağlanması, ardından çok kanallı uzun süre testi.

## DMR güncellemesi — 2026-09-12

27 donanımdan bağımsız test, Ruff, ty ve basedpyright geçti; wheel ve kaynak paketi üretildi. Kullanıcı gerçek RF'den çözülen DMR konuşmasını anlaşılır duyduğunu doğruladı. Alıcının frekans sapması kalıcı PPM ayarıyla düzeltildikten sonra doğrudan canlı alımdan iki konuşma WAV'ı arşive yazıldı. Kaynak/hedef ID, color code ve sistem bazında isim eşlemesi gerçek çözücü olaylarıyla eşleşti. Simplex olaylarında fiziksel slot verilmediği için boş bırakıldı. Sınırlar ve zaman damgası yaklaşımı için `DMR.md` dosyasına bakın.


## 0.2.0 çok modlu ekran ve kayıt adları

42 donanımdan bağımsız test geçti: beş frekans sırası, altı kutuda düzenleme/ton kaydı, FM RADIO ile ana alıcı çakışmasını engelleme, CTCSS doğru/yanlış ton, DCS normal/ters polarite, WFM ses frekansı, dosya adı çakışması, dosya taşıma/arşiv tutarlılığı ve TETRA slot başına açık çağrı kapısı dahil. TETRA yardımcı süreç gerçek yerel DLL'lerle 96 kHz I/Q sıfır girişinde çalıştırılıp temiz kapatıldı; gerçek RF ses testi değildir. APCO25 Phase 1 ve NXDN96 kamuya açık discriminator örnekleri gerçek DSD-FME ikilisi üzerinden ses dosyası ve metadata üretti, ayrı test arşivine alındı. USB → WFM → PortAudio yolu 99,5 MHz'te ses çıkışı sıfıra ayarlanarak açılıp kapatıldı; yayın anlaşılırlığı henüz kullanıcı tarafından doğrulanmadı.

Mevcut 27 arşiv dosyası okunabilir adlara dönüştürüldü; her dosyanın önceki/sonraki SHA256 değeri aynı ve veritabanı yolları erişilebilir. Önce SQLite yedeği ve yol manifesti oluşturuldu. TETRA/NXDN48/CTCSS/DCS için RF saha kabulü, beş kullanıcının belirleyeceği frekansla gerçek tarama ve uzun süreli performans testleri bekliyor. Ayrıntılı mod sınırlamaları `CHANNELS_AND_MODES.md` dosyasında.


## 2026-09-12 kayıt koruması / dijital veri
63 test ve tüm kalite kontrolleri geçti; paket derlendi. 102 mevcut WAV şifrelendi ve hash ile doğrulandı. GPS RF kabulü bekleniyor. Ayrıntı: SECURITY_AND_DIGITAL_DATA.md.


## 2026-09-12 Harita
67 test, Ruff, ty, basedpyright ve wheel/sdist derleme başarılı. Gerçek kayıtlı DMR UTF-16LE mesajından son konum otomatik çıkarıldı; masaüstünde Harita sekmesi ve ID 3737 telsiz simgesi gözlemlendi. Yeni RF gönderimi bu turda yapılmadı.


## Harita ayrıntıları
67 test ve tüm kalite kontrolleri / paket derleme geçti. Harita testi 81 il, şehir, göl ve ölçek çizimini; şehir katmanı kapanırken telsizin kalmasını da doğrular. İlk test çalışmasında Tk auto.tcl açılışı geçici hata verdi; dosyanın mevcut olduğu doğrulandı ve tam kontrolün tekrarında tüm testler geçti.


## Yerel XYZ uydu katmanı
10 JPEG üzerinde boyut ve EXIF incelemesi yapıldı: tümü 256×256, EXIF alanı yok. z/x/y yolu ile konumlandırıldı. 69 test; XYZ sınırları / Mercator ters dönüşümü, yerel JPEG çizimi, katman değişiminde marker koordinatının sabit kalması dahil kontroller başarılı. Google uydu paketi ve ID 3737 harita ekranında birlikte görsel olarak doğrulandı. Karoların uç piksel örneklemesi kenar çizgilerini önlemek için sınırlandı. Tk testlerinin bitmiş yorumlayıcıları testler arasında toplanıyor; üretim alıcısı değişmedi.


## turkey_9_katman isteğe bağlı paketi
3.396 PNG doğrulanarak ayrı veri klasörüne kuruldu; z1–11 seviyeleri. Konya örneğinde yollar/yer adları görüldü. Harita listesinde paket etkinleştirildi ve son telsiz simgesiyle açıldı. Son telsiz konumu yüksek detay kapsamı dışında olduğundan bu bölgede düşük seviyenin büyütülmesi beklenir. 71 test ve tüm kalite kontrolleri / paket derleme başarılı. Kurulum tekrarında aynı paketin korunması, bozuk paketin etkinleşmemesi ve görünür karolar için tembel yükleme test edildi.

## 2026-09-30 Otomatik çözümleme
Otomatik kanal modu eklendi: Analog FM (olası), DMR, TETRA ve kanıtla Hytera XPT etiketi. Frekans/PPM değiştirilmez. Mevcut manuel modlar ve kayıt koruması korunur. 91 donanımsız test ve kalite kontrolleri geçti; wheel/sdist derlendi. Kurulu DSD-FME + TetraBridge ile kamuya açık DMR discriminator örneğinin I/Q yeniden oynatımı üç korumalı DMR kaydı üretti; analog kayıt oluşmadı. Yeni Auto için canlı RF, gerçek TETRA/XPT ve çoklu kanal yük kabulü bekleniyor. Ayrıntı: AUTO_DECODE.md.

## 2026-09-30 Tepe frekansı / referans PPM

Canlı kanal kartına yerel FFT tepe frekansı ve girilen frekansa göre işaretli kHz farkı eklendi.
Referans merkez frekansından PPM hesaplama/kaydetme paneli eklendi; USB açılışında düzeltme
sıfır dahil gönderilip sürücüden geri okunur. Kanal frekansları otomatik değiştirilmez.
111 donanımsız test, Ruff, ty ve basedpyright geçti; wheel/sdist üretildi.
İlk kontrollerde mevcut ortamın aralıklı Tk `tcl_findLibrary` açılış hatası görüldü;
aynı tam kontrol tekrarında 111 testin tamamı geçti. Gerçek USB açılmadan yerel DLL'de
PPM set/get işlevlerinin bulunduğu doğrulandı. Sekiz sentetik kanalın ortak FFT telemetrisi
bu PC'de 100 tekrar ortalaması 10,89 ms/güncelleme ölçüldü; bu RF yük kabulü değildir.
1120/1280/1600/1920 piksel pencere genişliklerinde Tk widget geometrileri kontrol edildi.
Kaynak/ayar yedeği `data/backups/peak-readout-20260930-092546` içinde.
Canlı RF kabulü bekliyor. Son bildirilen gözlenen frekansın yönü önceki ekranla çeliştiğinden
çalışan +2 PPM ayarı değiştirilmedi; referans 427.550 MHz. Ayrıntılar: PEAK_AND_CALIBRATION.md.

### 424 MHz canlı kalibrasyon sonucu — aynı gün 09:48

Kullanıcının bilinen 424.000 MHz el telsiziyle yeni ölçümü, +2 PPM'den +15 PPM'e
düzeltme gerektirdi. Günlük, yeni alımın +15 PPM ile başladığını doğruladı.
Nominal 424.000 MHz / manuel DMR'de üç korumalı ses kaydı oluştu (3,96 / 2,88 /
6,84 sn); dosyalar mevcut, ID 3737 / grup 3737 / CC 1, fiziksel slot boş.
Ekranda görülen −0,79 kHz spektral tepe farkı kesin taşıyıcı merkez hatası sayılmadı.
Kayıtların anlaşılırlığı dinlenerek doğrulanmadı; Otomatik modun bu kalibrasyonla
gerçek RF kabulü ayrı tutuldu. Çalışan alım ve +15 PPM ayarı korunuyor.

## 2026-09-30 Sınırlı RF sinyal takibi

Kanal başına isteğe bağlı ±6,5 kHz sinyal merkezine kilit eklendi. Sayısal I/Q
telafisi girilen frekans ve PPM'yi değiştirmez. RF kilidi ve işaretli fark kartta
gösterilir: ±2 kHz dahil yeşil, dışında kırmızı, sinyal kaybı beklemesinde gri.
Ayrı hazırlık kopyasında 128 test ile Ruff, biçim, ty ve basedpyright geçti.
Ana projeye aktarımda dosya hash'leri eşleştirildi; wheel/sdist derlendi.
Gerçek DSD-FME/TetraBridge ile -5,5 ve +5,5 kHz kaydırılmış I/Q yeniden oynatımı,
her yönde üç korumalı DMR kaydı üretti (2,16 / 5,76 / 11,16 sn). Analog kayıt yok;
nominal kanal 424 MHz olarak kaldı. USB açılmadı, gerçek RF kabulü bekliyor.
Sonuç: `data/validation-follow/run-20260930-100038/validation.json`.
Yedek: `data/backups/signal-follow-20260930-100439`. Ayrıntı: SIGNAL_FOLLOW.md.

10:07 yeniden açılışında kullanıcının son kaydettiği 427.550 MHz / AUTO ve +15 PPM
korundu. Gerçek USB akışında RF kilidi 427.548131 MHz / -1869 Hz; otomatik TETRA
tanıması, CC 18 ve Main_Carrier 1094 gözlendi. Tür göstergesi arada bilinmiyora
dönüyor. 0,06 sn/1241 bayt korumalı TETRA dosyası oluşması konuşma kabulü sayılmadı.
Kontrollü ±5,5 kHz DMR canlı testi ve anlaşılır ses kabulü bekliyor.

## 2026-09-30 Arşivde CC ve slot

CC/RAN/NAC ile slot ayrı sütunlarda gösteriliyor. Sıfır dolgulu DMR CC nedeniyle
kaçırılan çözücü-slot eşlemesi düzeltildi. 134 test, Ruff, biçim, ty ve basedpyright
geçti; wheel/sdist derlendi. İlk çalışmada yeni testin paylaşılan ses dosyası
fixture'ı düzeltildi; ayrıca ortamın aralıklı Tk fonts.tcl açılış hatası tekrar
görüldü. Düzeltmeden sonraki tam çalışmada 134 test başarılı.
Gerçek oturumun 10:24 ve 10:30 çağrılarına ait loglar CC 1 / çözücü slotu 1
olarak eşleşti. Yedek sonrası sadece bu iki kaydın decoder_slot alanı tamamlandı;
fiziksel slot tahmin edilmedi. DMR.md içinde gerekçe ve yedek yolları var.

## 2026-09-30 RF güç ölçümü ve kayıt maksimumu

Kanal kartında kaymanın yanında RF seviyesi, arşiv sütunu, yeni dosya adı eki ve
SQLite güç alanları eklendi. Anten dBm değeri ancak dış referansla kalibrasyon ve
aynı alıcı koşulları eşleştiğinde yaklaşık olarak veriliyor; kalibrasyonsuz dBFS
asla dBm diye etiketlenmiyor. Ayrıntı ve sınırlamalar: RF_POWER.md.

Check-Radia.ps1: Ruff, biçim kontrolü, ty, basedpyright ve **158 testin tamamı**
tek çalışmada geçti (Python 3.14.6; 40,17 saniye; toplam kapsam %78).
`python -m uv build` wheel/sdist üretti. Donanım açmayan testlerde 90/2 saniye
sınırı, kalibrasyon/gain/AGC, eski DB şeması, dijital slotlar, güç alanları ve
dosya/DB tutarlılığı doğrulandı. Canlı RF ve referansla mutlak dBm doğruluğu
henüz doğrulanmadı. Önce kaynak ve SQLite yedeği alındı:
`D:\Projects\Biem\_SDR_Archives\2026-09-30\before-rf-power`.

Commit kancasının ikinci tam koşusunda 157 test geçti; kalan GUI testi Tk
oluşturulurken `invalid command name tcl_findLibrary` verdi. Bu makinenin önceki
harita çalışmasında da görülen aralıklı Tcl başlatma hatasıdır; uygulama koduna
girmeden oluştu. Tam 158 testin yeşil ilk koşusu korunmuştur. Hatalı GUI testi
ayrı Python sürecinde yeniden geçti (4,43 saniye); commit sırasında yalnız
kancadaki tekrar pytest adımı atlandı. Ruff/format/ty/basedpyright kancaları
atlandı sayılmaz ve yeniden çalıştırıldı.

## 2026-09-30 Hytera Ethernet ve bağımsız SNMP durumu

İki slot için IP Dispatch ses/kayıt alımı ve canlı dinleme eklendi. Önceki
ham ağ yakalamasıyla 8 korumalı kayıt ve dosya/SQLite/slot eşleşmesi doğrulandı.
Kullanıcı sesleri dinleyip işlemi başarılı buldu. Slot 2 gerçek ses testi bekliyor.

Gerçek HR659 üzerinde salt okunur SNMP GET/UDP 161 ve Trap/UDP 162 doğrulandı.
7 alarm alanı normal, ileri/yansıyan güç tanımsız (-1). Aktif tanımlı alarm yok.
Üretici OID'si/birim belgesi olmayan ham veriye anlam atanmadı. Sol menüde
`Röle var` ve durum/günlük penceresi gerçek uygulamada görsel olarak doğrulandı;
ses alımı kapalıyken SNMP yanıtları devam etti. Fiziksel arıza oluşturulmadı.

Check-Radia.ps1: Ruff, biçim, ty ve basedpyright başarılı. 168 test geçti;
bir mevcut GUI testi uygulama kurulmadan önce Python 3.14 ortamında
`ttk/altTheme.tcl` dosyasına erişim hatası verdi. Aynı test ayrı Python sürecinde
geçti: `test_five_editable_cards_tones_and_radio_guard`. Yeni SNMP testleri
GET-only kodlamayı, v1/v2c ve bozuk paketleri, kaynak filtrelemeyi, alarmı
bilinmeyen değerin temizlememesini, zaman aşımını ve soketlerin bırakılmasını
doğruladı. Ses durdurmanın SNMP'yi durdurmaması, uygulama kapanışının ikisini
durdurması ayrıca test edildi. Wheel ve sdist üretildi.

Yedek: `data/backups/snmp-before-20260930-160858`. Gerçek IP profili,
telemetri ve günlükler yalnızca yerelde. Kullanım ve teknik kaynaklar:
[HYTERA_ETHERNET.md](HYTERA_ETHERNET.md).

## 2026-09-30 SNMP voltaj ve sıcaklık değerleri

Gerçek HR659'dan alınan OCTET STRING değerleri çözüldü: 13,9855957 V,
28 °C; DC besleme, batarya bağlantısı yok. Ayrı 12 saniyelik canlı monitor
testinde bu değerler yeni ölçüm motoruna alındı; kapatmada soketler bırakıldı.
Ana ekrana özet ve alarm tablosuna ayrı ölçüm sütunu eklendi. Bilinmeyen birimler,
RSSI -200, batarya gerilimi -1, VSWR 0 gerçek sayı olarak sunulmuyor.
Yeni testlerde birimler, negatif/0 sıcaklık, endian/tip/uzunluk hataları,
NaN/sonsuz, her ölçüm için bağımsız eskime, günlük ve GUI hücreleri doğrulandı.

Check-Radia.ps1: Ruff/format/ty/basedpyright geçti; 180 test başarılı, iki mevcut
GUI testi aynı toplu Python/Tk sürecinde hata verdi (PhotoImage TclError ve
spektrum işaretçisi eşik güncellemesi). İki test de ayrı temiz Python süreçlerinde
geçti. Yeni ölçüm/SNMP odaklı 18 test ayrıca geçti. SDR/kayıt motoru değiştirilmedi.
Uygulama yeniden başlatıldı; SNMP izlemesi çalışıyor. Son manuel ekran kontrolünde
başka uygulamanın oturum açma penceresi ön plandaydı; bu pencereye müdahale edilmedi,
sayısal hücreler donanımsız GUI testiyle doğrulandı.
Yedek: `data/backups/snmp-values-before-20260930-161816`.

## 2026-09-30 RDAC benzeri skalalar ve elle RSSI okuma

Check-Radia.ps1 son çalıştırması tamamen geçti: Ruff, format, ty, basedpyright,
**189 test**, %80 toplam kapsam. `python -m uv build` wheel ve sdist üretti.
Ara odaklı testte Python/Tk'nin daha önce kaydedilmiş çoklu yorumlayıcı `tk.tcl`
hatası görüldü; ayrı süreçte test geçti ve son tam kontrolde tekrar etmedi.

Gerçek HR659 ile salt okunur GET/Trap testi: 13,99 V, 28 °C; arayüz kontrolünde
29 °C; boşta ileri/yansıyan güç 0 W. Röle adı ve kimliği cihazdan alındı.
Uygulama gerçek profille açıldı; koyu temadaki beş skala, PLL, RSSI ve yerel
ayarlar görsel olarak kontrol edildi. Ekrandaki RSSI oku düğmesine basıldı;
iki slotun yeni GET yanıtları -200 olduğundan Ölçüm yok gösterildi, iki olay da
günlüğe düştü. Aktif konuşma sırasında bu düğmenin kullanıcı testi bekleniyor.
SNMP istek-numarası/kaynak-port eşleştirme, ilgisiz cevap, yanlış kaynak,
zaman aşımı, hata cevabı, kapanış ve çift tıklama donanımsız testte doğrulandı.
Koyu/açık tema ve dar yerleşim ayrıca GUI testinde doğrulandı.

Röle GNSS harita işi kısmi: SNMP adı haritaya bağlı; ayrı simge, geçerli fix
kontrolü ve odaklama arayüzü sentetik koordinatla test edildi. Gerçek koordinat
bildirimi alınmadı; eldeki MIB GNSS tanımı içermiyor. Canlı GNSS çözümü/harita
beslemesi henüz uygulanmadı. Kimlik verisi veya telsiz konumu röle koordinatı
sayılmaz. CPS yalnızca görüntülendi; ayar yazılmadı. SDR ve ses motoru aynı.

Yedek: `data/backups/hytera-gauges-before-20260930-162703`.
