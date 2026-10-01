# 2026-10-01 — Sunucu ve istemci kararı

## Kullanıcının isteği

Ofiste sürekli çalışan bir sunucu programı ve ona bağlanan istemci arayüzleri olacak. Ürün/sunucu adı **BIEM-ICC-SERVER**. Yönetici şifreyle giriş yapacak; hangi kullanıcıların girebileceğini ve yetkilerini kutulardan belirleyecek. Örneğin bir kullanıcı spektruma, başka bir kullanıcı kayıt ekranına erişemeyecek. İstemciler verileri sunucudan alacak.

## Kullanıcının netleştirdiği tercih

İstemci bağlantısı: **“Tarayıcıdan bağlansın (önerilen)”**.

## Uygulama kararları

- Ayrı çalışma klasörü ve dal; önceki alıcı/çözücü kodu korunur.
- İlk yönetici şifresi kullanıcı tarafından yerel kurulumda belirlenir. Şifre sohbetten istenmez, hazır şifre verilmez.
- Sayfa, işlem ve kanal kapsamı sunucuda uygulanır. Menü gizlemek tek başına yetkilendirme değildir.
- Arşivi görme ve sesi dinleme ayrı izinlerdir. Ekranların yanında belirli kanalları seçme veya tüm kanallara erişme seçeneği vardır.
- Kullanıcı hesabı kapatıldığında/izinleri değiştiğinde oturumları iptal edilir; son yönetici korunur.
- Tarayıcıdan çıkış alım ve kaydı durdurmaz. Sunucu çalışması mevcut SDR/Hytera motorlarını kullanır.
- Spektrum ve alımı yönetme tüm kaynak üzerinde etkilidir; panelde açıkça belirtilir.
- Gerçek kullanıcı parolaları, oturumlar, loglar ve RF kayıtları Git'e girmez.

Bu not tarihli gereksinim kaydıdır. Kurulum, sınırlar ve test kanıtları için `docs/SERVER_CLIENT.md` esas alınır. Tam geçmiş konuşmanın bire bir dışa aktarımı olduğu iddia edilmez.

## Aynı gün — Yönetici kanal ayarları / masaüstü USB bildirimi

Kullanıcı: “kanal ayarları admin kullanıcıda çıkmıyor. masaüstü yazılımıda sdr ı görmüyor. bir şeyler ters gitti sanırım”

- İlk web sürümünde olmayan yönetici kanal editörü tamamlandı; kanal kartında Ayarlar ve solda Alıcı / kanal ayarları bulunur.
- Frekans, mod, CC, analog ton, kayıt eşiği, yakın sinyal kilidi; genel USB/rtl_tcp, kazanç, PPM ve tarama ayarları mevcut masaüstü biçiminde kaydedilir.
- Standart kullanıcılar bu ayarları göremez/değiştiremez. Alım veya spektrum çalışırken ayar dosyası değiştirilmez. Önceki dosya yedeklenir ve eski tarayıcı oturumunun yeni ayarları ezmesi engellenir.
- Ayrı klasöre kopyalanan masaüstü başlatıcıları sürücü/veri için aynı mevcut proje köküne yönlendirildi. Eski projenin kaynakları ve sürücü kurulumu korunur.
- Alım kapalı durumu kartta ayrıca belirtilir; USB kopmasıyla aynı metin kullanılmaz.
- Kısa gerçek USB testinde cihaz listelendi ve 327.680 I/Q örneği okundu. Ses/kayıt veya uzun süreli USB kararlılığı testi olduğu iddia edilmez.
- Ayrı temsili tarayıcı verileriyle yönetici ayar kaydı ve kullanıcı erişim sınırı doğrulandı; tüm 238 test ve paket derlemesi geçti. Gerçek kullanıcı parolalarına/ayarlarına müdahale edilmedi.
