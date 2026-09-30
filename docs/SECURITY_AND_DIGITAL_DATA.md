# Kayıt koruması ve dijital veri günlüğü — 12 Eylül 2026

## Uygulanan davranış

- Analog kartında CSQ / CTCSS / DCS / DCS-I kullanılabilir; CSQ ton değeri gerektirmez. Dijital modlarda analog ton alanları pasiftir.
- DMR CC alanı boş bırakılınca filtre uygulanmaz. Gelen çözücü senkronundan CC, çağrıdan kaynak ID ve hedef alınır. Grup / özel hedef yalnız çözücü bunu açıkça bildirdiğinde etiketlenir. Frekansı yazmak tek başına metadata sağlamaz.
- MS/DM simplex çıktısındaki slot, doğrulanmış fiziksel TDMA slotu yerine **Çözücü slotu** olarak etiketlenir. Arşivdeki doğrulanmış slot ve çözücü slotu ayrımı korunur.
- Kayıt dinleme işlemi Windows `IsUserAnAdmin` kontrolünden geçer. Normal yetkiyle çalışan Radia arşiv sesini açmaz. Yönetici başlatıcısı: `Start-Radia-Admin.cmd`.
- Masaüstü uygulamasının tamamlanan analog, DMR ve TETRA kayıtları Windows DPAPI ile şifrelenir. Dosya adı mevcut tarih / ID / grup / süre düzenini korur; uzantı `.wav.radia` olur. Standart medya oynatıcısı bu dosyayı WAV olarak açamaz.
- Oynatma çözümü RAM içindedir. Önceki `dmr-playback.wav` dinleme kopyası artık oluşturulmaz; DMR dinleme kazancı +6 dB ve yumuşak sınırlama korunur.
- Kaynak dosya kaldırılmadan önce şifreli dosya diske yazılır ve geri çözülerek birebir doğrulanır. Mevcut SQLite kaydı yeni yola geçirilir. Yazma / anahtar hatasında kaynak korunur.
- 12 Eylül geçişinde mevcut 102 WAV dosyası (arşiv, çözücü, tanılama kopyaları dahil) şifrelendi, 102 SHA-256 karşılaştırması eşleşti. Geçiş sonunda `data` altında sıfır `.wav` kaldı. Manifest ve eski SQLite: `data/backups/protection-20260912/`. Eski DB yedeğinin WAV yolları yeni şifreli dosya adlarına uyarlanmalıdır.

## Güvenlik sınırları — tasarımda gizlenmemeli

Bu bir süreç bağlama veya bağımsız yönetici anahtar servisi değildir. DPAPI anahtarı Windows kullanıcısına bağlıdır; aynı kullanıcı bağlamındaki başka bir yazılım teorik olarak çözebilir. Yerel yönetici veya sistem sahibi için “yalnız Radia dinleyebilir” garantisi yoktur. Yönetici kontrolü uygulamanın dinleme akışına uygulanır; Windows dosya erişimini yöneten ayrı hizmet / ACL düzeni bu sürümde yoktur.

Normal ve yükseltilmiş Radia **aynı Windows hesabıyla** açılmalıdır. Başka yönetici hesabının parolasını girerek başlatılan süreç, mevcut kullanıcının şifreli kayıtlarını çözemeyebilir. Windows profilini / DPAPI anahtarlarını kaybetmek kayıtları erişilemez hale getirebilir; doğrulanmış bir profil ve anahtar yedekleme planı gereklidir. `.radia` dosyaları tek başına taşınabilir dışa aktarma değildir.

Devam eden analog `.wav.part` ve üçüncü taraf DSD-FME'nin açık WAV dosyaları tamamlanana kadar geçici düz ses içerebilir. DSD-FME kapanışında kalan WAV'lar da şifrelenir. Çökme, disk dolması veya şifreleme hatasında kurtarılabilir dosyalar tutulur; bu durumda tüm diskin şifreli olduğu iddia edilmez. Silinen eski düz dosyalar için güvenli disk silme yapılmadı. Daha güçlü koruma için ayrı anahtar hizmeti, Windows hesap/ACL tasarımı ve şifreli geçici depolama sonraki güvenlik aşamasıdır.

Referans: https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata

## Dijital veri

Yeni **Dijital Veri Günlüğü** sekmesi son oturumların çıktısını gösterir; tüm satırlar veya GPS / SDS / veri metinleri filtrelenebilir. Ekran 1000 satırla sınırlıdır. Filtre sonraki gelen satırlara uygulanır; dosyalar değişmez.

DMR oturumu: `data/dmr-sessions/<oturum>/`

- `decoder.log`: DSD-FME ham konsol çıktısı, `-Z` ile payload ayrıntıları.
- `digital.jsonl`: host UTC gözlem zamanı, kanal, frekans, protokol, kategori ve özgün çözücü satırı. Zaman damgası RF paketi içindeki saat değildir.
- `lrrp.tsv`: `-L` seçeneğiyle çözücü geçerli LRRP çıktısı üretirse oluşur.
- `events.log`: çağrı olayları.

TETRA: `data/tetra-sessions/<oturum>/events.jsonl`. UTC gözlem zamanı, kanal/frekans, senkron, slot, hata bilgileri ve köprü tarafından açığa çıkarılan ham alanlar saklanır. PCM bu metin günlüğüne yazılmaz. Orijinal parserda SDS / konum alanları vardır, ancak köprü tüm SDS metinlerini / bitlerini açığa çıkarmaz. Bu sürüm tam bir SDS uygulaması değildir.

`GPS`, `LRRP`, `SDS` veya `PDU` sözcüğünün bulunması yalnız metin kategorisidir; koordinat doğruluğu, hedef eşleştirmesi veya başarılı GPS kabul testi anlamına gelmez. Ses dışı veri gelmesi mümkündür; alınan paket ve çözücü desteği canlı testte değerlendirilir. Günlükler düz metindir; içerdikleri ID / konum verisinin erişim ve saklama politikası ayrıca ele alınmalıdır.

## Doğrulama ve bekleyen canlı test

- 63 donanımsız test; Ruff, ty, basedpyright ve paket derleme başarılı.
- DPAPI geri çözme / bozulma reddi, şifreleme hatasında kaynak koruma, yönetici dışı dinleme engeli, moda göre alanlar, artımlı log okuma ve eski CC bilgisinin yeni senkrona taşınmaması test edildi.
- Gerçek USB alımı 427.500 MHz'te açıldı; DSD-FME TCP bağlantısı ve payload / LRRP seçenekleri günlükten doğrulandı. CC filtresi boş, PPM +15. Kullanıcı ID 3737, slot 1 bildirdi; bunlar çözülen bilgi olarak önceden atanmadı.
- GPS mesajı ve yeni otomatik CC / ID / grup RF sonucu kullanıcı gönderimini bekliyor. Geçici test ayarları kullanıldı; önceki kanal / alıcı JSON dosyaları başlangıç sonrasında geri kondu.
