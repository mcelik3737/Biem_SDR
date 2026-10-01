# BIEM-ICC-SERVER / tarayıcı istemcisi

Tarih: 2026-10-01. Yeni kod ayrı `codex/server-client` dalında ve bu bilgisayarda `D:\Projects\Biem\ICC_Server` klasöründedir. Önceki çalışan `D:\Projects\Biem\_SDR` kaynakları değiştirilmez.

## Kullanım

1. Önce eski masaüstü uygulamasında alımı durdurun ve uygulamayı kapatın. SDR# aynı USB alıcıyı kullanmamalı. Eski uygulama ile sunucuyu aynı alıcı/arşiv üzerinde birlikte çalıştırmayın.
2. Yeni klasörde `Start-BIEM-ICC-SERVER.cmd` dosyasını açın. Başlatıcı bu bilgisayardaki eski projenin `data` ve `vendor` klasörlerini kullanır; kayıtları veya haritaları kopyalamaz/silmez. Başka kurulumda `Start-BIEM-ICC-SERVER.ps1 -Project 'D:\Biem'` ile veri kökünü açıkça seçin.
3. İlk çalıştırmada sunucunun kendi tarayıcısında **Yöneticiyi tanımlayın** ekranı açılır. Kullanıcı adını ve en az 12 karakterlik şifreyi kendiniz belirleyin. Hazır/default şifre yoktur. Tek kullanımlık kurulum anahtarı URL'nin sunucuya gönderilmeyen fragment bölümünde taşınır ve sayfa açılınca adres çubuğundan kaldırılır. Kurulum ekranını kaybettiyseniz, ilk hesap henüz oluşturulmamışken sunucuyu yeniden başlatın.
4. Yönetici hesabıyla **Kullanıcılar ve yetkiler** ekranına girin. Kullanıcı adı/şifre girin; hesabı etkin bırakın; ekranları ve görebileceği kanalları işaretleyin. **Kullanıcıyı oluştur** düğmesine basın.
5. Yönetici, canlı izleme kartındaki **⚙ Ayarlar** veya soldaki **Alıcı / kanal ayarları** üzerinden kanal frekansı/modu, CC, eşik, analog ton, yakın sinyal kilidi, USB seçimi, kazanç ve PPM ayarlarını düzenleyebilir. Kaydetmeden önce SDR alımı ve spektrum durmalı; dosya kapanışının bitmesi beklenmeli. **Cihazları yenile** ile alıcıyı seçip **Kaydet** düğmesine basın. Kanal değişiklikleri için **Tüm kanal ayarlarını kaydet** kullanılır. Ardından canlı izleme ekranındaki **Başlat**, bu ayarlarla alımı başlatır. **Röle izleme** içindeki başlat düğmesi mevcut Hytera profilini kullanır. Ses çözümü ve kayıtlar sunucuda yapılır. **Dinle** tarayıcıdan canlı ses verir; birden fazla çözücü ses akışı varsa akışı seçebilirsiniz. Fiziksel slot bilinmiyorsa tahmin edilmez.
6. **Sunucu başlangıcı** bölümünde SDR, Hytera ve SNMP için otomatik başlangıcı seçebilirsiniz. Bunlar sunucu uygulamasının bir sonraki açılışında uygulanır. Tarayıcıdan çıkış yapmak veya sekmeyi kapatmak alımı durdurmaz.

Yerel adres: `http://127.0.0.1:8765`. Bu adres diğer bilgisayarlardan erişilemez.

Sunucuyu kapatmak için konsolda `Ctrl+C` kullanın ve kapanışın bitmesini bekleyin. Birden fazla dijital kanalın son dosyalarını tamamlamak zaman alabilir. Sunucu, çözücüler kapanmadan veri klasörü kilidini bırakmaz. Görev Yöneticisi ile zorla sonlandırmayın. Sunucu konsolunu/Windows oturumunu kapatmak tarayıcı sekmesini kapatmakla aynı şey değildir.

## İki arayüz, tek veri kaynağı

- **Yönetici:** Tüm kanallar, ekranlar, alım kontrolü, kullanıcı/yetki yönetimi ve işlem günlüğü.
- **İstemci kullanıcı:** Yalnızca yönetici tarafından işaretlenen ekran ve kanallar. Boş kanal listesi hiçbir kanal demektir. “Tüm mevcut ve gelecekteki kanallar” ayrı bir seçimdir.

| Yetki | Sonuç |
| --- | --- |
| Canlı kanalları gör | İzinli kanalların RF/ses ve çözüm bilgileri |
| Canlı sesi dinle | İzinli kanalların çözülen sesini tarayıcıda dinleme |
| Kayıt arşivini gör | İzinli kanalların kayıt satırları ve ID/grup/slot/CC bilgileri |
| Kayıtları dinle | Arşiv görme yetkisine ek olarak sesin sunucudan alınması |
| Gelen mesajları gör | İzinli kanallardan mesajlar; çözülmemiş ham veri ayrıca etiketlenir |
| Harita ve konumları gör | Yerel çevrimdışı yol haritası ve izinli kanallardan son konum |
| Röle durumunu gör | Tüm rölenin SNMP ölçümleri ve güncel iki-slot RSSI sorgusu |
| Spektrumu gör | Tüm ölçüm bandının spektrumu; kanal filtresinden bağımsızdır |
| Spektrum ölçümünü yönet | Ölçüm başlatma/durdurma; SDR canlı alımıyla aynı anda açılmaz |
| Alımı başlat / durdur | Tüm SDR veya Hytera alımını etkileyen işletme yetkisi |

Dinleme için ilgili görme yetkisi gerekir; arayüz bağımlı kutuyu birlikte seçer, API de bunu kontrol eder. Kullanıcı hesabını kapatma, şifre veya yetki değişikliği bütün oturumlarını iptal eder. Son etkin yönetici kapatılamaz veya kullanıcıya dönüştürülemez. Kullanıcı silme yerine hesabı devre dışı bırakma vardır; işlem geçmişi korunur.

## Ofis ağından bağlantı

Başka PC/tabletler aynı sunucunun **HTTPS** adresini açar. İstemcide Python/SDR sürücüsü gerekmez. Sunucu ilk kurulumu tamamlandıktan sonra, ofisin güvenilen TLS sertifikası ve PEM özel anahtarı ile örnek:

```powershell
.\Start-BIEM-ICC-SERVER.ps1 `
  -Project 'D:\Projects\Biem\_SDR' `
  -ListenAddress '0.0.0.0' -Port 8765 `
  -Origin 'https://biem-server.ofis.local:8765' `
  -Certificate 'D:\BiemKeys\server.crt' `
  -PrivateKey 'D:\BiemKeys\server.key'
```

Örnek alan adı yereldir, gerçek kurulum adresi değildir. İstemcilerde DNS/hosts çözümü ve sertifika güveni bu adla eşleşmeli. Windows güvenlik duvarında yalnız gerekli ofis alt ağına TCP 8765 erişimi verilmeli. Sertifika/anahtar ve güvenlik duvarı değişiklikleri bu geliştirmede otomatik yapılmadı. Sunucu düz HTTP ile LAN'a açılmayı reddeder. `Origin` tarayıcıda kullanılan adresle tam eşleşmelidir. Ters vekil başlıklarına güvenilmez; bu ilk sürüm Uvicorn'un doğrudan TLS bağlantısını kullanır. İnternete yönlendirme/port açma yapılmadı.

## Veriler ve güvenlik

- `data/server/accounts.sqlite3`: Argon2id şifre özetleri, açık yetkiler, kanal izinleri, hashlenmiş oturum belirteçleri, giriş denemeleri ve yönetim/dinleme olayları.
- `data/server/startup.json`: Sunucu açılışında başlatılacak alımlar.
- `data/server/server.log`: Başlangıç ve çalışma hataları.
- `data/server/config-backups/`: Web ayarlarında yapılan her kayıttan önce mevcut JSON dosyasının tarihli yedeği. Tarayıcı eski ayarı kaydetmeye çalışırsa sürüm kontrolü işlemi reddeder. Bozuk dosyalar kendiliğinden üzerine yazılmaz; yönetici ekranında uyarı ve başlangıç değerleri gösterilir. Yönetici düzelterek kaydettiğinde bozuk ham dosya da yedeklenir. Geçersiz kanal dosyasıyla alım başlatılmaz.
- Mevcut `data/radia.sqlite3`, kayıt dosyaları, mesaj indeksi, konumlar ve harita paketleri kullanılır. Bunlar HTTP statik dizini olarak paylaşılmaz. Ses için önce ekran ve kanal yetkisi doğrulanır; dosya yolu istemciye verilmez.
- Çerez: HttpOnly, SameSite=Strict; HTTPS modunda Secure. Oturum üst sınırı 8 saat, etkinlik olmadan 30 dakika. İsteklerde güncel hesap durumu kontrol edilir. Yazma işlemleri aynı origin + CSRF doğrulaması gerektirir. Giriş denemeleri sınırlandırılır.
- Eski DPAPI kayıtlarını okuyabilmek için sunucu, kayıtları oluşturan **aynı Windows hesabıyla** çalışmalıdır. Web yöneticiliği Windows yönetici yetkisi değildir. Mevcut spektrum sürücüsü Windows yönetici yetkisi istediği için, spektrum kullanılacaksa başlatıcı da bu yetkiyle çalıştırılmalıdır.
- Dinleme izni verilmiş ses istemciye aktarılır. Tarayıcıya ulaşan sesi kopyalamayı veya yeniden kaydetmeyi mutlak biçimde engelleme iddiası yoktur.
- Sunucu kullanıcı verileri ve test ortamları Git'e alınmaz. Anahtarlar, gerçek şifreler, kayıtlar ve haritalar yedek depoya gönderilmez.

## İlk sürüm sınırları

Bu, çalışan sunucu/istemci temelidir; Windows hizmet kurulum paketi, otomatik yeniden başlatan servis yöneticisi ve uzun süreli yük/saha kabulü henüz yoktur. Şu an Python sunucu sürecinin ofis bilgisayarında açık kalması gerekir. Uvicorn tek süreç/tek worker çalışmalıdır; ikinci sunucunun aynı veri klasörünü açması engellenir. Eski masaüstü uygulaması bu yeni kilidi tanımadığından, onu ayrıca kapatmak gerekir.

Kanal/frekans/RF ayarları web yöneticisinden düzenlenebilir ve mevcut masaüstünün JSON biçiminde saklanır. Bu ekran yalnız yöneticiye açıktır; standart kullanıcının alımı başlatma yetkisi ona ayar düzenleme yetkisi vermez. Kanal adları erişim izinlerinin kimliğidir: ad değişikliğinde kullanıcıya yeni kanal ayrıca tanımlanmalıdır; önceki arşiv eski adla kalır. Sunucu ve masaüstü aynı ayarları kullansa da aynı alıcı/arşivde eşzamanlı çalıştırılmamalı. Mevcut SDR/DMR/TETRA demodülasyon kodu değiştirilmedi.

Bu ayrı çalışma kopyasındaki `Start-Radia.cmd`, `Start-Radia-Admin.ps1` ve `Start-Radia-Diagnostic.ps1` masaüstü başlatıcıları da sunucu başlatıcısı gibi mevcut `D:\Projects\Biem\_SDR` veri/sürücü kökünü kullanır. Aksi halde Git çalışma kopyasında bulunmayan `vendor` DLL'si nedeniyle USB listesi boş görünüyordu. Önceki projenin başlatıcıları ve USB sürücü kurulumu değiştirilmedi.

Web haritasında mevcut çevrimdışı **sokak** paketi kullanılır; masaüstünün uydu katmanı, röle GNSS ikonları ve tüm ayrıntılı harita kontrolleri bu web sürümüne henüz taşınmadı. Masaüstündeki özellikler korunur. GNSS koordinatı gelmeden röle için konum uydurulmaz.

Kayıt/mesaj araması sayfa başına 100 sonuç verir; önceki/sonraki düğmeleriyle eski sayfalara geçilebilir. RF/CC/slot gibi ölçülmeyen bilgiler boş gösterilir. Yeni canlı ses aktarımı kısa ve sınırlı tamponla çalışır; gecikmiş ağda eski sesler biriktirilmez. Kesintisiz endüstriyel kayıt/SLA veya 8 kanal performans garantisi değildir.

## Doğrulama

2026-10-01: `Check-Radia.ps1` başarılı: Ruff, biçim kontrolü, ty, basedpyright ve **219 test** geçti. `python -m uv build` kaynak paketi ve wheel üretti. JavaScript sözdizimi `node --check` ile doğrulandı. Mevcut veri kökündeki çevrimdışı Türkiye sokak paketi sunucu çizicisiyle açılıp görsel olarak kontrol edildi; alıcı başlatılmadı. Önceki çalışma klasörünün Git durumunda değişiklik yok.

Donanımsız testlerde gerçek SQLite/Argon2/API kullanılır. Oturum, sayfa/kanal erişimi, doğrudan ses URL'si, şifre/değer sızıntısı, CSRF, hesap kapatma, son yönetici, çerezler, eşzamanlı sunucu kilidi, yavaş kayıt kapanışı, ses akışlarını ayırma ve başlatma hatasında temizlik test edilir. Testler SDR, ağ rölesi veya hoparlör açmaz.

Tam paket Git kontrolünde eski Tk testlerinde aralıklı Tcl dosya açma hataları görüldü. Dosyalar diskte mevcuttu; tekil testler geçti. [Pytest'in Python düzeyinde çıktı yakalaması](https://pytest.org/en/stable/how-to/capture-stdout-stderr.html) (`--capture=sys`) ile tüm 219 test geçti. Bu mod, yerel dosya tanıtıcılarını yeniden yönlendirmediği için test yapılandırmasına eklendi. Test veya doğrulama atlanmadı; üretim alıcısına müdahale edilmedi.

Tarayıcıda ayrı ve temsili test verileriyle ilk yönetici kurulumu, hesap oluşturma, bağımlı izin kutuları, oturum değiştirme, yalnız bir kanalın gösterilmesi ve açık/koyu görünüm kontrol edildi. Gerçek ofis ağından çoklu istemci, gerçek RF canlı ses ve uzun çalışma testi ayrıca yapılmalıdır.

### Aynı gün: yönetici ayarları ve USB takibi

Yeni tam kontrol: **238 test geçti**; Ruff, biçim, ty, basedpyright ve kaynak/wheel paketi başarılı. Ek testler: yönetici/CSRF sınırı, alım/spektrum/kapanış sırasında yazma engeli, kanal/mod/CC/ton doğrulaması, eski tarayıcı sürümünü reddetme, yedek ve atomik kayıt, USB seri numarası eşleştirmesi, bozuk JSON onarımı, geçersiz RF ayarlarıyla otomatik alım başlatılmadan web yönetiminin açık kalması ve kanal adı değişikliğinde izinlerin genişlememesi.

Tarayıcıdaki ayrı test ortamında kartın Ayarlar düğmesi, DMR seçilince CC'nin etkinleşmesi ve ton alanının kapanması, frekans/CC kaydı, PPM kaydının yeniden yüklenmesi ve standart kullanıcının ayarlara erişememesi doğrulandı. Test frekansları gerçek kanal dosyasına yazılmadı.

Donanım: bağlı Terratec T Stick PLUS / RTL2838UHIDIR sürücüden listelendi; sınırlı USB testinde **327.680 I/Q örneği** okundu ve alıcı normal kapatıldı. Bu, cihazın o testte listelendiğini ve veri verdiğini kanıtlar; ses çözümü veya kesintisiz kayıt kabul testi değildir. Günlüklerdeki aralıklı üç saniyelik USB veri bekleme hatası bu kısa testte tekrarlanmadı; kesin bir donanım arızası veya kalıcı giderim sonucu çıkarılmadı. USB sürücüsü/DLL, eski alım motoru, kayıtlar ve gerçek kanal ayarları değiştirilmedi.

Teknik dayanaklar: [FastAPI güvenlik belgeleri](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [Argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/howto.html), [OWASP oturum yönetimi](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html). Bu kaynaklar uygulama ayrıntıları için kullanıldı; kullanıcı gereksiniminin yerine geçmez.
