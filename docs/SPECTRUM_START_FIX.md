# Spektrum başlatma düzeltmesi — 13 Eylül 2026

Kullanıcı spektrum ölçümünün aralıklı olarak başlamadığını, canlı alımın çalıştığını bildirdi.

Kod incelemesinde sınırlı mesaj kuyruğunun hem üretici hem ekran tarafından kilitsiz tüketildiği görüldü. Doluluk/boşluk kontrolü ile get_nowait arasındaki yarış, Empty hatasıyla iş parçacığını veya Tk yenilemesini kesebiliyordu. Yayınlama ve toplu tüketim ortak kilide alındı. Çizim hataları yakalanıp günlüğe yazılıyor; ana uygulamanın yenileme döngüsüne taşınmıyor.

Başlatma, USB açılışı, örnek okuma, FFT ve kapanış hataları data/radia.log içinde Spectrum başlığıyla izlenebilir. Kuyruk düzeltmesi USB senkron okumasına zaman aşımı eklemez; donanım/sürücü kaynaklı bekleme olasılığı henüz dışlanmadı. Kullanıcının yaşadığı olayda bu yarışın tek neden olduğu doğrulanmadı.

Yalnız spectrum.py ve ilgili testler değişti. Canlı alım, çözücüler, USB sürücüleri ve SDR# değiştirilmedi. Önceki dosyalar data/backups/spectrum-start-20260913 altında saklandı.

Doğrulama: Spektrum ve bant ayarı testleri 10 geçti. Check-Radia.ps1 tüm statik kontrolleri ve 81 testi geçti. python -m uv build başarılı. Gerçek USB ile tekrarlı spektrum başlatma/durdurma kullanıcı doğrulaması bekliyor. Dağıtım EXE'si yeniden paketlenmedi; düzeltme ilk yerel sürüme uygulandı.
