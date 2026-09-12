# Codex uygulama yönlendirmesi — BIEM Radia

## İstenen sonuç

**01 Operasyon** tasarımını çalışan Windows uygulamasına uygula. Operatör, frekans ayarı yapmadan kimin konuştuğunu, hangi kanalda olduğunu, sesin kayda girip girmediğini ve geçmiş kaydı nasıl açacağını anlayabilsin. 02 Gece konsolu ve 03 Arşiv odaklı aynı veri/olay modelinin alternatif düzenleridir; üç ayrı uygulama değildir.

Bu görev görsel tasarım ve günlük kullanım düzenidir. Mevcut RF/DMR/analog alım, kanal yönetimi, çağrı kapanması, WAV yazımı, SQLite ve cihaz erişimi korunur. Ekranlara temsili veriler veya hazır “başarılı” durumlar taşınmaz.

## Önce doğru çalışan kaynak

**Önce yerel proje notunu oku:** Kullanıcı bu çalışma sırasında `D:\Projects\Biem\_SDR\BIEM_RADIA_PROJE_NOTLARI_VE_ARAYUZ_BRIFI.md` dosyasını ayrıca paylaştı. Dosyanın içeriği bu tasarım oturumundan erişilebilir değildi; kontrol edilen Git dallarında bulunamadı. PC'deki Codex, uygulamaya başlamadan bu dosyayı okuyup mevcut kapsam, marka kararları ve teknik sınırlamalarla tasarım paketini eşleştirmeli. Bu tasarım paketi, okunmamış yerel notların yerine geçmez.

- Kullanıcının proje yolu: `D:\Projects\Biem\_SDR`.
- Referans incelemede `main@e27f0a9` Python/Tk analog sürümüdür.
- `codex/dmr-receiver@4e30773` Python/Tk + DMR/sıralı tarama yolunu içerir.
- Kullanıcının gönderdiği son ekranlarda ayrıca logo, canlı kartlar, Hytera Ethernet, SDR cihazları ve spektrum var. Bu görüntülerin tamamı erişilen Git kaynaklarıyla aynı sürüm olarak doğrulanmadı.
- **PC'de çalışan dalı ve kaydedilmemiş değişiklikleri esas al.** Bunları yedeklenmiş/izlenebilir kaynak sürümüne getir. Tasarım dalının eski `src` dosyalarını yerel çalışan sürümün üzerine kopyalama.
- Bu paketin `docs/ui/` içeriği tasarım girdisidir. `Biem_SDR_V1` C++/Qt deposu ayrı hattır; sırf görsel değişiklik için iki hattı birleştirme.

## Ekran iskeleti

### Ürün başlığı ve gezinme

Üst başlık yaklaşık 70 px. Solda **orijinal BIEM logosu** 134 × 42 px içinde, oranı korunarak; yanında RADIA. Logoyu yeniden çizme, biçimini veya renklerini değiştirme. Logo alanını uygulama penceresinin yüksekliğine göre büyütme.

Sağda kaynak durumu, yerel saat ve **Alımı başlat / Alımı durdur**. Buradaki eylem kayıt motorunun mevcut yaşam döngüsünü çağırır. “Ses kapat” ile aynı düğme olmaz.

Sol gezinme 180–218 px. Sıra:

1. Canlı izleme
2. Kayıt arşivi
3. Kimlik rehberi
4. Sistem altında Spektrum
5. Kaynaklar ve ayarlar

Mevcut **Hytera Ethernet**, **SDR Cihazları**, **Alıcı/Gelişmiş Ayarlar** ekranları Kaynaklar ve ayarlar altında kaynak türüne göre erişilir. **BİEM** hakkında/iletişim bilgisi ayrı yardım alanına taşınır. FM radyo destekleniyorsa yardımcı kaynak/araç olarak erişilir; ana kayıt kontrolüyle görsel rekabete girmez.

Sol menüde mevcut müşteri/sistem bağlamı görünür. Oturum ve yetki altyapısı yoksa sahte giriş/rol/kurumsal çoklu kullanıcı iddiası ekleme.

### Canlı izleme

İlk satır: sayfa adı, kısa açıklama, kanal düzeni ve kanal ayarları.

İkinci satır: fiziksel kaynak, bağlantı türü, alım biçimi ve gerçek aktif kayıt sayısı. Sabit modda bant içi eşzamanlılık; taramada sırayla alım açıkça yazılmalı.

Ana alan: kanal kartları + seçili çağrı paneli. Kartlar isme/konuşma durumuna göre her güncellemede yer değiştirmesin. Sabit sıralama ve seçili kanal korunmalı. Arama ve yalnız aktif filtresi görünüm filtresidir; alıcı aboneliğini veya kaydı değiştirmez.

Kart bilgi sırası:

1. Kanal numarası, mod rozeti, metinli alım durumu.
2. **Kanal/grup adı.**
3. Daha küçük frekans.
4. **Konuşan adı**, altında ID / TG / fiziksel slot; yanında çağrı süresi.
5. Sinyal seviyesi / dBFS.
6. Ayrı **Kaydediliyor** göstergesi; küçük yerel dinleme sesi ve ayar düğmeleri.

DMR çift slot destekleniyorsa bir taşıyıcı altında iki bağımsız slot satırı veya ayrı slot kartı göster. Fiziksel kanal kartı ile mantıksal çağrı kartı modelde ayrılmalı. Aynı frekanstaki eşzamanlı slotlar tek çağrı süresinde veya tek WAV'da birleştirilmemeli.

Varsayılan 2 veya 3 sütun. Kart yaklaşık 180–205 px yüksekliğinde; genişlik 260 px altına düşerken sütun azalt. 1920 × 1080'de 6 kart ve son kayıtlar birlikte görünür olsun. 1366 × 768'de sayfa içine sığmayan içerik kayabilsin; uygulama penceresi dışına taşmasın.

Seçili çağrı panelinde telsiz adı, gerçek ID, destination/group ID, çağrı türü, doğrulanmış slot, color code, kaynak, kayıt süresi. Kimlik bilinmiyorsa `—` ve gerekiyorsa “Kimlik çözülemedi”; önceki çağrıdan alan doldurma.

### Kayıt arşivi

Filtreler: serbest metin (başlık / kanal / isim / ID), yerel tarih veya tarih aralığı, grup ve slot. Mevcut arama sözleşmesi önce korunur; yeni filtre API'si gerekiyorsa ayrıca eklenir ve doğrulanır.

Tablo: tarih/saat, kanal, konuşan adı ve ID, grup, slot, süre, kayıt durumu, dinle. Teknik ayrıntılar sağ paneldedir. Sıralama en yeni önce; kullanıcı sıralaması ve seçimi yenilemede kaybolmaz.

Kaydı tek tıkla seç; oynat düğmesi veya çift tıkla dinlet. Seçili kaydın dalga biçimi, ilerleme çubuğu ve süre bilgisi görünür. Dalga biçimi **gerçek dosyadan** üretilir; örnek çizgiler üretime taşınmaz. Dosya henüz tamamlanmamış, eksik veya okunamıyorsa ilgili açıklama ve hata durumu görünür. Metadata olayı tek başına dinlenebilir kayıt olarak sunulmaz.

Hız değiştirme, dalga biçimi, dışa aktarma ve yer işareti mevcut motor tarafından desteklenmiyorsa uygulamada tamamlanmış gibi gösterme. İlk görsel teslimde gerçek oynatma kontrolleri çalışsın; ek işlevler ayrı iş olarak açıkça belirtilebilir.

Ürün PC'nin yerel saat dilimini kullanır. Depoda UTC tutulması korunur. Prototipteki sabit tarih ve UTC+03:00 senaryosu üretime kopyalanmaz.

### Kanal ve kaynak ayarları

Kanal ayarı sağ panelde açılır; canlı sayfa frekans giriş kutularıyla dolmaz. “Uygula” ve “Vazgeç” açık eylemler olsun. Geçersiz değer kullanıcı alanında açıklansın, önceki çalışan konfigürasyon kaybolmasın.

| Mod / kaynak | Gösterilecek alanlar |
|---|---|
| Analog NFM | Frekans, kanal aralığı, RF filtresi, squelch, gerçekten desteklenen CTCSS/DCS |
| DMR | Frekans, color code, doğrulanmış slot filtresi, sistem/müşteri kapsamı, kayıt politikası |
| TETRA | Gerçek destek seviyesi ve doğrulama durumu; desteklenmeyen işlevler çalışır gibi görünmez |
| USB SDR | Cihaz, örnek hızı, tuner kazancı/AGC, PPM; tuner'a özgü geçerli değerler |
| rtl_tcp | Sunucu/port ve bağlantı durumu; Hytera protokolü olarak adlandırılmaz |
| Hytera Ethernet | Desteklenen gerçek entegrasyon türü, bağlantı, ses ve metadata durumları ayrı |

Alım sırasında değişebilen ve durdurma gerektiren parametreler backend sözleşmesine göre ayrılır. Prototipteki genel durdurma örneği, çalışma sırasında güvenle uygulanabildiği doğrulanmış USB kazancını gereksiz yere durdurma zorunluluğuna dönüştürmez.

Kaynağın birden fazla kanal tarafından paylaşıldığı anlaşılır olmalı. Kaynak ayarı tek kartın ayarıymış gibi sunulmaz.

### Spektrum

Spektrum günlük çağrı kartlarının yerine varsayılan açılış ekranı olmaz. Frekans aralığı, ölçüm/kayıt durumu ve dBFS ölçeği açık; FFT penceresi gibi teknik seçenekler gelişmiş ayara gider.

Aynı cihazda ölçüm ile kayıt çakışıyorsa: “Aktif kayıtlar tamamlanacak; ölçüm sırasında yeni çağrı kaydı alınmayacak.” Onaydan sonra önce backend'in kayıtları güvenle kapattığı ve cihazı bıraktığı doğrulanır, sonra ölçüm açılır. UI düğmesine basılmış olması yeterli değildir. Hata olursa uygun kayıt/cihaz durumu korunur ve gösterilir.

Sıralı geniş bant taramasındaki şelale, kesintisiz tek bant FFT akışı gibi sunulmaz. Eksik tarama/satır bilgisi görülebilmeli. Kalibrasyon yoksa dBm yazılmaz.

## Durum sözleşmesi

| Durum | Görünüm | Ne ifade eder |
|---|---|---|
| Devre dışı | Soluk gri + metin | Kanal yapılandırmada kapalı |
| Beklemede | Gri + metin | Kaynak açık, bu kanalda aktif çağrı yok |
| Sıra bekliyor | Gri + tarama bilgisi | Tuner şu anda başka kanalda |
| Sinyal var / senkron yok | Amber + açıklama | RF var; sesin çözülmesi doğrulanmadı |
| Alınıyor | Mavi işaret + durum | İlgili alım/çözme olayı doğrulandı |
| Kaydediliyor | Küçük kırmızı kayıt noktası + metin | O çağrının ses dosyasına gerçekten PCM yazılıyor |
| Kaydedildi | Yeşil işaret + metin | Dosya tamamlandı ve arşive başarıyla işlendi |
| Metadata var / ses yok | Amber + metin | Olay var, dinlenebilir dosya yok |
| Bağlantı/kayıt hatası | Kırmızı + neden | Operatörün müdahalesi gerekiyor |
| Yerel ses kapalı | Üzeri çizili hoparlör | Monitör sesi kapalı; kayıt politikası değişmez |

Renk tek başına anlam taşımasın. Hata kırmızısı bütün karta yayılmasın; küçük kayıt noktası normal REC göstergesidir. Aynı anda farklı kanalları dinleme/miks önceliği backend destekliyorsa açık seçili kanal/slot kontrolü sun.

`decoder_slot` ile doğrulanmış fiziksel TDMA slotunu ayır. Mevcut DMR dalında bu ayrım için commit var; güzel görünmesi için birleşik tek `slot` alanına indirgeme. Simplex/DMO'da fiziksel slot güvenilir değilse `—`; çözücü kanalı ayrı teknik ayrıntıda.

## Yazı ve renk sistemi

- Windows'ta **Segoe UI**. Prototip CSS px değerleridir; Tk point boyutlarıyla birebir sayı kopyalama. DPI dönüşümünü dikkate al.
- Başlık 24–27 px; kanal adı 16–18 px; kişi 12–14 px; ana kontrol ve tablo 12–14 px hedeflenir. Örnek HTML'deki çok küçük ikincil etiketler Windows'ta okunurluk lehine büyütülebilir.
- Numerik alanlarda tabular rakamlar; ID/frekans için Consolas uygundur. Gövdeyi monospace yapma.
- BIEM bordo marka vurgusu, lacivert gezinme, açık nötr yüzey, semantik mavi/yeşil/amber/kırmızı.
- Kenarlar 1 px; köşe yarıçapı 6–9 px; aralıklar 4/8/12/16/24 px.
- Tüm yazı ve kontrol durumlarında kontrast/klavye odağı korunmalı. Hedef normal metinde en az 4,5:1; ikincil metni aşırı soluklaştırma.

## Mevcut Python/Tk yoluna uygulama

Mevcut kaynak doğrulandığında arayüz sınıfını küçük görünüm bileşenlerine ayırmak yeterlidir. Tk kullanılmaya devam edilebilir; yeni toolkit zorunluluğu yok.

Önerilen sorumluluklar: tema/ölçüler; uygulama kabuğu; kanal kartı; seçili çağrı paneli; arşiv görünümü; ayar paneli. `Receiver`, `Archive` ve mevcut olay kuyruğu arayüzleri korunur. Alıcı iş parçacıkları Tk widget'larını doğrudan güncellemez. Yenileme, UI thread üzerinden; yüksek hızlı RF verisi UI'ya taşınmaz.

Tablolar mevcut `ttk.Treeview` ile; esnek bölmeler `PanedWindow`/grid ağırlıklarıyla; dalga biçimi/sinyal göstergesi gerektiğinde Canvas ile çizilebilir. Kaydırma alanları, seçili öğe ve klavye sırası bilinçli yönetilsin.

## Uygulama sırası

1. **Kabuk + tema:** logo, başlık, gezinme, ölçüler. Çalışan ekranları yeni kabuk içine taşı.
2. **Canlı görünüm:** salt okunur kartlar, seçili çağrı, ayrı kayıt ve monitör sesi durumları; ayar paneli.
3. **Arşiv:** filtre/tabloda bilgi sırası ve gerçek oynatma. Dalga biçimi ve inceleme düzeni destek durumuna göre.
4. **Kaynak/cihaz durumu:** hata, tarama, DMR metadata, spektrum kaynak paylaşımı.
5. **Gece teması ve DPI:** aynı bileşenlerin alternatif rengi; geniş kart düzeni.

Her adımda çalışan analog/DMR kayıt davranışını koru. Donanımdan gelen gerçek veriyle kabul ayrı aşamadır.

## Kabul kontrolü

- 1920 × 1080 ve 1366 × 768; %100 / %125 / %150 Windows ölçeklerinde düğmeler ve yazılar kesilmiyor.
- 6 kanal hızlı okunuyor; kritik durum ve kayda geçiş görünür; ayarlar canlı kartları kaplamıyor.
- Kanal araması/filtreleme alıcıyı veya kaydı değiştirmiyor.
- Monitör sesi kapatıldığında WAV yazımı sürüyor.
- Arşivde tarih, isim, ID, grup ve slot araması doğru sonuç veriyor; oynatma gerçek dosyayı kullanıyor.
- Analogda ID/TG/slot boş. Senkron kaybında eski çağrı kimliği yeni çağrıya taşınmıyor.
- Fiziksel slot doğrulanmadığında çözücü slotu yerine yazılmıyor.
- Kaynak kopması, disk dolması, eksik WAV ve çözücü hatası görünür; sahte “kaydedildi” yok.
- Spektrum geçişi gerçek kayıt kapanması/cihaz bırakılmasını bekliyor; kaydı sessizce kesmiyor.
- `Check-Radia.ps1` ve `python -m uv build` Windows uygulama değişikliği sonrası geçiyor.
- Sentetik/prototip doğrulaması, gerçek RF ve anlaşılır ses testi olarak raporlanmıyor.
