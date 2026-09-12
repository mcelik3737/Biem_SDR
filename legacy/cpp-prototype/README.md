# BİEM Radia Dispatcher (C++/Qt track)

> **Bu klasörün konumu hakkında:** repo kökü artık `src/biem_radia/`'daki
> Python tabanlı, donanımda doğrulanmış analog-FM MVP'yi barındırıyor.
> Bu C++ ağacı ona rakip değil, **tamamlayıcı, daha geniş kapsamlı bir
> ikinci hat**: DMR dijital çözme (FEC: Hamming/Golay/BPTC), Hytera
> repeater network entegrasyonu ve Qt6 masaüstü arayüzünü hedefliyor —
> bunların hiçbiri Python MVP'sinin kapsamında değil. İkisi de aktif
> tutuluyor; analog-only hızlı kullanım için repo kökündeki `README.md`'ye
> bakın.

Tek PC üzerinde çalışan, UHF/VHF telsiz trafiğini (analog FM + DMR dijital)
kaydeden, konuşma bazında loglayan ve tarih/başlık/ID/grup/slot kriterleriyle
aranıp dinlenebilen bir masaüstü dispatcher/logger uygulaması.

Kullanım senaryosu: BİEM'in hizmet verdiği firmaların **kendi izinli**
frekanslarındaki (lisanslı iş telsizleri + lisanssız PMR simpleks) telsiz
trafiğini İSG (iş sağlığı ve güvenliği) ve güvenlik amaçlı kayıt/log altına
almak — bkz. [Hytera Smart Dispatch Plus](https://www.hytera.com/eu/products/smart-dispatch-plus.html)
benzeri ürünler.

## İki ses/veri kaynağı

1. **SDR (RF üzerinden)** — Simpleks / lisanssız PMR ve repeater'a erişimi
   olmayan kanallar için: USB RTL-SDR dongle ile havadan I/Q örnekleme,
   ardından yazılımsal demodülasyon (analog NBFM, ve DMR dijital). Kanal
   aralığı: 6.25 kHz / 12.5 kHz / 25 kHz.
2. **Network / repeater modülü** — Repeater'a bağlı (örn. Hytera DMR)
   cihazlarda, konuşma + ID + Grup(Talkgroup) + Slot + GPS + SDS bilgisi
   doğrudan repeater'ın gönderdiği UDP trafiğinden okunur (RF demod'a gerek
   yok). İlk hedef cihaz: **Hytera HR659** (bkz. `docs/HYTERA_HR659.md`).

Her iki kaynaktan gelen çağrılar da aynı ortak `CallRecord` modeli ve aynı
kayıt/veritabanı/arama boru hattından geçer.

## Durum (özet — ayrıntı için `docs/ROADMAP.md`)

| Modül | Durum |
|---|---|
| Analog NBFM demodülasyon | ✅ Çalışır durumda (bu repo içinde derlenip test edilebilir) |
| Kayıt motoru (WAV) + SQLite log/arama | ✅ Çalışır durumda |
| DMR fiziksel katman (FEC: Hamming/Golay/BPTC) | ✅ Algoritmalar doğru, kendi içinde test edildi |
| DMR frame sync / senkron kelimeleri | ⚠️ ETSI TS 102 361'den web üzerinden doğrulandı (bkz. `docs/DMR_NOTES.md`) |
| DMR burst bit yerleşimi (Slot Type/EMB alan ofsetleri) | ⚠️ **DOĞRULANMADI** — gerçek sinyalle/spec ile çapraz kontrol gerekiyor |
| DMR ses (AMBE+2 vocoder) | ❌ Henüz yok — bkz. `docs/DMR_NOTES.md` (harici decoder entegrasyonu planlanıyor) |
| RTL-SDR donanım girişi (librtlsdr) | ✅ Kod yazıldı — bu sandbox'ta donanım/kütüphane yok, Windows'ta ilk gerçek derleme/test gerekiyor |
| UDP ham paket kaydedici (repeater trafiğini yakalamak için) | ✅ Çalışır durumda |
| Hytera HR659 UDP parser | ⏳ Stub — gerçek port/paket formatı bekleniyor |
| Qt6 masaüstü arayüzü | ✅ Kod yazıldı — bu sandbox'ta Qt6 yok, Windows'ta ilk gerçek derleme gerekiyor |

## Derleme

Bu repo Linux sandbox'ında **Qt6 ve librtlsdr olmadan** (`biem_core`,
`biem_cli`, `tests`) derlenip test edilmiştir — bkz. `docs/ROADMAP.md`
içindeki derleme/test çıktısı. Windows'ta tam GUI + donanım derlemesi için
bkz. **`docs/BUILD_WINDOWS.md`**.

```bash
cmake -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
ctest --test-dir build --output-on-failure
```

## Klasörler

```
src/
  core/     CallRecord, ChannelConfig, Database (SQLite), CallRecorder, WavWriter
  dsp/      IqSource arayüzü, WavIqSource, RtlSdrSource, NBFM demod, DMR (dsp/dmr/)
  net/      INetworkIngestSource, UdpRawLogger, repeater modülleri (net/hytera/)
  ui/       Qt6 masaüstü arayüzü (kanal listesi, çağrı logu/arama, oynatma)
  cli/      Qt'siz headless kayıt aracı (biem_cli) — sandbox'ta test için
docs/       Mimari, DMR notları, Hytera HR659 protokol notları, Windows build, yol haritası
tests/      FEC round-trip, NBFM sentetik ton, veritabanı CRUD/arama testleri
```

Ayrıntılı mimari için `docs/ARCHITECTURE.md`.
