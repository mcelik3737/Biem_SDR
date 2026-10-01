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
