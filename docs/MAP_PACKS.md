# İsteğe bağlı çevrimdışı harita paketleri

Haritalar uygulama kodundan ayrı, `data/map-packs/<ad>-<sha256 öneki>/` altında tutulur. Uygulama wheel paketine veya Git deposuna eklenmez. Harita paketi olmadan standart Natural Earth haritası çalışır.

## Yükleme

```powershell
.\Install-MapPack.ps1 -ArchivePath "D:\Desktop_Yedek\MAPS\Yeni klasör (2)\konya\googlemaps\turkey_9_katman.zip"
```

Radia yeniden açıldığında Harita listesinden paket seçilir. Aynı ZIP tekrar verilirse aynı kurulum kullanılır; mevcut paket silinmez. Paket kendi başına kod çalıştıran bir eklenti değildir, isteğe bağlı harita verisidir.

Destek: ZIP içinde herhangi bir kökün altında `z/x/y.png`, `.jpg`, `.jpeg`; görüntüler 256×256, XYZ Web Mercator. Dosya yolları doğrudan çıkartılmaz; doğrulanan sayısal koordinatlardan hedef yollar oluşturulur. Dosya boyutu, görüntü boyutu ve dosya bütünlüğü kontrol edilir. Tamamlanmayan paket manifest yayımlamadığı için etkinleşmez.

## Görüntüleme

Görünümün piksel yoğunluğuna göre yerel seviye seçilir. Daha kaba seviyeler eksik kapsama için altta kalır. Yalnız görünen parçalar açılır; çözülmüş görüntü önbelleği 128 karoyla sınırlıdır. Yakınlaştırma üst sınırı genişletilmiş pakette 8192× düzeyine çıkarıldı. `Paket alanı` en yüksek ayrıntı seviyesinin kapsama kutusuna götürür. `Son telsize yaklaş` gerçek son bildirilen koordinata gider. Görüntüdeki yer adlarıyla çakışmayı azaltmak için yeni veri paketinde ilave şehir etiketi varsayılan kapalıdır.

## İlk paket doğrulaması

`turkey_9_katman.zip`: 3.396 PNG, 16.446.244 bayt açılmış görüntü verisi; adındaki 9 ifadesine rağmen z1–11 içerir. Konya çevresindeki örnek görüntüde yol numaraları ve yer adları görsel olarak doğrulandı. Ayrıntılı z11 kapsaması Türkiye'nin tamamını kapsamaz; Marmara'daki son telsiz noktasında daha kaba seviyeler kullanılır. Bu nokta yüksek ayrıntı alanına taşınmaz veya sahte konum verilmez. Önceki uydu paketi ayrı seçim olarak korunur.

Kaynak harita görüntüleri kullanıcı tarafından sağlandı. Sağlayıcı/dağıtım lisansı bu pakette doğrulanmadı; ticari kurulumda dağıtım hakkı ayrıca belirlenmelidir. Radia bu entegrasyonda hiçbir çevrimiçi harita isteği yapmaz.


## Kullanım kararı — sunum sürümü (12 Eylül 2026)
Kullanıcı kararı: mevcut çevrimdışı haritalar ve turkey_9_katman paketi şimdilik sunum / demo için kullanılacak. Bu paket son müşteri teslimatı olarak kabul edilmeyecek. İleride çevrimiçi harita kullanımı değerlendirilebilir; sağlayıcı, bağlantı yöntemi ve müşteri sürümünün harita çözümü henüz seçilmedi. Bu not çevrimiçi servisi şimdi etkinleştirme veya konum verisini dışarı gönderme talimatı değildir. Mevcut sunum sürümü çevrimdışı çalışmaya devam eder.


## Roadmap devam paketi — 12 Eylül 2026

Kullanıcının verdiği yolun mevcut karşılığı `D:\Desktop_Yedek\MAPS\Yeni klasör (2)\konya\googlemaps\roadmap` bulundu. Önceki turkey_9_katman verisiyle birleştirilerek **Türkiye yol haritası - genişletilmiş** seçeneği kuruldu. Önceki paket ve kaynak dosyalar korundu.

- 374,831 koordinatlı karo, z1–17; 167,716 benzersiz görüntü. Aynı görüntü farklı koordinatlarda tek içerik dosyasına bağlanır. Düz renkli karolar geçerli zemin olabileceğinden otomatik silinmedi.
- Aynı XYZ'de 0 farklı dosya saptandı; bunlarda önceki paketin görüntüsü korundu. 3396 aynı koordinat/içerik tekrarlandı. Reddedilen dosya: 0. Ayrıntılı import raporu kurulu pakette.
- Yerel `tile-index.json`, sayısal koordinatları `tiles/content/<sha256>.png` içeriğine eşler. Bu klasör kurulumu mevcut basit ZIP yükleyicisinin yeni bir dağıtım formatı desteği değildir; bu aşama sunum için yerel birleştirmedir.
- Görüntü boyutu, PNG bütünlüğü ve çözülebilirlik kontrol edildi. Her seviyeden örnek okundu. Yerel indeks yükleme ölçümü 2.77 sn; yakın görünüm sorgusu 0.16 ms, 71 görünür karo. Bu sorgu süresi çizim/FPS ölçümü değildir.
- Yakınlaştırma üst sınırı 64× yerine 8192×; görünür koordinatlar doğrudan aranır. Görüntü önbelleği 128 içerikle sınırlı kalır. Telsiz koordinatı ve ikonun 44–192 piksel sınırı değişmez.
- 73 donanımsız test, kalite kontrolleri ve 0.2.0 paket derlemesi geçti. Canlı kullanıcı ekranındaki akıcılık ve yeni kapsama görsel kabulü bekleniyor. Harita internet kullanmaz; RF alımında değişiklik yapılmadı.

Yeni paketi görmek için Radia yeniden açılır; Harita listesinden **Türkiye yol haritası - genişletilmiş (paket)** seçilir. **Paket alanı** yüksek ayrıntı bölgesine götürür; **+** veya tekerlekle yaklaşılır. Son telsiz konumu bu bölgeye taşınmaz. Yeni z17 kapsaması bütün Türkiye için sokak ayrıntısı anlamına gelmez.

## 30 Eylül 2026 güncellemesi

Yukarıdaki Google/9 katman notları geçmiş entegrasyon kaydıdır. Bu paketler yeni yol ve uydu haritaları doğrulandıktan sonra etkin projeden çıkarılıp yerel arşive taşındı. Güncel paketler ve geri yükleme adımları [yedek notunda](BACKUP_2026-09-30.md), görsel kullanım [dokunmatik konsol notunda](TOUCH_CONSOLE_2026-09-30.md).
