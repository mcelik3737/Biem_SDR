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
