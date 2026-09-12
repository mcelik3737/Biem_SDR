# Doğrulama — 12 Eylül 2026

## Gerçek ortam

- Proje: `D:\Projects\Biem\_SDR`; önceki Codex çalışma klasörü boş bir Git deposuydu.
- İstenen `BIEM_Radia_Codex_Proje_Talimati.md` dosyası belirtilen konumlarda bulunamadı. Bu uygulama kullanıcının mesajlarındaki analog FM önceliğine göre hazırlandı; bulunmayan dosyanın okunmuş olduğu iddia edilmez.
- Mevcut SDR# kurulumu okunarak incelendi; dosyaları ve sürücüsü değiştirilmedi.
- USB PnP: `VID_0CCD&PID_00D7`, iki Bulk-In arayüzü, Windows durumu OK.
- librtlsdr: `Terratec T Stick PLUS`, `Elonics E4000` tuner.
- Gerçek örnek akışı: 960 kS/s; merkez 446,10625 MHz; çözülen kanal 446,00625 MHz.
- USB açma, örnek okuma, asenkron alım iptali ve tekrar açma gerçek cihazla doğrulandı.
- Otomatik kazançla başlangıç gürültüsü −60 dBFS'den yaklaşık −46 dBFS'ye yükselerek sürekli kayıt açtı. Sabit 19 dB kazançla boş kanal yaklaşık −59 dBFS'de kaldı; −48 dBFS eşikte kayıt bekleme durumuna geçti.
- İlk kazanç denemesinin 180,012 ve 48,077 saniyelik WAV dosyaları arşive yazıldı. Bunlar doğrulanmış konuşma kayıtları değildir; test RF/gürültü kayıtları olarak korunuyor.
- Windows arayüzü açıldı; canlı seviye, durdurma, arşivde iki WAV satırı ve yeni kazanç kontrolü görsel olarak doğrulandı.

## Otomatik kontroller

17 test: bilinen FM tonunun çözülmesi, düzensiz bloklarda filtre sürekliliği, iki eşzamanlı kanalın ayrılması, bant dışı taşıyıcının bastırılması, iki ayrı konuşma parçası, ön/son tampon, WAV başlığı ve PCM verisi, gün/kanal araması, açık kaydın hata veya durdurmada tamamlanması, maksimum süre bölünmesi, parçalı rtl_tcp başlığı/komutları, ağ kopması, hatalı kanal/bant sınırları, arşiv yol güvenliği, gerçek uygulama motorundan arşive sentetik I/Q akışı, USB kuyruk taşması bildirimi, masaüstü kanal düzenleme ve kayıt seçme/dinleme dosya yolu.

Ruff, biçim kontrolü, ty ve basedpyright geçiyor. Wheel ve kaynak paketi oluşturuldu. Test kapsamı raporunda toplam yaklaşık %71; gerçek DLL ve kullanıcı etkileşimlerinin tüm hata dalları otomatik kapsamda değildir. Sayısal test kapsamı saha kabulü yerine kullanılmaz.

## Henüz doğrulanmayan veya uygulanmayan işler

- Kullanıcının telsizinden anlaşılır canlı konuşma alımı ve mandal bırakıldıktan sonra ayrı kayıtlara bölünmesi: kullanıcı testi bekleniyor.
- Aynı cihazla çok kanallı gerçek yayın performansı ve 24 saat kesintisiz çalışma.
- Ethernet üzerinde gerçek rtl_tcp sunucusu: adaptör mevcut, yerel protokol testi geçti; gerçek ağ cihazı testi bekliyor.
- DMR hava arayüzü/ses çözümü, ID/grup/slot çıkartma ve alias eşlemesi uygulanmadı.
- Hytera repeater entegrasyonu uygulanmadı; rtl_tcp bu entegrasyon değildir.
- Crash recovery, disk kotası, saklama süresi, kullanıcı yetkileri ve kurumsal yedekleme sonraki aşama.

## Sonraki kabul ölçütü

446,00625 MHz analog kanalda 5–10 saniyelik iki test konuşması, arada en az 2 saniye taşıyıcısız bekleme. Her biri ayrı dosya olmalı; tarih/kanal aramasıyla bulunmalı ve kullanıcı sesi anlaşılır duyduğunu doğrulamalı. Ancak bundan sonra analog saha kabulü tamamlandı sayılmalı.
