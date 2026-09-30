# Hytera HR659 Ethernet alımı

Güncelleme: **2026-09-30**. IP Dispatch alım sürücüsü, iki slot için bağımsız
ses kaydı ve canlı dinleme uygulandı. SDR kaynaklarına, DLL'lerine, USB sürücüsüne,
RF kazanç/PPM ayarlarına dokunmaz. Bu bir IPSC master veya RF verici değildir.

## Kullanım

1. **Hytera Ethernet → Bağlantı ayarları** bölümünde rölenin IPv4 adresini ve bilgisayarın o ağdaki
   IPv4 adresini girin. Bilgisayar adresi CPS içindeki **Third Party Server IP**
   ile aynı olmalı. CPS'te **Forward to PC** açık, **Defined Mode** seçili olmalı.
2. Bu HR659 testinde doğrulanan UDP portları:

   | Hizmet | Slot 1 | Slot 2 |
   | --- | ---: | ---: |
   | Radio Call Control | 30009 | 30010 |
   | Radio Voice Service | 30012 | 30014 |

3. **Ayarları kaydet** yalnızca yerel profili kaydeder. **Röleye bağlan** alımı
   başlatır. Program açılışında kendiliğinden ses alımı başlamaz. SNMP durum
   izlemesi ayrı bir tercihtir; açık kaydedilirse sonraki açılışta devam eder.
4. **Röle yanıtı: 4/4 port** iki slotun kontrol/ses portlarından son 15 saniyede
   geçerli paket alındığını gösterir; konuşma alındığı anlamına gelmez. Ses paketi
   sayacı, kayıp sayacı ve ses göstergesi ayrıca izlenir.
5. **Slot 1 canlı dinle / Slot 2 canlı dinle** seçili slotu hoparlöre verir.
   **Sesi kapat** kaydı durdurmaz. **Bağlantıyı kes** iki slotun kayıtlarını
   tamamlar, UDP portlarını serbest bırakır. Üstteki **Durdur** hem SDR hem Hytera
   alımını durdurur; SDR sayfasının **Başlat** düğmesi Hytera'yı başlatmaz.
6. Kayıtlar mevcut **Kayıt arşivi** sayfasında `Hytera • Slot 1/2` kanalı ve
   `DMR/Hytera-IP` kaynağıyla bulunur. Kanal, tarih, ID, grup veya slotla aranabilir.
   Dinleme için mevcut Windows yönetici kuralı devam eder.

## Kayıt ve veri kuralları

- RCP `0xB845` içinden kaynak ID, hedef ID, çağrı türü ve durum okunur. Grup alanı
  yalnızca açıkça grup çağrısı bildirildiğinde doldurulur; özel hedef grup değildir.
- Port-slot eşlemesi CPS ile doğrulanmıştır. Pakette ayrıca slot seçeneği varsa
  portla eşleşmesi gerekir. Slotlar ve RTP akışları karıştırılmaz.
- RTP sürüm 2, payload type 0: **G.711 µ-law / 8 kHz / mono**, PCM16 WAV'a çevrilir.
  Değişken RTP başlığı, CSRC, uzantı, dolgu ve paket sınırları kontrol edilir.
- Kontrol paketi olmadan gelen ses, bilinmeyen ses biçimi veya E2E hizmeti kayıt
  kabulü sayılmaz. Yeni çağrı başlangıcı kaybolduğunda önceki çağrının ID'si sese
  taşınmaz. Bu ilk sürümde böyle bir konuşma eksik kalabilir; kontrolsüz sesin
  sınırlı tamponla kurtarılması sonraki güvenilirlik çalışmasıdır.
- Tekrar/gecikmiş paketler atılır. 150 ms'ye kadar sıra düzeltmesi yapılır;
  kısa kayıplar zaman çizelgesinde sessizlikle korunur. Büyük zaman/sıra kopuşunda
  çağrı kapatılır; önceki konuşmanın örnekleri tekrar edilmez.
- Her kayıt en fazla **90 saniye**, devam eden seste yeni kayıt öncesi **2 saniye
  ara**. Konuşma bitişi, ses zaman aşımı, bağlantıyı kesme ve program kapanışı
  dosyayı tamamlar. Tamamlanmamış `TEMP_hytera_...wav` çökme durumunda korunur.
- Ana uygulamada mevcut **Windows DPAPI** zarfı kullanılır (`.wav.radia`);
  bu, aynı Windows hesabı/yöneticiye karşı mutlak kopya koruması değildir.
- Dosya adı mevcut DMR ID/grup/tarih/saat/süre düzenindedir. Slot ayrıca SQLite'a
  yazılır; aynı ad çakışırsa dosya ezilmeden numara eklenir.
- Bu HR659 kontrol/ses akışında **CC, RF frekansı ve anten dBm bilgisi doğrulanmadı**.
  CC ve RF gücü NULL bırakılır. Eski DB'nin NOT NULL frekans alanında 0, bilinmeyen
  ağ frekansı anlamındadır; arayüz `—` gösterir. SDR kanal frekansı kopyalanmaz.
- Ağ sesinin dBFS göstergesi **ses etkinliğidir**, anten/RF gücü değildir.
- SMS, GNSS/GPS, RRS ve telemetri portlarının CPS'te açık olması, bu sürücünün
  bunları çözdüğü anlamına gelmez. Şimdilik sadece dört kontrol/ses portu açılır.
- `Dijital veri günlüğü` sayfasında röle kontrol çıktısı ve ham HEX görülebilir.
  Kayıtlar, gerçek IP profili, ham paketler ve günlükler `data/` altında yerel
  tutulur, Git'e eklenmez. Profil: `data/hytera.json`.

## Canlı test — 30 Eylül 2026

- Kullanıcının HR659 cihazına ping 3/3 başarılı; ARP MAC değeri CPS ile eşleşti.
- İki slotun dört portundan HSTRP heartbeat alındı. Yalnızca oturum kurma,
  heartbeat ve gelen paket ACK'leri gönderildi. PTT, çağrı kurma veya ses gönderimi
  yapılmadı. CPS ve Windows güvenlik duvarı değiştirilmedi.
- Kullanıcının telsiz denemelerinde Slot 1'de geçerli RCP grup/kaynak ID bilgisi
  ve **743 PCMU ses paketi** yakalandı. Ham test yakalaması yeni kayıt motorunda
  yeniden işlendi; **8 korumalı kayıt** oluştu (0,72–12,60 sn).
- Çözülen kayıtlarda 17 eksik RTP paketi görüldü. Kontrolü olmayan/gecikmiş
  136 paket kabul edilmedi. Bu rakamlar kontrollü ilk test yakalamasına aittir;
  kayıpsız ağ veya tüm konuşmaların eksiksiz alındığı iddiası değildir.
- WAV başlığı, 8 kHz örnek sayısı, korumalı dosyanın çözülebilmesi, SQLite
  ID/grup/slot ve dosya eşleşmesi doğrulandı. **Kullanıcı 30 Eylül'de işlemin
  başarılı olduğunu ve seslerin güzel geldiğini bildirdi.** Slot 2 üzerinden
  gerçek konuşma testi bekleniyor.
- Firmware alanındaki önceki “2.5” notu cihazdan okunarak doğrulanmadı.

## Teknik kaynaklar

Bağımsız alım uygulaması, gözlenen HR659 trafiği ve aşağıdaki protokol
belgeleri/açık kaynak araştırmalarıyla geliştirildi. Projelerden çalıştırılabilir
kod veya bağımlılık taşınmadı. HytBridge örneği RF gönderimi yaptığı için çalıştırılmadı.

- [HytBridge IP Dispatch araştırması](https://github.com/dk7lst/HytBridge) — GPLv3.
- [OK-DMR Hytera PDU araştırması](https://github.com/OK-DMR/ok-dmrlib/tree/master/okdmr/dmrlib/hytera/pdu) — AGPL.
- [RFC 3550 RTP](https://www.rfc-editor.org/rfc/rfc3550).
- [RFC 3551 PCMU / RTP ses profili](https://www.rfc-editor.org/rfc/rfc3551).

Donanımsız testler: HSTRP TLV/sağlama toplamı/ACK, RTP uzantı/dolgu/codec,
G.711 sabit örnekleri, iki slot, özel/grup ayrımı, sıra/tekrar/kayıp, eski ID'nin
taşınmaması, E2E reddi, 90/2 saniye, kapatmada portların bırakılması ve gönderilen
paketlerin sadece 6 baytlık taşıma kontrolü olması.

## SNMP cihaz durumu ve arıza günlüğü — 30 Eylül 2026

**Hytera Ethernet → Röle durumunu izle (SNMP)** ile ses kaydı kapalıyken de
cihaz izlenir. Sol menüde renk yanında durum yazısı bulunur. Dar ekranda
Hytera simgesi ve renkli nokta görünür; ayrıntı için simgeye dokunulur.

- **Yeşil / Röle var:** son 35 saniyede geçerli SNMP yanıtı veya bildirimi geldi.
- **Yeşil / Bağlı:** iki slotun dört kontrol/ses portu yanıtlıyor. Bu tek başına
  aktif konuşma ya da tüm donanımın arızasız olduğu anlamına gelmez.
- **Turuncu:** kısmi ses bağlantısı, ses bağlantısı bekleniyor veya SNMP izleme
  hatası. Ses çalışırken SNMP kesilirse `Ses bağlı • SNMP yok` gösterilir.
- **Kırmızı / Yanıt yok:** izleme açıkken 35 saniyedir SNMP yanıtı yok ve ses
  bağlantısı da doğrulanamıyor. Bu durum fiziksel cihaz yokluğu ile ağ/güvenlik
  duvarı sorununu tek başına ayırt etmez.
- **Kırmızı / Alarm:** tanımlı üretici alarm kodu pozitif. İlgisiz yeni paket
  veya bilinmeyen değer alarmı temizlemez; aynı alanın normal bildirimi gerekir.
  Alarm verisi eskirse son alarm, `veri eski` uyarısıyla korunur.
- **Gri:** izleme kapalı, ayarlanmamış veya ilk yanıt bekleniyor.

**Durum ve olay günlüğü** düğmesi 9 alarm alanını, son bildirim yaşlarını ve
son 100 olayı yerel saatle gösterir. `Veri günlüğü` sayfasında da ham OID/değerler
görülebilir. Tam günlük günlük dosyalara yazılır:
`data/hytera-status/YYYY-MM-DD.jsonl`. Dosyadaki `observed_utc` UTC'dir.
Günlük ve gerçek cihaz profili Git'e gönderilmez.

Röleye yalnızca SNMPv1 **GET / UDP 161** gönderilir; 10 saniyede bir standart
sysUpTime ve 9 alarm nesnesi sorgulanır. Her nesne ayrı sorgulandığından
desteklenmeyen alan diğerlerini engellemez. **UDP 162** üzerinde SNMPv1 ve v2c
Trap dinlenir. Kaynak IP, sorgu yanıt portu, istek numarası ve OID doğrulanır.
SET, yeniden başlatma veya RF gönderimi yoktur. Yalnızca MIB'de belgelenen
varsayılan okuma topluluğu kullanılır; XNMS erişim kodu okunmaz/değiştirilmez,
topluluk değeri günlüğe yazılmaz. Farklı topluluk/SNMPv3 için bu sürümde ayar yoktur.

CPS'te Trap IP, bilgisayarın yerel IP adresi; Trap portu 162 olmalıdır.
Broadcast Trap ve Local Machine Info Trap, kullanıcı tarafından etkinleştirilip
röleye yazıldı. Windows güvenlik duvarına veya CPS ayarlarına yazılım müdahale etmez.
UDP 162 kullanımda ise salt okunur sorgular devam eder; günlükte uyarı görünür.
Ses **Durdur / Bağlantıyı kes** ile kapanır; SNMP ayrı kutudan kapatılır.
Program kapanışında iki servis de portlarını bırakır.

### Donanımda gözlenen sonuç

Gerçek HR659'dan GET yanıtları ve CPS yazımından sonra Trap bildirimleri alındı.
Gerilim, sıcaklık, fan, VSWR, TX PLL, RX PLL ve batarya alanları `0 / normal`
bildirdi. İleri ve yansıyan güç alanları `-1 / tanımsız` bildirdi; bunlar normal
olarak sayılmadı. Aktif tanımlı alarm gözlenmedi. Gerçek arıza oluşturulmadı;
alarm oluşması/temizlenmesi ve zaman aşımı donanımsız testlerde doğrulandı.
Üreticiye özgü sayısal byte dizileri belgelenmiş birim ve byte sırası olmadan
volt, derece veya RF gücü diye yorumlanmaz. Aşağıdaki ölçüm desteğinde gerilim
ve sıcaklığın biçimi ayrıca doğrulandı. Standart GNSS trap ayarının açık
olması, yeni geçerli GPS koordinatı alındığı anlamına gelmez.

Kaynaklar:

- [Hytera XNMS/CPS bağlantı ayarları](https://www.hytera.com/en/services/feedback/detail.page/product-problem-253/).
- [Hytera HR65X ürün bilgisi](https://www.hytera.com/en/product-new/digital-radio/dmr-system/hr65x.html).
- [Hytera üretici MIB'i, LibreNMS arşivi](https://github.com/librenms/librenms/blob/master/mibs/hytera/HYTERA-REPEATER-MIB) — 2014 sürümü; HR659'da cevaplanan alanlar yukarıda ayrıca belirtilmiştir.
- [RFC 1157](https://www.rfc-editor.org/rfc/rfc1157), [RFC 3416](https://www.rfc-editor.org/rfc/rfc3416).

## Sayısal ölçümler — 30 Eylül 2026

Kullanıcının isteğiyle, alarm durumundan ayrı **Ölçülen değer** sütunu eklendi.
Hytera ana sayfasında besleme voltajı, güç katı sıcaklığı, besleme türü ve batarya
bağlantısı da görünür. Durum penceresinde ilave RSSI/besleme satırlarına sağdaki
kaydırma çubuğuyla ulaşılır. GET listesine aşağıdaki 8 salt okunur nesne eklendi:

| Veri | `1.3.6.1.4.1.40297.1.2.1.2.` sonrası | Gösterim |
| --- | --- | --- |
| Besleme gerilimi | `1.0` | V, 2 ondalık |
| Güç katı sıcaklığı | `2.0` | °C, 1 ondalık |
| VSWR | `4.0` | oran `:1`; 0 ölçüm yok |
| Slot 1 / 2 RSSI | `9.0` / `10.0` | MIB birimi dB; -200 ölçüm yok |
| Besleme türü | `11.0` | DC / Batarya |
| Batarya bağlantısı | `12.0` | Bağlı / Bağlı değil |
| Batarya gerilimi | `13.0` | V; -1 ve 0 ölçüm yok |

MIB float alanları 4 baytlık OCTET STRING'dir. IEEE754 float32 little-endian
biçimi LibreNMS'nin Hytera sensör uygulamasıyla kontrol edildi; standart Python
`struct` çözümü kullanılır, üçüncü taraf kod taşınmaz. Byte sırası otomatik tahmin
edilmez. Bozuk uzunluk/tip, NaN, sonsuz ve anlamsız değerler sayı olarak gösterilmez.
Sıcaklıkta 0 ve -1 °C geçerli olabilir; gerilim için kullanılan boş-değer kuralı
sıcaklığa uygulanmaz. MIB'nin RSSI birimi dB'dir; dBm ya da SDR anten ölçümü olarak
yeniden etiketlenmez. Fan devri doğrulanmadığı için rpm yazılmaz. İleri/yansıyan
güç için sonraki RDAC skala çalışması aşağıda açıklanmıştır.

Her ölçümün kendi son alınma zamanı tutulur. Başka bir Trap gelmesi eski voltajı
güncel yapmaz. 35 saniyeyi aşan veya izleme kapalıyken görülen sayılar eski veri
olarak işaretlenir. Ölçüm değişimleri okunabilir birimli metin ve ham OID/değerle
günlüğe yazılır; ayrıca dakikalık ölçüm özeti vardır. Ölçüm değeri, ayrı üretici
alarm bildirimini kendiliğinden temizlemez.

Gerçek HR659 yeniden açıldıktan sonra GET ile **13,9855957 V** ve **28,0 °C**,
DC besleme, batarya bağlantısı yok, RSSI -200, batarya gerilimi -1 alındı.
Bunlar cihazın bildirdiği ölçümlerdir; harici voltmetre/sıcaklık referansıyla
kalibrasyon testi yapılmadı. Daha önceki Trap kaydındaki 13,929653 V ve 28 °C de
aynı kodlamayla çözüldü.

Ek teknik kaynaklar:

- [LibreNMS Hytera voltaj sensörü](https://github.com/librenms/librenms/blob/master/includes/discovery/sensors/voltage/hytera.inc.php).
- [LibreNMS Hytera sıcaklık sensörü](https://github.com/librenms/librenms/blob/master/includes/discovery/sensors/temperature/hytera.inc.php).
- [LibreNMS Hytera float dönüşüm tanımı](https://github.com/librenms/librenms/blob/master/includes/functions.php).

## Görsel skalalar ve RSSI oku — 30 Eylül 2026

Hytera sayfasında beş skala bulunur: besleme 0–30 V, sıcaklık 0–100 °C,
VSWR 1:1–6:1, ileri güç 0–70 W ve yansıyan güç 0–15 W. Bu aralıklar kullanıcının
RDAC örneğindeki gösterim aralıklarıdır; alarm eşikleri değildir. Aralık dışındaki
sayının metni korunur, çubuk sınıra dayanır ve `Skala dışında` yazılır.
Alarm rengi bağımsız üretici alarmından gelir. Alıcı ve verici PLL alanları
MIB'deki **normal/kilit hatası alarmını** gösterir; RDAC'ın 0/1 kilit durumu ile
karıştırılmaz. Karanlık/aydınlık tema, dar ekranlarda satır düzeni ve sayfa
kaydırması desteklenir. Bağlantı ayarları açılır bölümde, ses kontrolleri aynı sayfadadır.

RDAC ekranının W birimi ve mevcut float kodlamasıyla ölçüm `5.0` / `6.0` alanları
eklendi. Sıfır W geçerli boşta ölçüm; -1 ölçüm yoktur. Gerçek cihazda yalnızca
0 W örneği doğrulandı; sıfırdan büyük RF gücü harici ölçümle karşılaştırılmadı.

**RSSI oku** düğmesi, açık SNMP servisinde iki slot için hemen yeni GET gönderir.
Sonuç yalnızca o isteğin IP/port/istek numarası/OID eşleşen yanıtından gelir.
Eski önbellek veya otomatik sorgu cevabı elle okumayı tamamlayamaz. Her slot
bağımsız yanıtlanır; 3 saniyede yanıt gelmezse `Yanıt yok`, servis durursa
`Okuma durduruldu`, -200 gelirse `Ölçüm yok` gösterilir. Okuma sırasında düğme
kilitlidir. Son elle okuma zamanı görünür; yeni sorguya kadar bu sonuç korunur.
Olaylar yerel tarihli SNMP günlüğüne yazılır. Bu düğme SET veya RF komutu göndermez.

Gerçek HR659 GET ve uygulama düğmesiyle iki-slot sorgu testi yapıldı; boşta
iki slot -200 verdi. Daha önceki gerçek Trap günlüklerinde negatif aktif RSSI
örnekleri var; bu sürümün aktif konuşma sırasında düğme testi kullanıcı kabulünü bekliyor.

## Röle adı ve GNSS harita hazırlığı

`rptRadioAlias` (`...1.2.4.6.0`, cihazda doğrulanan UTF-16LE) ve `rptRadioID`
(`...1.2.4.7.0`) salt okunur sorgulanır. Rölenin adı Hytera ve Harita ekranlarına
aktarılır. Haritada telsiz işaretçisinden ayrı anten-kule simgesi ve `Röleye yaklaş`
kontrolü hazırdır; sadece açıkça doğrulanmış röle GNSS konumu ile etkinleşebilir.
Kimlik, bilinmeyen ham sayılar ve telsizden gelen eski konum bu simgeyi oluşturmaz.

**GNSS alım entegrasyonu henüz tamamlanmadı.** Kullanıcı antenin takılı ve konumun
alındığını belirtti. Mevcut GET/Trap kayıtlarında geçerli enlem/boylam yok; eldeki
2014 üretici MIB'i GNSS nesnelerini tanımlamıyor. Harita bunu `GNSS koordinatı henüz
alınmadı` diye bildirir. Çizim arayüzü yalnızca simüle edilmiş geçerli/bozuk konumlarla
test edildi; canlı GNSS paketini bu arayüze aktaran çözücü henüz yoktur. Güncel HR659
GNSS Trap MIB/API tanımı veya gerçek koordinat paketi alınarak birim, eksenler,
geçerli fix bilgisi ve kaynak kimliği doğrulanmalıdır. Cihaz adı okunması GNSS
başarısı sayılmaz. CPS ayarları ve Windows ağ ayarları değiştirilmedi.

Ek referans: [Hytera RDAC uygulama notları](https://setronics.net/wp-content/uploads/descargables/Documentos-software/DMR/RD626/Manual%20Tecnico/WF_DMR%20Conventional%20Series%20RDAC%20Application%20Notes%20R2.1.pdf).
