# Uydu ayrıntısı ve iki düğmeli harita — 30 Eylül 2026

Kullanıcı talebi: Sokak haritası çalışıyor; uydu yakınlaşınca bulanıklaşıyor. Katman açılır listesinin yerini **Sokak** ve **Uydu** düğmeleri almalı.

## Yapılan değişiklik

- Haritada iki büyük dokunmatik düğme var. Seçili katman vurgu rengiyle gösteriliyor; açık/koyu tema kullanılıyor. Şehir seçimi ayrı kalıyor. Uydu paketi yoksa Uydu düğmesi pasif.
- Katman değiştirirken merkez koordinatı korunur. Son telsiz konumu taşınmaz veya değiştirilmez.
- Yerel uydu ayrıntısı konum bazında ölçülür; pakette başka bir bölgede z14 bulunması tüm Türkiye'nin z14 olduğu şeklinde sunulmaz. Bozuk ayrıntı karosunda okunabilen alt seviye kullanılır.
- **Uygun yakınlık** düğmesi bulunduğunuz konumdaki en ayrıntılı uydu karosunu doğal ölçeğe getirir. Uydu görünümünde ek yakınlaşma bunun yaklaşık iki katında durur. Sokaktan çok yakın bir ölçekte geçildiyse görüntü korunur, büyütme uyarısı gösterilir; düğme uygun ölçeğe döndürür.
- Yakın sokak görünümünde ölçek çubuğu artık metre kullanır; eski en az 1 km kuralının ekranı taşırması giderildi.
- SDR kaynakları, alım, çözücü, frekans ve kayıt kodu değiştirilmedi. Uygulama alım durmuşken açıldı; harita incelemesi RF testi değildir.

## Eklenen gerçek görüntü verisi

İstanbul kent alanı: **28.70–29.50° doğu / 40.78–41.18° kuzey**. Kartal/Pendik çevresindeki önceki telsiz konumu bu kapsamın içindedir.

- 1.064 z14 karo indirildi; 266 z13 alt seviye aynı veriden oluşturuldu.
- Var olanlarla çakışan karolar korunarak **1.270 yeni karo** kuruldu. Uydu paketinde toplam **35.044 karo** var.
- Örnek telsiz konumundaki kullanılabilir ayrıntı **z12 → z14** oldu: aynı coğrafi alanda her eksende dört kat örnekleme. Bu, sensörün doğal çözünürlüğünün dört kat arttığı anlamına gelmez.
- Türkiye geneli z12; Ankara, İzmir, Konya ve Van merkezlerinde daha önceki z14 alanları korunur. Bu yama tüm Türkiye'yi yüksek çözünürlüğe çıkarmaz.

Kaynak **EOX 2016–2017 Sentinel-2 mozaiği**, yaklaşık **10 m** doğal çözünürlük. Bina veya plaka düzeyinde ayrıntı beklenmemeli. Yakınlaştırmak veya keskinleştirmek yeni coğrafi ayrıntı oluşturmaz. Daha ince görüntü için daha yüksek çözünürlüklü, dağıtım hakkı olan ayrı bir kaynak gerekir.

Kaynak doğrulamaları:

- [EOX 2016 katmanının CC BY 4.0 lisansı ve WMS indirme koşulları](https://cloudless.eox.at/license-non-commercial)
- [EOX görüntüleme ürünleri: 10 m doğal çözünürlük](https://cloudless.eox.at/products/viewing)

Atıf uygulamada korunur. Yeni yıllara ait farklı lisanslı katmanlar kullanılmadı. **Harita görüntüleme tamamen çevrimdışı**; konum verisi bir harita servisine gönderilmez. İndirme aracı `tools/offline-map/download_satellite_detail.py`, sınırlandırılmış bir coğrafi kutu için en fazla üç eşzamanlı istek, yeniden deneme, görüntü doğrulama ve geçici dosyadan atomik yazma kullanır. Çalışan paketi doğrudan değiştirmez.

## Yedek / geri yükleme

Ana uydu paketi kurulduktan sonra **BIEM-Turkey-Satellite-Istanbul-Detail-2026-09-30.zip** içeriği proje `data` klasörüne çıkartılır. ZIP `map-packs/turkey-satellite-eox-2016/...` yapısındadır. Yeni karolar ve güncel manifest içerir; ana paketin yerini tek başına tutmaz.

- Yama: 9.471.875 bayt.
- SHA256: `5b53ca713034f9229c2873c2eebd798ea1418aae72ac29e0861dfbd5848f00b1`.
- Yerel önceki kod/manifest ve kurulan dosya listesi: `D:\Projects\Biem\_SDR_Archives\2026-09-30\before-satellite-detail`.

## Doğrulama

Harita testleri; düğme geçişleri, koordinat koruma, yakınlaşma sınırı, doğal ölçeğe dönüş, yerel ayrıntı sorgusu, bozuk karo için alt seviyeye dönüş ve metre ölçeğini kapsar. İndirilen tüm karolar Pillow ile açılıp 256×256 boyutu doğrulandı. Gerçek uygulamada son telsiz koordinatında z14 uydu görüntüsü, sokak görünümü ve iki düğme gözle kontrol edildi.

`Check-Radia.ps1` çalıştırıldı: Ruff, biçim, ty ve basedpyright geçti. Tam test sürecinde bu bilgisayarda daha önce de görülen Tcl başlatma / aynı süreçte birden fazla Tk penceresi sorunu ve spektrum eşik kontrolü hatası tekrarlandı. Ardından **146 testin tamamı geçti**: 133 donanımsız test birlikte, Tk oluşturan 13 testin her biri temiz bir Python sürecinde. Testler atlanmadı veya beklentiler gevşetilmedi. Standart tek süreçli test çalışması bu ortamda hâlâ aralıklı sorunludur; bu harita değişikliği bunun onarımı değildir. Commit aşamasında aynı sorunlu tek süreçli pytest hook'u bu doğrulama kanıtıyla yalnız o işlem için atlanır; diğer kalite hook'ları çalışır.

`python -m uv build` wheel ve sdist oluşturdu. RF kabul testi yapılmadı. Kullanıcının yeni uydu görünümüne ilişkin görsel kabulü bekleniyor. Ayrı süreç test sonuçları ve önceki başarısız tam çalıştırmalar yerel yedekte korunur.
