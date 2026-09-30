# Otomatik çözümleme — 30 Eylül 2026

## Kullanım

1. Kaynak sürümü `D:\Projects\Biem\_SDR\Start-BM-ICC-08.cmd` ile açın.
2. Alım kapalıyken **Canlı izleme → Kanal ayarları → Mod: Otomatik** seçin.
3. Frekansı ve Eşik / dBFS değerini ayarlayın, kanalları kaydedin ve alımı başlatın.
4. İlk saha denemesini tek etkin kanal ve **Sabit** alımla yapın. Ekranda
   `OTOMATİK • DMR`, `DMR / Hytera XPT`, `TETRA`, `Analog FM (olası)` veya
   `Bilinmiyor / yayın bekleniyor` görünür. CC ve analog ton alanları Auto'da kapalıdır.

Mevcut kanal seçimi, frekanslar ve kayıt arşivi kendiliğinden değiştirilmez.
Önceki ayrı kurulum EXE'si yeniden paketlenmedi; bu özellik yerel kaynak sürümündedir.

## Kapsam ve karar kuralları

- Tek I/Q akışından DMR ve TETRA çözücüleri birlikte çalışır. DMR 12,5 kHz,
  TETRA 25 kHz filtresi kullanır; analog aday yolunda kanalın analog filtre ayarı kullanılır.
  Yeni USB bağlantısı açılmaz; bağımlılıklar USB alımından önce hazırlanır.
- **DMR:** 1,5 saniyelik pencerede aynı CC ile en az üç geçerli senkron çıktısı.
  CRC/FEC/senkron hatası aday sayacını sıfırlar. AMBE `err = [0] [0]` başarı
  satırları hata sayılmaz. Ses arşivleme mevcut WAV/olay eşleştirme, şifreli çağrıyı
  dışlama ve slot belirsizliğini koruma kurallarından geçer. Oturumda DMR doğrulandıktan
  sonra kapanışta gelen tamamlanmış WAV da içe alınabilir.
- **TETRA:** en az üç hatasız alınmış veri olayı ve geçerli CC gerekir. Doğrulanmış
  akışta ses çerçeveleri kilidi sürdürür. Ses için ayrıca o slota ait güncel açık çağrı
  bilgisi gerekir. Şifre çözme eklenmedi. İlk doğrulama çerçevelerinin sesi atlanabilir.
- **XPT:** genel DMR senkronundan veya marka isminden çıkarılmaz. CRC denetiminden
  geçen DSD-FME `Hytera XPT Site Status` / `Hytera XPT CSBK 0x0B` çıktısı tekrarlanmalıdır.
  Yalnız dinlenen frekanstaki çözümleme/etiketleme vardır; otomatik trunk frekans takibi yoktur.
- **Analog:** yaklaşık iki saniye olumlu FM ses ölçütü gerekir. Gürültü, modülasyonsuz
  taşıyıcı, dört seviyeli FSK ve belirgin sembol saati özellikleri elenir. Son üç saniyede
  dijital kanıt varsa analog açılmaz. Sonuç **olası** olarak gösterilir: bu bir sezgisel
  sınıflandırıcıdır, tüm sinyal tipleri için kesin tanı değildir. Zayıf, kısa veya yoğun
  parazitli analog çağrılarda manuel Analog modu daha uygun olabilir. Aday analog ses
  için 2,5 saniyeye kadar ön tampon vardır; uygunsuz bölümler sessizlikle tutulur.
- Çelişen DMR/TETRA kanıtı ayrı gösterilir. Dijital kanıt geldiğinde analog kayıt kapanır.
- **APCO25 ve NXDN mevcut manuel modlarda kalır; bu Auto sürümünde otomatik çözülmez.**
- Analog ID/grup/slot değerleri boş kalır. Dijital kayıtlarda yalnız çözülen metadata
  kullanılır. Mevcut yönetici dinleme yetkisi, kayıt koruması ve 90 sn / 2 sn kuralları korunur.
- Tarama Auto kanalında en az 3 sn tanıma zamanı tanır. Türü bulunamayan güçlü taşıyıcıya
  süresiz kilitlenmez; TETRA sessiz taşıyıcı 20 sn ve kontrol kanalı geçiş kuralı sürer.

## Frekans ve günlük

Girilen frekans ve mevcut PPM ayarı korunur. Kanal ayarındaki **Yakın sinyale kilitlen
(±6,5 kHz)** seçeneği açıkken, ayrı RF takip katmanı yakındaki uygun sinyalin merkezini
izler ve o kanalın I/Q akışını çözücüden önce sayısal olarak düzeltir. Bu özellik
Otomatik ve manuel modlarda ortaktır; protokol tanımasıyla aynı kilit değildir.
Ayrıntı: [SIGNAL_FOLLOW.md](SIGNAL_FOLLOW.md). Korunan bandın her iki yanında
12,5 kHz komşu sinyal / kalite uyarısı ayrı geliştirme maddesidir; henüz uygulanmadı.

Tür değişimleri `data/dmr-sessions/<oturum>/auto-detection.jsonl` ve arşiv olay
günlüğüne yazılır; Dijital veri günlüğü ekranında da görünür. Ham DMR ve TETRA
günlükleri önceki yerlerinde kalır. Bunlar Git'e eklenmez.
Tür günlüğündeki `tuning_changed: false`, yapılandırılmış frekansın ve donanım
ayarının değiştirilmediğini belirtir. Kanal başına sayısal RF takip düzeltmeleri
arşiv olay günlüğünde `RF takip` satırlarında ayrıca kaydedilir.

## Doğrulama

- Donanımsız testler: tekrarlı kanıt, CC değişimi, süre aşımı, CRC/FEC hatası,
  XPT yanlış pozitifleri, çelişen türler, gürültü/FSK reddi, analog ses → arşiv,
  dijital kanıtla analog kaydının kesilmesi, geç tamamlanan DMR WAV'ı, TETRA slot
  ve şifreli çağrı kapısı, UI Auto seçimi/ayar kaydı, USB öncesi çözücü açılışı,
  hata sonrası kaynakların kapanması ve tarama.
- Gerçek kurulu DSD-FME + TetraBridge ile kamuya açık DMR discriminator örneği
  yeniden I/Q üretilerek oynatıldı. Auto DMR tanıdı; üç korumalı DMR kaydı oluştu
  (11,16 / 5,76 / 2,16 sn), analog kayıt oluşmadı. USB açılmadı.
  Sonuç: `data/validation-auto/run-20260930-085557/validation.json`.
- Yerel P25 ve NXDN96 discriminator örnekleri analog sınıflandırıcıya verildi:
  iki saniyelik analog kabulü oluşmadı. Bu kapsamlı protokol doğruluğu kanıtı değildir.
- **Yeni Auto modu için canlı RF kabulü henüz yapılmadı.** TETRA ve XPT Auto
  tanıması olay/sinyal simülasyonuyla test edildi; gerçek TETRA/XPT Auto saha testi bekliyor.
  Aynı anda çok sayıda Auto kanalı için işlemci/USB yük testi henüz yapılmadı.

Değişiklik öncesi dosya yedeği:
`data/backups/auto-decode-20260930-085006/`.
