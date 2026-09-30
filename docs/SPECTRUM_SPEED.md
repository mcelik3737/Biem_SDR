# Spektrum tarama hızı

USB cihazı her bantta yeniden açılıp kapanmıyor. Spektrum kaynağı senkron USB
okuması kullanıyor; tek worker dışında okuma veya frekans değiştirme yok.
Frekans/gain/PPM değişikliği sonrası donanım tamponu sıfırlanıyor, ayarlanabilir
yerleşme örnekleri atılıyor ve ardından FFT ölçülüyor. Asenkron ana kayıt yolu
aynı kalır; hızlı ayarlama o yolda reddedilir.

Hızlı (varsayılan): 60 ms; Dengeli: 120 ms; Kararlı: 250 ms / bant geçişi.
Değişmeyen tek bantta yeniden yerleşme beklenmez, tampon yine temizlenir.
Yayın döngüsü en fazla 10 tam tarama/saniye hedefiyle sınırlandırılır; gerçek hız
USB, tuner, bant sayısı ve FFT işlem süresine bağlıdır. Arayüz 200 ms'de yenilenir.
Bu bir garanti edilen yenileme hızı değildir. AGC veya kararsız tepe genliklerinde
Dengeli/Kararlı seçilmelidir.

Testler tek USB açılışıyla üç bant ölçümünü, kapanışı, frekans/gain/PPM sonrası
tampon sıfırlama sırasını, aynı frekansta gereksiz tuner komutlarının atlanmasını
ve asenkron kayıt yolunda yeniden ayarlamanın reddini doğrular.

Gerçek USB hız testi denendi ancak cihaz açılışı -3 döndürdü; cihazın başka bir
programca kullanılıyor olması mümkündür. Sürücüler değiştirilmedi, başka program
kapatılmadı. Ölçülmüş gerçek hız veya performans artış oranı henüz yok.
Sonuç data/spectrum-speed-proof.json içinde.
