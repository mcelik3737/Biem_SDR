# Operasyon V2 — doğrulama kaydı

12 Eylül 2026. Bu kayıt **HTML tasarım prototipine** aittir. Radyo, gerçek kayıt, DPAPI, Windows UAC ve RF kabul testi değildir.

## Yapılan kontroller

- Chromium 153 / Playwright ile altı ana sayfa: canlı izleme, arşiv, harita, günlük, spektrum, kaynaklar.
- 1280×920, 1366×768, 1920×1080. Ayrıca %125/%150 ölçeklemenin kullanılabilir alanını temsil eden 1536×864, 1280×720, 1024×736, 853×613, 1093×614 ve 911×512 CSS viewport boyutları.
- Toplam **54 sayfa/boyut kontrolünde** belge ve ana sayfa yatay taşması yok; sabit alt durum çubuğu görünür; eksik ikon yok. Uzun içerik sayfa/table içinde kayar. Bu, gerçek Windows/Tk DPI testi yerine geçmez.
- 1920×1080’de altı kanal, sağ ayrıntı ve üç son kayıt görünür. 1366×768’de altı kanal görünür; ayrıntı paneli açılır, son kayıtlar aşağı kaydırılarak erişilir.
- **18 etkileşim senaryosu geçti:** kanal düzenleme kilidi; görünüm filtresinin alımı koruması; monitör sesinin kaydı koruması; özel hedef/çözücü kanalı; tarama/eski ölçüm; normal süreç arşiv listesi/dinleme kilidi; kimlik/tarih/slot filtreleri ve boş sonuç; yönetici dinleme görünümü/sesi kes; dosya çözme hatası; FM geçiş/gizleme/kapatma; beş protokolün ayar alanları; telsiz ikonunun ölçeği/alt orta koordinatı; boş/eski/eksik karo harita; yalnız yeni satırlara günlük filtresi; spektrum yetkisi/sahiplik/24 MHz/kilit/yeniden çizim; eksik/meşgul USB; Hytera ayar kaydı; tek HTML çevrimdışı görselleri/sayfaları.
- Senaryolarda JavaScript sayfa hatası **0**; HTTP(S) isteği **0**. Dış web bağlantısı yalnız BİEM bağlantısına kullanıcı tıklarsa açılır.
- `node --check` JavaScript kontrolü ve tek HTML üretimi başarılı. `python -m uv build` başarılı: bu tasarım dalının temelindeki **0.1.0** paketini üretir; yerel 0.2.0 derlemesi değildir.
- Logo, amblem ve telsiz dosyalarının yüklenen ZIP’teki dosyalarla byte eşitliği doğrulandı. Projeye gerçek ses, konum günlüğü veya karo arşivi eklenmedi.

## Gerçek uygulamaya kalan kabul

Bu Linux oturumunda `Check-Radia.ps1` / Windows Tk / UAC / DPAPI çalıştırılmadı. Kullanıcının brifindeki 71 donanımsız test ve 0.2.0 derleme sonucu yerel Codex raporudur; bu tasarım turunun yaptığı test olarak sunulmaz.

Özellikle gerçek kaydın 90/2 politikasıyla kapanması, DMR çağrı sonu import, TETRA kesintileri/kimlik ilişkilendirmesi, gerçek USB serbest bırakma, normal/yönetici RAM dinleme, konum doğrulama ve Windows %100/%125/%150 okunurluğu çalışan uygulamada ayrıca kontrol edilmelidir.

Önizleme örnek olayları dondurulmuştur; süreler/sinyaller bir alıcıdan akmaz. Bazı gelişmiş ayarlar yalnız yerleşim örneğidir. “Uygulandı” tasarım içi durumdur; donanım başarısı değildir. Üretim arayüzü bu durumları backend olaylarından almalıdır.
