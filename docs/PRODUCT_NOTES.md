# Kullanıcı geliştirme notları — 2026-09-12

## FM RADIO

İstek kaydedildi; henüz uygulanmadı. Ana ekranda `FM RADIO` düğmesi ayrı sayfa/pencere açacak. Kullanıcının istediği aralık 88,5–108 MHz, ayar adımı 100 kHz. Yayın radyosu için ayrı WFM demodülasyonu ve ses çıkışı kullanılacak; telsiz NFM/DMR filtresi kullanılmayacak. 100 kHz frekans adımıdır, WFM filtre genişliği değildir.

Ana telsiz alımı ve kayıtlar kesintiye uğramayacak. Aynı tek tuner ana kayıt için kullanılıyorsa FM RADIO o tuneri sessizce yeniden ayarlamayacak. Ekran açılabilir, fakat dinleme için boş/ikinci alıcı gerekir. Ana alım zaten kapalıysa aynı cihaz radyo için kullanılabilir. Ayrı ekran açmak ikinci fiziksel tuner sağlamaz.

## Uzak frekanslar ve çoklu cihaz

Kullanıcı 446,00625 MHz analog ve 427,500 MHz DMR kanallarını örnek verdi. Araları 18,50625 MHz; mevcut RTL-SDR ve 960 kS/s akışında birlikte kapsanamazlar. Yakın kanallar tek I/Q penceresine sığarsa aynı cihazdan NFM/DMR kanalları birlikte çözülebilir; cihaz/CPU performansı ayrıca doğrulanmalıdır.

Tarama modu eklendi: etkin kanallar sırayla alınır; her kanalın Squelch / dBFS eşiği aşılınca kanalda kalınır. Kesintisiz eşik altı bekleme süresi dolunca sıradaki kanala geçilir. Kanalı dinleme ve eşik altı bekleme süreleri 0,3–10 saniye arasında ayarlanır. Varsayılan ikisi de 1 saniyedir. Sinyal eşikte veya üstündeyken zorunlu kanal değiştirme yoktur; sürekli taşıyıcı taramayı durdurabilir. dBFS kalibre edilmiş dBm değildir.

Başka kanaldaki çağrı tarama sırasında görülemez; çağrı başı, kısa çağrı veya eşzamanlı konuşma kaybı mümkündür. İlk uygulama her kanal geçişinde kaynak bağlantısını ve ilgili demodülatörü yeniden açar; kayıtları kapatır, 250 ms başlangıç örneğini atar. DMR backend başlangıç/kapanış süresi de tarama turuna eklenir. Bekleme alanları toplam tur süresi garantisi vermez. Yakın kanallarda kesintisiz eşzamanlı alım için Sabit modu kullanılabilir.

Kesintisiz iki uzak frekans için iki bağımsız alıcı yolu gerekir. Çoklu USB cihaz seçimi, cihazları seri numarasıyla eşleme ve her alıcı için ayrı merkez frekans/kanal grubu sonraki geliştirme işidir; mevcut sürümde aynı anda iki USB alıcı yönetimi yoktur. Ethernet I/Q kaynağı da tek tunerin bant sınırını ortadan kaldırmaz.
