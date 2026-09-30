# Kullanıcı geliştirme notları — 2026-09-12

## FM RADIO

0.2.0 sürümünde uygulandı. Ana ekranda `FM RADIO` düğmesi üstte açılıp kapanan paneli gösterir. Kullanıcının istediği aralık 88,5–108 MHz, ayar adımı 100 kHz. Yayın radyosu için ayrı WFM mono demodülasyonu ve ses çıkışı kullanılır; telsiz NFM/DMR filtresi kullanılmaz. 100 kHz frekans adımıdır, WFM filtre genişliği değildir.

Ana telsiz alımı ve kayıtlar kesintiye uğramayacak. Aynı tek tuner ana kayıt için kullanılıyorsa FM RADIO o tuneri sessizce yeniden ayarlamayacak. Ekran açılabilir, fakat dinleme için boş/ikinci alıcı gerekir. Ana alım zaten kapalıysa aynı cihaz radyo için kullanılabilir. Ayrı ekran açmak ikinci fiziksel tuner sağlamaz.

## Uzak frekanslar ve çoklu cihaz

Kullanıcı 446,00625 MHz analog ve 427,500 MHz DMR kanallarını örnek verdi. Araları 18,50625 MHz; mevcut RTL-SDR ve 960 kS/s akışında birlikte kapsanamazlar. Yakın kanallar tek I/Q penceresine sığarsa aynı cihazdan NFM/DMR kanalları birlikte çözülebilir; cihaz/CPU performansı ayrıca doğrulanmalıdır.

Tarama modu eklendi: etkin kanallar sırayla alınır; her kanalın Squelch / dBFS eşiği aşılınca kanalda kalınır. Kesintisiz eşik altı bekleme süresi dolunca sıradaki kanala geçilir. Kanalı dinleme ve eşik altı bekleme süreleri 0,3–10 saniye arasında ayarlanır. Varsayılan ikisi de 1 saniyedir. Sinyal eşikte veya üstündeyken zorunlu kanal değiştirme yoktur; sürekli taşıyıcı taramayı durdurabilir. dBFS kalibre edilmiş dBm değildir.

Başka kanaldaki çağrı tarama sırasında görülemez; çağrı başı, kısa çağrı veya eşzamanlı konuşma kaybı mümkündür. İlk uygulama her kanal geçişinde kaynak bağlantısını ve ilgili demodülatörü yeniden açar; kayıtları kapatır, 250 ms başlangıç örneğini atar. DMR backend başlangıç/kapanış süresi de tarama turuna eklenir. Bekleme alanları toplam tur süresi garantisi vermez. Yakın kanallarda kesintisiz eşzamanlı alım için Sabit modu kullanılabilir.

Kesintisiz iki uzak frekans için iki bağımsız alıcı yolu gerekir. Çoklu USB cihaz seçimi, cihazları seri numarasıyla eşleme ve her alıcı için ayrı merkez frekans/kanal grubu sonraki geliştirme işidir; mevcut sürümde aynı anda iki USB alıcı yönetimi yoktur. Ethernet I/Q kaynağı da tek tunerin bant sınırını ortadan kaldırmaz.

### Sunum için Gelen Mesajlar — 12 Eylül 2026
Kullanıcının açık isteğiyle ilk çalışan sürüme yalnız Gelen Mesajlar sekmesi aktarıldı. Kanal/ID/grup/hedef/tarih ve metin araması; gerçek dijital günlüklerden konum metni ve açıkça etiketli ham veri olayları. Genel SMS/SDS çözücüsü eklenmedi. Günlük okuma yalnız sekme açıkken yapılır. RF/DSP/alım, kanal ayarları ve kayıt arşivi değiştirilmedi. Önceki app.py: data/backups/before-inbox-20260912-222152/app.py. Yeni arayüz V2 kullanılmaz.

Doğrulama: 76 donanımsız test, Ruff, ty, basedpyright ve paket üretimi geçti. İlk sürüm kendi klasöründen başlatıldı; otomatik alım başlatılmadı.

### İlk sürüm görünüm düzenlemesi
ChatGPT Operasyon tasarımına göre kompakt logo/başlık, lacivert sol gezinme, beyaz okunur kanal kartları, açılır mevcut kanal ayarları, gerçek seviye/durum/metin değişkenleri ve arşiv düğme yerleşimi uygulandı. Yeni veri/model veya V2 çalışma klasörü kullanılmaz. presentation.py yalnız mevcut widgetları düzenler. Arayüz bağlantısı app.py içinde; çalışan alım, çözümleme, kayıt ve harita modülleri değişmedi. Kanal ayarlarını açmak ayarı kaydetmez; mevcut Kanalları kaydet düğmesi kullanılır. FM gizleme/durdurma ayrımı korunur. Kanal adları mevcut ayarlardan gelir; Test sözcüğü varsa kullanıcı tanımıdır. Yedek: data/backups/before-presentation-20260912-222503/app.py.


### Tarama kuralları — 12 Eylül 2026
Kayıt 90 sn / 2 sn ara değişmedi. TETRA taramada çözülen ses yoksa en fazla 20 sn; doğrulanmış kontrol kanalı için mevcut 2 sn çıkış korunur. Ses çözülüyorsa taşıyıcı zaman aşımı uygulanmaz.
DMR tarama modunda kayıtlı CC filtresini değiştirmeden geçici alıcı kopyasında otomatik CC 0–15 kullanılır. Güçlü RF tek başına kilitlemez. Taze (0,8 sn) DMR senkronu ve eşik üstü sinyal bulunduğunda CC kilitlenir, arşiv içe aktarımı o CC ile filtrelenir. Senkron/CC/eşik kaybında ayarlı release süresi sonunda sonraki frekansa geçilir. İlk DMR araması asenkron çözücü için en az 2 sn, veya daha büyük kullanıcı dwell süresi bekler. Sabit moddaki elle CC filtresi değişmez. Canlı RF kabulü bekliyor. Yedek: data/backups/before-scan-rules-20260912.

