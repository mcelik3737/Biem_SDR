# Codex uygulama görevi — BİEM Radia Operasyon V2

**Teslim: 12 Eylül 2026.** Kullanıcının istediği işlem: açık renkli Operasyon tasarımını mevcut çalışan Python/Tkinter/ttk uygulamasına uygula. Bu klasör uygulanabilir görsel referanstır. Ana örnek [BIEM_Radia_Arayuz_Onizleme.html](BIEM_Radia_Arayuz_Onizleme.html); tüm veriler temsili. Senaryo / yönetici önizleme çubuğunu, örnek veri kümelerini ve örnek olay ekleme düğmelerini üretime taşıma.

## Önce çalışan yerel kaynak

Kanonik proje `D:\Projects\Biem\_SDR`. Kullanıcının yüklediği `BIEM_RADIA_GUNCEL_BRIF.md` / `Yapıştırılan markdown.md` **tam olarak okundu**; iki dosya aynı içerikte (SHA-256 `9b66ddc479013e6c61e1c8ef6e9e6cd705a83428b18cb7a778e6436adc2a9a10`). V2, bu belgenin 21. bölümündeki teslim isteğini esas alır. Yerel en güncel brifle karşılaştır; çalışan, henüz commit edilmemiş değişiklikleri koru. GitHub `main@e27f0a9` veya `codex/dmr-receiver@4e30773`, çalışan 0.2.0 yerel sürümünün tam yedeği değildir.

**Bu tasarım dalının eski `src` dosyalarını çalışan Windows projesinin üstüne kopyalama.** Yalnız `docs/ui/` girdilerini al. Yerel değişiklikleri inceleyip güvenli bir çalışma dalında mevcut kaynak üzerinden ilerle. SDR# kurulumu, USB sürücüleri, gerçek kayıtlar, ayarlar ve üçüncü taraf çözücüler korunur. Qt / WebView / web uygulaması göçü bu görevin parçası değildir.

## V1’den V2’ye kararlar

| Korunan | Düzeltilen / eklenen |
|---|---|
| Açık zemin, lacivert gezinme, özgün BIEM logosu | Büyük üst boşluk azaltıldı; okunur altı kanal ve canlı RF kazancı / Tuner AGC alanı |
| İzleme kartı + seçili çağrı ayrıntısı | Yapılandırılan mod / çözülen protokol ve CC filtresi / alınan CC ayrıldı |
| Arşiv arama ve çağrı bağlamı | `.wav.radia`, normal süreç dinleme kilidi, dosya çözme hatası |
| Kaynak ve spektrum ayrımı | FM RADIO, üç kaynak sekmesi, büyük grafik ve iki yanda kaydırıcılar |
| Kimlik rehberi kapsamı | Özel hedef / grup ve fiziksel slot / çözücü kanalı ayrımı |
| — | Harita, son geçerli konumun yaşı, dijital veri günlüğü |

Üç tema yerine **tek olgun Operasyon düzeni** önceliklidir. Sahte oturum/rol, disk kapasitesi, hazır dalga biçimi, ileri sarma ve oynatma hızı kaldırıldı. TETRA ses çözücüsü yokmuş gibi gösterilmez.

## Ekranlar ve davranışlar

| Alan | Uygulama kararı |
|---|---|
| Başlık | Orijinal logo 140 × 44 mantıksal px içinde; RADIA; mevcut SDR işi; FM RADIO; alımı başlat / durdur. İşin açık olması, ses veya arşiv başarısı anlamına gelmez. |
| Gezinme | Canlı izleme → Kayıt arşivi → Harita → Kimlik rehberi → Dijital veri günlüğü; Sistem: Spektrum → Kaynaklar ve ayarlar → BİEM. Normal süreçte arşiv listesi açık kalır. |
| Canlı | Sabit sıralı altı kart, ayrı kaynak/iş/alım biçimi, RF kazancı ve Tuner AGC. Salt okunur kart; düzenleme paneli. Alım sırasında frekans/protokol düzenleme kilitli. Desteklenen canlı kazanç yolu kullanılabilir. |
| Kart | Kanal adı, yapılandırılan mod, metinli durum; MHz, dBFS, süre; kaynak adı/ID, grup **veya** özel hedef, doğrulanmış slot türü. Kimlik bilinmiyorsa boş/“Bilinmiyor”. Önceki çağrı kimliği taşınmaz. |
| Seçili çağrı | Kaynak ID, hedef türü/ID, fiziksel slot, çözücü kanalı, ayarlanan/çözülen protokol ve ayarlanan/alınan CC ayrı. Monitör sesi, kayıt durdurmayla aynı işlem değildir. |
| Arşiv | Başlık/kanal/ID, tek yerel tarih, fiziksel/çözücü slot ayrımlı filtre. Günlük tarih biçimi açık. Seçim yenilemede korunur. Tablo içi kaydırma; altta seçili dosya ve desteklenen dinle/sesi kes. Dar ekranda “Kayıt ayrıntısı” paneli. |
| Harita | Mevcut çevrimdışı paket okuyucusu ve tek son geçerli nokta korunur. Büyük harita, kapatılabilir bilgi kartı, paket/yaş/koordinat görünür. Mesaj zamanı ile PC alma zamanı ayrı. Geçersiz güncelleme eski noktayı bozmaz; yaşı büyür. |
| Günlük | DMR/TETRA çözücü metni; saat, kanal/protokol, kategori, orijinal satır. Son oturumlarda en fazla 1.000 satır. Metin filtresi **yeni gelen satırlara** uygulanır; geçmişi silmez/yeniden taramaz. GPS/SDS etiketi koordinat doğrulaması değildir. |
| Spektrum | Windows yükseltilmiş süreç kontrolü. Sol: tepe eşiği, üst seviye, dinamik aralık; sağ: 1–20× zoom, merkez, görsel işaretçi. FFT/ortalama/gösterim, tepe listesi/tut/reset, kilit, görünür bant ve 250 kHz hazırlığı. Gerçek alıcı kazancı, Tuner AGC ve PPM mevcut kaynak kontrolüne bağlanır. |
| Kaynaklar | Alıcı ayarları / SDR cihazları / Hytera Ethernet. USB indeks/ürün/tuner/seri ve anlık envanter. Meşgul/yok ayrımı. Kaynağın hangi işi yürüttüğü görünür. |
| FM RADIO | Üstte açılıp gizlenir. 88,5–108 MHz, 100 kHz, WFM mono; arşiv yok. **Gizle sesi sürdürür; Kapat FM işini durdurur.** |
| Hytera | HR659 çevrimdışı ayar formu. IP boş hazırlanabilir; portlar doğrulanmamış örnek. Kaydetmek bağlantı/voice alımı değildir. IP ses sürücüsü tamamlanmış gibi görünmez. |

## Değişmeyecek sözleşmeler

- Analog ID / grup / slot `NULL`. DMR simplex örneğinde yalnız çözücü kanalı varsa `1 (çözücü)`; fiziksel TDMA slotu uydurulmaz. Özel hedef ID’si TG değildir. Alias sistem/müşteri kapsamında kalır.
- DMR CC 0–15; TETRA CC 0–63; APCO25 NAC 0–4095 ondalık; NXDN RAN 0–63. Boş filtre “tümü”. NFM CSQ/CTCSS/DCS/ters DCS; 6,25/12,5/25 kHz aralık, RF filtre genişliği ve ayar adımı ayrı.
- **90 sn bölüm / 2 sn kayıt arası** korunur. Doğal çağrı bitişinde ek 2 sn bekleme yok. TETRA slot tamponları bağımsızdır. DMR/APCO25/NXDN dosyası çağrı sonunda teslim edilir; bölümler o zaman arşive girer. UI 90 sn’de canlı arşiv teslimi vaat etmez.
- `.wav.radia`: tamamlanan dosya Windows kullanıcısına bağlı DPAPI ile korunur; arşiv sesi aynı Windows hesabındaki yönetici süreçte RAM içinde çözülür. DMR dinleme +6 dB/yumuşak sınırlama mevcut RAM yolunda korunur; düz geçici dinleme dosyası oluşturulmaz.
- DPAPI uygulama adına kilitli değildir. “Yalnız Radia açabilir / kırılamaz” yazma. Aktif `.wav.part`, çözücü WAV’ı ve kalıntılar düz ses içerebilir. Günlük ve konum JSON’u ses korumasına dahil değildir. Anahtar/hesap hatasını dosya yokmuş gibi gösterme; kurtarılabilir veriyi silme.
- Tek seçili fiziksel USB: **kanal alımı VEYA FM RADIO VEYA spektrum**. Geçişte mevcut iş ve açık kayıtlar güvenle sonlandırılıp cihaz bırakılmadan yeni iş başlamaz. İstek gönderildi diye UI başarılı duruma geçmez; onaylanmış backend sonucu beklenir. Başlatma hatası açıklanır.
- Sabit eşzamanlılık yalnız güvenli IQ penceresinde ve desteklenen yoldadır. Tarama bir tunerla sıralıdır; diğer kanalların seviyesi eski olarak etiketlenir. Dwell 1 sn, tüm taramanın 1 sn’de tamamlanması demek değildir. TETRA kontrol kanalı bekleme kuralları değiştirilmez.
- dBFS ≠ dBm. Tepe eşiği ≠ squelch ≠ RF kazancı ≠ ses seviyesi. FFT tepesinden protokol sınıflandırılmaz. Maksimum spektrum aralığı 24 MHz; FFT penceresi modülasyon değildir.
- Grafik zoom’u çözünürlüğü artırmaz. İşaretçi 6,25/12,5/25/200 kHz **görseldir**. Şelalede 3 px bir tam tarama; en yeni üstte. Ölçülmemiş geçmiş karanlık; yeniden çizim/mouse yeni satır üretmez. Ayar değişiminde eski tepe verisi temizlenir; gain/AGC/PPM yeni tam taramada uygulanır.
- Konum tek kabul edilen son noktadır; çoklu filo, rota veya sürekli GPS değildir. Yeni geçersiz mesaj eski konumu değiştirmez. Paket eksik karoda düşük katmana düşebilir, detay uydurmaz. Alım, harita/günlük gezinmesiyle başlamaz veya durmaz.

## Durum metinleri

| Gerçek olay | Görünüm |
|---|---|
| Alıcı kapalı | Alım durduruldu |
| Tuner başka kanalda | Sıra bekliyor · önceki ölçüm yaşı |
| RF eşik altında | Bekliyor |
| RF var, ses yok | Sinyal var; ses henüz çözülemedi |
| PCM dosyaya yazılıyor | Kırmızı nokta + Kaydediliyor |
| Maksimum süre arası | 2 saniyelik kayıt arası |
| DSD dosyası henüz teslim edilmedi | Çağrı tamamlanınca arşive aktarılacak |
| Dosya + koruma + arşiv başarıyla tamam | Kayıt tamamlandı · Korumalı |
| Normal süreç | Dinlemek için yönetici yetkisi gerekli |
| Çözme/okuma hatası | Kayıt çözülemedi + gerçek neden |
| Eski konum | Son geçerli konum + PC alınma yaşı |

Renk yanında metin zorunlu. Kayıt kırmızısı bütün ekranı alarm rengine dönüştürmez.

## Üç iş grubu

**A — Yalnız arayüz / mevcut bağlara uyarlama:** tema, kabuk, gezinme, kompakt logo, altı kart, koşullu protokol ayarları, arşiv tablo sütunları, kilit açıklaması, kaynak sekmeleri, FM paneli, harita/günlük yerleşimi, odak ve DPI, metinler. Mevcut backend olaylarına bağla; DSP değişikliği gerekçesi değildir.

**B — Ek veri olayı veya sunum uyarlayıcısı gerekebilir:** kaynak işi sahipliği ve kesin bırakma/başlatma sonucu; cihaz kayboldu/meşgul ayrımı; istenen/uygulanan kazanç; ölçüm yaşı; doğrulanmış protokol/slot türü; kayıt açık/ara/dosya bekliyor/finalizasyon/koruma/import/hata durumları; son kayıt özeti; konum yaşı ve paket/karoya düşüş durumu. Bunların bir kısmı yerel uygulamada var: önce mevcut kaynakta eşleştir, yalnız eksikleri ekle. Bunlar paket içindeki JS nesnelerinden üretilemez.

**C — Sonraki ürün aşaması:** waveform, pause/seek/hız, tarih aralığı, çoklu SDR, filo/rota/geofence, uygulama içi kullanıcı/roller, HR659 IP ses entegrasyonu, otomatik trunk takibi, kapsamlı geçici ses şifreleme/anahtar yedekleme. Bu teslimde çalışır kontrol veya satış iddiası yapılmaz.

## Ölçüler, erişilebilirlik ve Windows uyarlaması

Ayrıntı: [design-tokens.json](design-tokens.json). Segoe UI; 14 px gövde, 13 px kontroller, 12 px tablo/veri, 11–12 px ikincil metin; başlık 25–28 px; kanal 18 px. Rakamlar tabular, uygun yerde Consolas. Standart kontrol en az 36 px; yardımcı ikon 32 px, kontrastlı 3 px klavye odağı. Tab sırası gezinme → filtre/kontrol → içerik → ayrıntı; Enter/Space düğmeleri, Escape paneli kapatır. Arşivde yalnız mouse satır tıklamasına bağımlı kalma; Treeview seçimi ve Enter/dinle düğmesi erişilebilir olmalı.

1920×1080: üç sütun + sağ ayrıntı, sol alanın altında son kayıtlar. 1280×920 ve 1366×768: üç sütun; ayrıntı panel olarak açılır. 1180 mantıksal px altı iki sütun; yazıları sürekli küçültme. 980 px altı gezinme ikon şeridi, erişilebilir adlar korunur. Sayfa içi kaydırma, sabit başlık/alt durum; ayar paneli alt eylemleri erişilebilir. Arşiv tablosu kendi içinde kayar; küçük yükseklikte sayfa oynatıcıya kadar kaydırılabilir.

CSS px değerleri Tk font point değerlerine doğrudan kopyalanmaz. `grid` ağırlıkları, ttk/PanedWindow/Treeview, Canvas ve `after` üzerinden UI thread güncellemesi kullan. 100/125/150% **Windows/Tk** ölçek testi yerel PC’de yapılır; HTML viewport denemesi bunu tamamlamış sayılmaz.

## Marka / harita varlıkları

Paketin `assets/biem-logo.png`, `biem-amblem.png`, `telsiz-ikonu.webp` dosyaları yüklenen özgün dosyaların **birebir kopyalarıdır**. Yeniden çizme, renk değiştirme, oran bozma. Telsiz zoom ile 44–192 px aralığında ölçeklenir; alt orta noktası koordinata sabitlenir; üst sınıra sıkıştırmada gerçek noktaya çizgi çekilir. HTML’deki Natural Earth şematik altlık görsel referanstır; mevcut harita paketi okuyucusunun yerine yeni harita motoru ekleme. Karo arşivlerini Git’e koyma.

## Uygulama sırası ve kabul

1. Çalışan yerel kaynak durumunu koru; kabuk/tema/gezinmeyi mevcut ekranlara uygula.
2. Canlı kartlar ve seçili çağrı, kanal düzenleme kilidi, gain/AGC, tarama yaş bilgisi.
3. Arşiv + gerçek normal/yönetici ayrımı + RAM dinleme + hata durumları.
4. Harita, günlük, FM ve kaynak sekmeleri; tek USB iş sahipliği.
5. Spektrum kontrol yerleşimi, DPI, klavye ve kapanış kontrolleri.

Her adımda analog ve DMR akışı, TETRA mevcut ses yolu, 90/2 ve koruma davranışı korunmalı. Yerel uygulama değişikliğinde `Check-Radia.ps1` ve `python -m uv build` çalıştır. Testler gerçek SDR açmasın. Sonuçları **UI doğrulaması / donanımsız test / gerçek RF saha kabulü** diye ayrı yaz. Yüklenen brifin 71 test ve 0.2.0 build raporu bu tasarım oturumunda yeniden çalıştırılmış değildir.
