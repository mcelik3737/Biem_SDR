# Hytera HR659 Ethernet alımı

Güncelleme: **2026-09-30**. IP Dispatch alım sürücüsü, iki slot için bağımsız
ses kaydı ve canlı dinleme uygulandı. SDR kaynaklarına, DLL'lerine, USB sürücüsüne,
RF kazanç/PPM ayarlarına dokunmaz. Bu bir IPSC master veya RF verici değildir.

## Kullanım

1. **Hytera Ethernet** sayfasında rölenin IPv4 adresini ve bilgisayarın o ağdaki
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
volt, derece veya RF gücü diye yorumlanmaz. Standart GNSS trap ayarının açık
olması, yeni geçerli GPS koordinatı alındığı anlamına gelmez.

Kaynaklar:

- [Hytera XNMS/CPS bağlantı ayarları](https://www.hytera.com/en/services/feedback/detail.page/product-problem-253/).
- [Hytera HR65X ürün bilgisi](https://www.hytera.com/en/product-new/digital-radio/dmr-system/hr65x.html).
- [Hytera üretici MIB'i, LibreNMS arşivi](https://github.com/librenms/librenms/blob/master/mibs/hytera/HYTERA-REPEATER-MIB) — 2014 sürümü; HR659'da cevaplanan alanlar yukarıda ayrıca belirtilmiştir.
- [RFC 1157](https://www.rfc-editor.org/rfc/rfc1157), [RFC 3416](https://www.rfc-editor.org/rfc/rfc3416).
