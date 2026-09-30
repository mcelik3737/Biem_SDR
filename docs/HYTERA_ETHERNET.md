# Hytera Ethernet hazırlığı

Hedef cihaz: kullanıcının belirttiği HR659 UHF. “2.5” bilgisi firmware sürümü
olarak ön doldurulmuştur; cihaz üzerinde doğrulanmalıdır.

Hytera Ethernet sekmesi röle/PC IPv4 adreslerini ve iki slot için ayrı kontrol/ses
UDP portlarını `data/hytera.json` dosyasında saklar. IP alanları boş bırakılabilir.
Portlar HytBridge örneğindeki 30009/30010 (kontrol), 30012/30014 (ses) değerleridir;
HR659 için doğrulanmış değerler değildir. Bu sekme yalnızca çevrimdışı ayar hazırlığıdır.
Kaydetme ağ bağlantısı, otomatik bağlantı veya RF gönderimi başlatmaz.

Yerel `D:/Projects/HytBridge-master` incelemesi: IP Dispatch G.711 μ-law ses ve
çağrı metadata örneği bulunuyor; IPSC desteği yok. Örnek firmware A8.05.07.001,
lisans GPLv3. Mevcut uygulamaya bu projeden kod kopyalanmadı.

Sonraki aşama: HR659 IP Dispatch uyumluluğu ve gerçek portları doğrulama;
alım için gerekli oturum/ACK/keepalive işlemleri; iki slotun bağımsız ses akışı;
paket sıralama/kayıp yönetimi; çağrı sınırları ile ID/grup/ses eşleştirme ve arşiv.
Bağlantı sürücüsü ve canlı ses alımı henüz uygulanmadı.

Doğrulama: donanım kullanmadan ayar kaydetme/yeniden yükleme, geçersiz IPv4 ve
çakışan port reddi, hatalı girişte önceki dosyanın korunması; socket açma testi
yasaklanarak çevrimdışı çalışma kontrol edilir. Röle bağlı olmadığı için donanım
ve ses testi yapılmadı.
