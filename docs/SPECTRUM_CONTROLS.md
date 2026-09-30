# Spektrum ölçüm kontrolleri

## Yan sürgüler

Solda eşik dBFS, üst seviye dBFS ve görünüm aralığı dB sürgüleri bulunur.
Sağda 1–20× görünüm yakınlığı ve ölçülmüş bant içindeki merkez konumu (%) bulunur.
Spektrum, tepe etiketleri, fare işaretçisi ve şelale aynı görünür aralığı kullanır.
Yakınlık gerçek FFT çözünürlüğünü artırmaz; mevcut ölçümün görünümünü büyütür.
Sürgüler ölçüm geçmişini veya ana kayıt squelch ayarlarını değiştirmez.

Tam bandı göster görünümü sıfırlar. Görünen bandı ölçüm aralığı yap, ölçüm durmuşken
başlangıç/bitişi yeni aralığa aktarır; Ölçümü başlat ile daha dar aralık ölçülebilir.
Tarama sürerken görüntü yakınlaştırması serbesttir, RF aralığı kendiliğinden değişmez.
Testler yakınlık, bant uçlarında merkez sınırlandırma, sabit frekanslı marker/seviye,
eşik farkı ve geçmişin korunmasını doğrular.

Kullanıcının seviye/eşik ve fareyle tepe kilitleme isteği, 2026-09-12.

Araştırma: GNU Radio Frequency Sink ve FFT belgelerinde referans seviye,
görünüm aralığı, FFT ortalaması ve tepe tutma ayrı kontrollerdir:
https://wiki.gnuradio.org/index.php/QT_GUI_Frequency_Sink
https://wiki.gnuradio.org/index.php?title=FFT

Uygulanan kontroller:

- RF kazanç, Tuner AGC ve PPM aynı sekmededir. RF ayarını uygula, değişikliği
  sonraki tam taramada devreye alır; aynı taramanın bant parçaları aynı ayarla ölçülür.
  Son bantta uygulanan kazanç ve ADC sınırına yaklaşan örnek yüzdesi gösterilir.
- Üst seviye ve görünüm aralığı spektrum ile şelaleyi birlikte ölçekler.
  Otomatik ölçek gürültü tabanı ve en yüksek değere göre görünümü ayarlar.
- Tepe eşiği dBFS/bin cinsindedir; ana alıcının kanal gücü/squelch eşiğini değiştirmez.
  Eşik üstünde, yerel belirginliği en az 3 dB olan en güçlü altı tepe etiketlenir.
- 1/2/4/8 taramalık üstel ortalama doğrusal güç alanında hesaplanır; tepe tutma
  ham taramalardaki maksimumları gösterir. RF ayarı, aralık veya FFT penceresi
  değişince geçmiş sıfırlanır. Tepeleri sıfırla elle sıfırlar.
- Fare gezinmesi frekans/seviye/eşik farkını gösterir. Sol tık 18 piksel içindeki
  en yakın belirgin tepeye kilitler; sağ tık kilidi kaldırır. Kilit frekansa bağlıdır.
  Durdurulduktan sonra yakınlaş düğmesi kilidin çevresinde 250 kHz aralık hazırlar.
- İşaretli bant 6.25/12.5/25/200 kHz seçilebilir; görsel seçimdir, RF filtresi veya
  kanal gücü ölçümü değildir. FFT/aralık değişince durdurup başlatmak gerekir.
- Şelale bütün grafik genişliğini kullanır. Her tarama üç piksel yüksekliğindedir;
  henüz ölçülmeyen geçmiş koyu kalır. Fare/yeniden boyutlandırma sahte satır eklemez.

Sinyal tipi: bu ölçüm yolu protokol çözücü çalıştırmıyor. Kilide yakın tanımlı
kanal varsa adı ve kullanıcı tarafından seçilmiş modu gösterilir, RF'den
doğrulanmadığı belirtilir. Kanal eşleşmezse bilinmiyor denir. Spektrum şeklinden
DMR/TETRA/analog tahmini yapılmaz; dBm kalibrasyonu olmadığı için dBm gösterilmez.

Doğrulama: 57 test ve paket derleme başarılı. Bilinen tepe seviyesi, eşik reddi,
ölçek sınırları, kilit frekansı, tepe tutma/sıfırlama, RF değişiminde geçmiş temizliği,
genişlik uyumu ve yakınlaştırma donanım kullanmadan test edildi. Mevcut kullanıcı
görseli önceki sürümün RF alımını gösterir; yeni kontrollerin canlı RF kabul testi
ayrıca yapılmalıdır.
