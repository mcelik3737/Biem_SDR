# Kanal kutuları ve modlar — 0.2.0

Canlı Kanallar ekranında altı düzenlenebilir kutu bulunur. Her kutuda etkinlik, ad, mod, frekans, erişim kodu ve dBFS eşiği ayarlanır. En az beş kutuya frekans girip `Kanalları kaydet` → `Tarama` → `Alımı başlat` ile 1 saniyelik gözlem süresi denenebilir. Kutular alım açıkken düzenlenmez; `Durdur` ile tekrar açılır. Boş frekanslar otomatik uydurulmaz. Altıncı kutu boş bırakılabilir.

Gösterge yalnız şu anda alınan kanalda güncel RF seviyesini gösterir. Diğer kanallar `Sırası bekleniyor` durumundadır. Tarama sırasında sinyal kanalın dBFS eşiği altına kesintisiz bekleme süresince düşene kadar kanal terk edilmez; ton uyuşmazlığı bu RF bekleme davranışını değiştirmez. Alıcı/çözücü yeniden açılması gözlem süresine eklenir; tur başına tam 5 saniye garantisi yoktur.

| Mod | Erişim / ton ayarı | Durum |
|---|---|---|
| Analog | CSQ, CTCSS 67–254,1 Hz, DCS, DCS-I | CSQ gerçek RF ses testi geçti; diğer tonlar sentetik sinyalle test edildi, RF testi bekliyor |
| DMR | Color code 0–15 veya boş | Gerçek RF ses ve metadata doğrulandı |
| TETRA | Color code 0–63 veya boş | Yerel I/Q demodülatör/codec köprüsü ve temiz kapanma test edildi; gerçek RF senkron/ses kabulü bekliyor |
| APCO25 | NAC, ondalık 0–4095 veya boş | Phase 1 C4FM örnek dosya ses/ID arşiv testi geçti; RF testi bekliyor |
| NXDN | RAN 0–63 veya boş | NXDN96 örnek dosya ses/ID testi geçti; NXDN48 ve RF testi bekliyor |

APCO25'te örneğin `0x293` NAC değeri ondalık `659` olarak girilir. NXDN48 için Gelişmiş Ayarlar bölümünde aralık/filtre 6250 Hz seçilir; NXDN96 12500 Hz kullanır. APCO25 Phase 2, otomatik trunk takip ve üretici IP repeater bağlantısı bu sürümde yoktur. Aynı ID/saniyede çakışan slot metadata'sı güvenle ayrılamıyorsa özgün DSD-FME dosyaları korunur, otomatik yanlış atama yapılmaz.

CTCSS doğru tonu seçerek ses kaydını açar. DCS normal, DCS-I ters polaritedir; birbirlerine otomatik çevrilmezler. Ton algılaması yaklaşık 0,5–0,6 saniyelik gözlem gerektirir ve kayıt başlangıcında kayıp olabilir. CSQ yalnız RF eşiğini kullanır. Eşik kalibre edilmiş dBm değildir.

## FM RADIO

Üstteki düğme paneli açıp kapatır. 88,5–108 MHz arasında 100 kHz adımla WFM mono dinlenir; ses kaydı oluşturulmaz. Ana telsiz alımı açıkken aynı USB alıcıyı kullanmak engellenir; FM RADIO dinlenirken de ana alım başlatılmaz. Paneli gizlemek sesi durdurmaz; `Kapat` sesi ve radyo alımını sonlandırır. Ayrı cihazı eşzamanlı seçme henüz yoktur. USB → WFM → ses çıkışı gerçek cihazda sessiz çıkışla test edildi; yayın sesinin kullanıcı tarafından dinleme doğrulaması bekliyor.

## TETRA sınırları

Yerel kurulum: `Setup-TETRA.ps1`. SDR# dosyaları değiştirilmez; ayrı x86 yardımcı süreç kullanılır. Sinyal π/4 DQPSK I/Q olarak işlenir, analog FM filtresine verilmez. Metadata kutuda gösterilir. Ses yalnız ilgili slot için yakın zamanda açık çağrı bilgisi doğrulanmışsa arşivlenir; şifreli veya durumu belirsiz çağrılar ses kaydı olarak içe alınmaz. Bu korumacı 2 saniyelik metadata süresi bazı açık çağrıları da kaçırabilir; RF testinde doğrulanmalıdır. SSI/GSSI çağrı ile güvenle eşlenmeden dosyaya kimlik yazılmaz. Dört slot ayrı tamponlarda tutulur. İki/dört gerçek eşzamanlı slot kabul testi henüz yapılmadı.

## Dosya adları

- Analog: `analog_2026-09-12_17_20_30_4.68sn.wav`
- DMR: `101_201_2026-09-12_17_20_30_4.68sn.wav` (cihaz ID, grup ID, tarih, saat, dakika, saniye, WAV süresi).
- Özel çağrıda grup yoksa grup alanı `bilinmiyor`; hedef cihaz ID'si arşivde ayrı alanda kalır.
- Tarih/saat PC yerel saatidir. Aynı ada sahip farklı kayıt çakışırsa `_02` gibi sayaç eklenir; dosya ezilmez.
- Önceki kayıtları dönüştürmek için `python -m biem_radia.rename_recordings --apply` kullanılır. Önce alımı kapatın. Veritabanı yedeği ve eski/yeni yol manifesti `data/backups` içine yazılır; ses baytları değişmez. Kesinti halinde bu manifest kurtarma içindir.
