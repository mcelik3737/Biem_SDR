# Anten giriş gücü ve kayıt maksimumu — 2026-09-30

## Kullanım

Canlı kanal kartında frekans kaymasının yanında anten gücü ve RF seviyesi bulunur.
Kalibrasyon yoksa `Anten: — dBm` ve ölçülen **dBFS** gösterilir. Bu değer kazançtan
etkilenir; kazancı çıkarmak onu gerçek dBm ölçümüne dönüştürmez. Ses kazancı bu RF
ölçümüne katılmaz. SDR kazancı veya sürücüsü bu özellik için değiştirilmez.

Her yeni kayıt için en güçlü ölçüm arşivde **Maks. RF (kanal)** sütununa ve dosya
adına yazılır: `..._5.76sn_max-24.5dBFS.wav.radia`. Geçerli kalibrasyonla örnek
ek `_max-68.2dBm` olur. Örnek değerler temsildir. Korumalı kayıt biçimi ve yönetici
dinleme kontrolü korunur; eski dosyalar yeniden adlandırılmaz.

## Gerçek dBm referansı

**Alıcı ayarları → RF güç kalibrasyonu / dBm** düğmesi kullanılabilir.

1. Anten portuna ulaşan gücü bilinen bir RF referansı hazırlayın. El telsizinin
   programlanmış çıkış gücü, kablosuz yoldan SDR'ye ulaşan güç değildir.
2. Referansı dinleyen kanalı açın, manuel kazanç kullanın. Kalibrasyon penceresinde
   o kanalı ve anten portundaki bilinen dBm değerini seçin.
3. Referansı kaydedin; alımı durdurup başlatın. Profil yalnız o cihazın benzersiz
   USB seri bilgisi, nominal frekans, mod, filtre, örnek hızı, PPM ve **uygulanan**
   donanım kazancı ile eşleşirse kullanılır.

`dBm ≈ kanal RMS dBFS + ölçülmüş referans ofseti`. Referans ofseti bütün alım
zincirini içerir; kazanç ikinci kez çıkarılmaz. Tek noktadan kalibrasyon yaklaşık
sonuçtur. Tuner doğrusal olmayan davranışı, sıcaklık, kablo/filtre değişiklikleri
ve cihazın analog katında sıkışma hata oluşturabilir. Profesyonel RF güç ölçer
doğruluğu iddia edilmez; farklı seviyelerde referansla doğrulama gerekir.

AGC, kimliği belirlenemeyen cihaz, rtl_tcp, ADC uç değerleri, kazanç değişiminden
sonraki 1 saniye veya eşleşmeyen profil durumunda dBm üretilmez. Doygunluk uyarısı
ADC örnekleriyle sınırlıdır; tüm RF katlarının sıkışmasını tespit etmez.
Kalibrasyon kaydı için canlı, son 2 saniyede alınmış ölçüm ve −110 ile −3 dBFS
arasında referans gerekir. Bu sınırlar doğruluk garantisi değildir.
Profil yerel `data/rf-power-calibration.json` dosyasındadır; Git'e gönderilmez.

## Ölçüm ve veritabanı

- Ölçüm: kanal filtresi çıkışındaki karmaşık I/Q için `10 log10(mean(|IQ|²))`.
  Demodülasyon öncesidir; ses hacmi veya spektrumun tek FFT kutusu değildir.
  En yüksek değer, işlenen blokların RMS ölçümleri arasındaki maksimumdur;
  anlık RF tepe zarfı ölçümü değildir. USB'nin mevcut okuma blokları yaklaşık 17 ms.
- Analog, DMR/APCO25/NXDN, TETRA ve AUTO kayıt yolları kapsanır. AUTO her adayın
  kendi filtresinden ölçer. Tür bulunmamışsa canlı RF alanı TETRA adayının 25 kHz
  ölçümüdür; bu, türün TETRA olarak doğrulandığı anlamına gelmez.
- DMR/TETRA değeri frekansın **ortak kanal RF gücüdür**. Diğer slotun yayını da
  maksimuma katkı verebilir. Slot başına bağımsız dBm ölçümü yapılmaz.
- Analog penceresi örnek saatinden; DMR penceresi mevcut çözücünün son olay zamanı
  ve ses süresinden tahmin edilir (olay zamanı saniye çözünürlüğünde). TETRA ilk/son
  sesin bilgisayara geliş zamanını kullanır. Dijital güç/çağrı ilişkisi bu zaman
  sınırları ve çözücü tampon gecikmeleri kadar yaklaşıktır.
- En fazla 24.000 blok geçmişi tutulur. Ölçüm aralığı eksikse dBm maksimumu NULL
  kalır; mevcut blokların dBFS maksimumu ve `partial_window` bilgisi saklanır.
  İçe aktarılan eski ses dosyalarına başka bir çağrının gücü atanmaz.
- Her 90 saniyelik kayıt ayrı özetlenir. Aradaki 2 saniye yeni kaydın maksimumuna
  taşınmaz. Analog ton kapısı için kullanılan yapay −120 değeri RF ölçümü yerine
  yazılmaz. Kayıt tetikleme/squelch davranışı değiştirilmez.

SQLite `calls` tablosuna nullable `rf_peak_dbfs REAL`, `rf_peak_dbm REAL`,
`rf_power_info TEXT` eklendi. JSON bilgi alanında yöntem, zaman temeli, ölçüm
sayısı, kalite durumu, maksimum anındaki cihaz/kazanç/PPM/filtre ve kalibrasyon
kimliği bulunur. Eski satırlar NULL kalır. Dosya adı ve DB aynı özetten üretilir.
Bir kayıt sırasında geçersiz kalibrasyonlu blok varsa o kaydın dBm maksimumu
yayınlanmaz; en yüksek gözlenen dBFS korunur.

## Doğrulama durumu

Yazılım testleri: referansın saklanması, farklı kazanç/frekans eşleşmesi, AGC,
doygunluk, eksik aralık, eski şema geçişi, analog 90/2 sınırları, ham RF/ton kapısı
ayrımı, dijital slot kimlikleri ve dosya/DB tutarlılığı. Bunlar yapay verili
testlerdir; canlı RF veya mutlak güç doğruluğu kabulü sayılmaz.

Gerçek cihazla bilinen RF referansı ve yeni canlı kayıt kabulü bekliyor.
Önceki kaynak ve veritabanı yedeği:
`D:\Projects\Biem\_SDR_Archives\2026-09-30\before-rf-power`.

Kaynaklar:
[librtlsdr sürücü API'si](https://github.com/osmocom/rtl-sdr/blob/master/include/rtl-sdr.h)
I/Q ve tuner kazanç arayüzlerini tanımlar; doğrudan anten giriş dBm ölçümü sağlamaz.
[SDRangel güç kalibrasyonu](https://github.com/f4exb/sdrangel/blob/master/sdrgui/gui/spectrumcalibration.md)
bilinen referansla eşleştirmeyi ve alıcı ayarlarının kalibrasyon etkisini açıklar.
