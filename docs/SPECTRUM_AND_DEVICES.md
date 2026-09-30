# Yönetici spektrumu, cihaz seçimi ve arayüz

2026-09-12 kullanıcı isteği uygulama notu.

## Uygulandı

- Açık gri/beyaz Windows tarzı arayüz, Segoe UI, mavi seçimler. Kullanıcının
  `D:/BIEM/BIEM_FILES/yeni_logo` klasöründen iki orijinal PNG paket içine kopyalandı;
  kaynaklar değiştirilmedi. Logo ve pencere simgesi Tk ölçeklemesiyle gösterilir.
- BİEM sekmesinde şirket adı, telefon, e-posta, adres ve web bağlantısı.
  Bilgiler https://biemelektronik.com/ üzerinden doğrulandı.
- Spektrum / Yönetici: başlangıç-bitiş MHz, Hamming/Hann/Blackman/dikdörtgen
  FFT pencereleri, spektrum/şelale/birlikte görünüm. 2048 noktalı FFT, 960 ksps,
  yaklaşık 468.75 Hz bin aralığı. Genlik FFT bin başına dBFS; kalibre dBm değil.
- 24 MHz'e kadar aralık, alıcının güvenli bant parçaları sırayla ölçülerek
  birleştirilir. Bir şelale satırı bir TAM taramadır, eşzamanlı geniş bant değil.
  Yeniden ayarlama/USB açılışı ve 250 ms yerleşme süresi tarama hızını sınırlar.
  Her tuner yazılımın kabul ettiği 24–1700 MHz sınırlarının tamamını desteklemeyebilir.
- Yönetici denetimi Windows yükseltilmiş süreç belirtecidir (IsUserAnAdmin).
  Normal kullanıcıda başlatma düğmesi kapalı; worker da yetkiyi tekrar denetler.
  Ayrı uygulama kullanıcı/şifre/rol sistemi değildir. `Start-Radia-Admin.cmd`
  Windows UAC üzerinden yönetici açılışı sağlar; UAC işlemini kullanıcı tamamlar.
- USB cihazları sürücü üzerinden açmadan listelenir: USB index/kodu, RTL-SDR tipi,
  üretici/ürün, seri numarası. Liste açılışta veya Yenile ile güncellenir;
  durum zaman damgası yerine açıkça son yenileme anı olarak belirtilir.
  Listelenme USB'nin boşta/kullanılabilir olduğu anlamına gelmez.
- Seçilen cihaz data/device.json içinde tutulur; benzersiz seri yeniden eşleştirilir.
  Ana alım, FM RADIO ve spektrum seçilen USB index'ini kullanır. Birbirlerini
  kilitlerler: ölçüm için kayıt/FM alımı kapatılmalıdır. Ethernet SDR için
  IP/port, Hytera için girilen IP ve etkin olmayan sürücü durumu görünür.

## Doğrulama

- FFT dört pencere için bilinen frekans ve genlik, bant kapsamı, yönetici reddi,
  üç parçalı taramada kaynağın kapanması ve ölçümün tamamlanması donanımsız test edildi.
- İki USB cihazının sırası değiştiğinde seri eşleştirme, seçilen cihazın kaybolması,
  Tk üzerinde şelale çizimi ve mevcut kayıt testleri çalıştırıldı.
- Normal kullanıcıda yönetici düğmesinin kilitli olduğu ve yeni canlı kanal
  arayüzü ekranda görüldü.
- Gerçek USB envanteri: Terratec T Stick PLUS, Realtek / RTL2838UHIDIR,
  seri 00000001. Canlı spektrum ve yükseltilmiş yönetici alımı ayrıca kullanıcıyla
  doğrulanacak. Bu oturumda spektrum üzerinden gerçek RF kabul testi yapılmadı.

## Sonraki aşama — kullanıcının çoklu SDR isteği

2–3 cihaz için kalıcı kullanıcı kodu/isim, fiziksel USB bağlantı yolu, seri
çakışması uyarısı, otomatik tak/çıkar takibi; ayrı cihazlara kanal atama ve
bağımsız eşzamanlı alıcı işçileri. Tuner tipi ve desteklenen frekans/gain sınırları
cihaz açılınca gösterilmeli. IP SDR ve Hytera bağlantı sağlığı gerçek sürücülerden
alınmalı. Mevcut sürüm bir USB seçer; çoklu bağımsız alım uygulanmadı.
