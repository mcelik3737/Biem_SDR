# Codex uygulama ve kabul işleri - BM-ICC-08

## Başlangıç

Windows'taki çalışan branch, config ve sürüm manifesti önce dondurulur. Depodaki 0.1.0 pyproject sürümü, bütün yerel DMR/TETRA/güvenlik özelliklerini temsil etmiyor. Bu belge donanım ve ürünleştirme işleri içindir; çalışan SDR# veya analog alımın üzerine sürücü/yazılım yazılmaz.

## Bağımlı uygulama sırası

| Öncelik | İş / somut sonuç | Kabul |
|---|---|---|
| P0 | PC/V3 sürüm ve seri numarası envanteri; tek V3 PPM kalibrasyonu | Frekans hatası Hz ve ppm olarak kaydedilir; decoder taşıyıcı ofsetiyle karıştırılmaz. |
| P0 | Kayıt motorunu kullanıcı ekranından ayıran Windows servisi | Oturum açılmadan kayıt; UI kapansa da kayıt; elektrik geri geldiğinde BIOS açılışı + servis başlangıcı testli. |
| P0 | Alıcılar için seri/USB yolu ile kalıcı kimlik | RF1/RF2 yeniden başlatmada yer değiştirmez; aynı seri varsa onboarding'de düzeltilir. |
| P0 | İki SDR'ye ayrı worker ve kaynak kilidi | Bir aygıt düşerse diğer alıcı ve arşiv oynatma devam eder; spektrum/FM radyo kaynak kullanımını çakıştıramaz. |
| P0 | Kanal planı / kanalizer / süreç sınırları | Tüm seçili frekanslar bir SDR'nin kabul edilmiş RF penceresine sığıyor; tarama modu eşzamanlı diye gösterilmez. |
| P0 | Kayıt yaşam döngüsü ve atomik metadata | WAV/decode çıktısı kapandığında süre/ID/grup/slot/CC/null ayrımı korunur; yarım kayıt kurtarılır. |
| P0 | Disk yöneticisi | Doluluk uyarısı, ayrılmış alan, kilitli kaydı silmeyen retention, disk yazma hatası ve alarm. |
| P1 | Roller ve anahtar kurtarma | Admin/dinleyici/teknisyen; audit; DPAPI servis hesabı, SSD değişimi ve dışa aktarım politikası testli. |
| P1 | REC/LAN/PWR fiziksel LED protokolü | USB denetleyiciye saniyede heartbeat; gerçek yazma durumu; heartbeat kaybında REC söner ve hata görünür. |
| P1 | İmzalı kurulum, güncelleme ve geri dönüş | Veri alanı ayrıdır; güncelleme başarısızsa önceki uygulama açılır; arşiv kaybolmaz. |
| P1 | Windows üzerinden güvenli yerel ağ yönetimi | İlk prototipte yetkili bakım oturumu; uzaktan GUI oturumunun kapanması kaydı durdurmaz. RDP internete açılmaz. Web arayüzü ayrı gelecek işidir. |
| P2 | Lisanslı DMR/TETRA SDK geçişi | Lisans matrisi kapandıktan sonra; aynı referans RF/WAV setinde ses ve metadata regresyonu. |

## LED ve buton davranışı

- PWR: USB denetleyici beslemesi tek başına “kayıt sağlıklı” değildir. Sabit yeşil yalnız servis heartbeat'i ve sağlıklı durum birlikteyken; başlangıçta yanıp söner.
- REC: yalnız aktif arşiv yazımı onaylandığında kırmızı. Decoder'da ses görülmesi, dosya başarıyla yazılmış olduğu anlamına gelmez.
- LAN: link/IP durumu için mavi; internet bağlantısı göstergesi değildir. Ağ kaybında kayıt sürer.
- Her LED'de 680 ohm seri direnç, 3,3 V GPIO; prototip RP2040 USB kartı. USB çıkışı fan veya PC güç düğmesini doğrudan sürmez.
- Ön güç kumandası ilk prototipte PC'nin kendi düğmesine mekanik basar. Güvenli kapama ayarı ve kapanmadan dosya flush'u test edilir. Donanım header pinleri tahmin edilmez.

## Kayıt süreleri ve arşiv kapasitesi

Konseptte istenen 90 saniye kayıt / 2 saniye ara davranışı korunacaksa, kesintisiz taşıyıcı üzerinde 90/92 = %97,83 kayıt zaman oranı oluşur. Bunun “kesintisiz kayıt” olarak pazarlanması doğru değildir. Uzun çağrıda bölme hedefi ile 2 saniyelik gerçek boşluk ayrı ürün kararları olarak görünür olmalıdır. Ses kaybını önlemek için boşluksuz dosya rotasyonu ayrı kabul işi olabilir; kullanıcı gereksinimi sessizce değiştirilmez.

DSD-FME mevcut yolunda dosya çağrı bitince içeri alınıp bölünüyor; 90 saniyede canlı teslim davranışı yok. TETRA sessiz taşıyıcı için son not 20 saniye; eski 120 saniye notu kodla karşılaştırılacak. Metadata'da bilinmeyen ID/slot/CC boş kalır; fiziksel slot ile decoder lane karıştırılmaz.

Hesap: 16 kHz × 16 bit × mono = 32.000 byte/s = 2,7648 GB/gün/sürekli ses akışı. 1 TB diskte %20 ayrılmış alan varsayımıyla 800 GB arşiv: 8 akışta yaklaşık 36,2 gün, 16 akışta 18,1 gün. Bu PCM üst sınır hesabıdır; arşiv ek yükü için ayrıca %10 bırakılması halinde sırasıyla yaklaşık 32,9 ve 16,4 gün. Görev döngüsü düştükçe süre uzar; gerçek dosya biçimiyle ölçüm gerekir. Sürekli ham IQ kaydı ana arşiv değildir: tek 2,4 MS/s, 8-bit I + 8-bit Q yaklaşık 414,7 GB/gün üretir.

## FAT / EVT testleri

| Test | Düzenek / süre | Başarı ölçütü (tasarım hedefi) |
|---|---|---|
| Frekans doğruluğu | Referans RF kaynağı, 30 dk ısınma, VHF/UHF izinli test frekansları | PPM ve Hz raporu; 6,25/12,5/25 kHz kanal ayarlarında merkezleme; rastgele ofset düzeltmesi yok. |
| Analog ses | Kontrollü RF + referans kayıt | Seçili kanalda anlaşılır ses; komşu kanala yanlış kayıt yok; mevcut kabul edilen analog davranış korunur. |
| DMR | Bilinen kaynak/hedef ID, TG, CC ve iki slot | 100 kontrollü çağrıda etiketler doğru; bilinmeyen alanlar null; özel çağrı TG diye gösterilmez. |
| TETRA | İzinli gerçek saha ve referans dosya | Trafik taşıyıcısı ve slotlar doğru; anlaşılabilir ses; şifreli içerik için destek uydurulmaz. |
| İki SDR hata izolasyonu | Tek USB çıkar, yeniden tak; toplam 20 çevrim | Diğer kaynağın kaydı sürer; kaynak kimliği değişmez; kayıp süre loglanır. |
| 4 RF yük | Gerçek/test RF, 24 saat | Uygulama/USB kaynaklı kayıp örnek 0; CPU p95 <= %70, disk kuyruğu/memory kararlı hedef. |
| 8 RF yük | 8 taşıyıcı; DMR iki slot için 16 ses senaryosu, 72 saat | Önceki hedefler; metadata çapraz karışma yok; gerçek hava kaynaklı hatalar yazılım kaybından ayrı ölçülür. |
| Güç kesilmesi | Aktif kayıt/yazma sırasında 20 kontrollü kesinti | Eski arşiv sağlam; mevcut kısmi dosya kurtarılır veya eksik olduğu açıkça işaretlenir; servis otomatik gelir. |
| Ağ kesilmesi | 30 dk kesinti; yeniden bağlan | Kayıt devam eder; arama/oynatma geri gelir; dış saat yoksa zaman belirsizliği loglanır. |
| Disk dolu/yazma hatası | Test diskinde eşikler ve izin hatası | Arşiv korunur; kilitli kayıt silinmez; görünür hata; sessiz başarısızlık yok. |
| Kurtarma ve yetki | Yeni SSD/servis hesabı, yanlış rol, anahtar kaybı simülasyonu | Yetkili restore denenmiş; geçici decoder WAV/raw log erişimi kontrol altında. |
| Isı ve RF paraziti | Kasa açık/kapalı, fan açık/kapalı; 35 °C giriş havasında 24 saat hedef | Bileşen sınırları altında; throttling/kayıp yok; aynı RF düzenekte gürültü tabanı artışı <=3 dB proje hedefi. |
| Mekanik/rack | Tork, kablo çekme, raf destekli montaj, taşıma | Soketlere yük yok; keskin kenar yok; ayaklar çıkarıldığında 2U yerleşim; final kütle etiketi. |

Hedefler test sonucu değildir. Kontrollü RF çoklu taşıyıcı üretilemiyorsa 8 kanal “kabul edildi” yazılmaz; dosya oynatması donanım RF kabulünün yerine geçmez. Ölçülen CPU sıcaklığı için bilgisayar üreticisinin limitleri kullanılır; -20/+70 °C ürün iddiası verilmez.

## Zaman ve çıkış kapıları

Parçalar ve çalışan yazılım imajı hazır olduğunda 1-3 iş günü giriş/tek V3 testi; yaklaşık 7-12 iş günü kasa numunesi planı; ardından 2 iş günü montaj. Bunlar satıcı termin taahhüdü değildir. İki SDR/servis/hata kurtarma için 2-4 hafta plan rezervi; EVT ve uygunluk hazırlığı için 8-12 hafta başlangıç planı. Lisans sözleşmesi veya laboratuvar kuyruğu bu süreyi uzatabilir.

Çıkış: EVT numunesi -> PPM/iki SDR -> 4 RF -> 8 RF -> uzun süre/fault -> lisans ve uygunluk -> pilot parti -> ticari sürüm. Her kapının sahibi, rapor bağlantısı, gerçek tarih ve sürüm hash'i üretim takip kaydında doldurulur. Hiçbiri bu tasarım teslimiyle tamamlanmış sayılmaz.
