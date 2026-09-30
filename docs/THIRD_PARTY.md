# Third-party components

The BIEM application source is original project code. No license granting redistribution of BIEM code has been selected by the owner.

## RTL-SDR runtime

- Upstream: https://github.com/rtlsdrblog/rtl-sdr-blog
- Release: V1.4.0
- Download: https://github.com/rtlsdrblog/rtl-sdr-blog/releases/download/V1.4.0/Release.zip
- Downloaded ZIP SHA256: `7ef33f1304647f65e5e0fde43637a73d54f076e91e651a3cecc4f55a17fd9815`
- Local path: `vendor/rtl-sdr/package/x64/rtlsdr.dll`
- This runtime is GPL software; retain the corresponding upstream license/source information when preparing distribution. Current setup downloads the upstream runtime locally, and does not commit its binaries. Distribution licensing review remains a release task.
- The original SDR# installation is not modified. The optional TETRA adapter copies a small set of its locally provided libraries into the project's ignored vendor directory.

## SDR++ reference checkout

- https://github.com/AlexandreRouma/SDRPlusPlus
- Commit: `8c9f5ee8fe405775bfcd62c8c8f8c0fc928a64af` (verify against checkout; see command below).
- Local path: `external/SDRPlusPlus`
- License: GPL-3.0, see the checkout's `license` file.
- Its Windows source build guide requires CMake, vcpkg, PothosSDR, RtAudio and additional C++ dependencies. This reference application was cloned and inspected; it was not built or embedded into BIEM's first Python prototype.

```powershell
git -C external/SDRPlusPlus rev-parse HEAD
```

## Python

Runtime versions and development tools are resolved in `uv.lock`. NumPy and SciPy provide numerical filtering; Tkinter and SQLite are supplied with Python. WAV playback uses the Windows winsound API.

FM RADIO live output uses sounddevice/PortAudio, pinned in `uv.lock`.

## TETRA local bridge

`Setup-TETRA.ps1` copies the user's existing SDRSharp.Tetra, SDRSharp.Radio, SDRSharp.Common, tetraVoiceDec and shark libraries to `vendor/tetra`, records their SHA256 hashes, and compiles the original `native/TetraBridge.cs` adapter with the installed .NET Framework x86 compiler. No binaries are committed or redistributed by this repository. The adapter reads 96 kHz complex float I/Q and exports decoder events and 8 kHz PCM over local process pipes. Library versions with a different ABI fail explicitly. The API was inspected against [SDR-Tetra-Plugin](https://github.com/vgpastor/SDR-Tetra-Plugin); no decompiled upstream source was copied into BIEM.

The [SDR++ TETRA demodulator](https://github.com/cropinghigh/sdrpp-tetra-demodulator) was researched as another implementation; it is not the active backend. Redistribution rights for the locally supplied libraries and codec must be established before packaging a commercial installer.

## Selective squelch references

CTCSS and DCS are implemented on the original discriminator path. The DCS code/parity matrix and bit order were checked against [SDRangel's NFM DCS generator](https://github.com/f4exb/sdrangel/blob/master/plugins/channeltx/modnfm/nfmmoddcs.cpp). No SDRangel binaries or source files are shipped. Tests cover normal and inverted polarity, wrong tone rejection and continuous sample processing. RF acceptance is pending.

## Digital sample validation

APCO25 Phase 1 and NXDN96 were tested with [dsd-samples](https://github.com/szechyjs/dsd-samples) discriminator recordings through the pinned DSD-FME executable. The sample downloads and decoded audio stay under ignored `external`/`data` directories. See `DMR.md` for the DSD-FME runtime version and hash.


## Harita / Natural Earth
`assets/turkey-region.geojson`: Natural Earth 1:50m Admin 0 Countries verisinin Türkiye çevresindeki poligonları. Public domain. Kaynak: https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
Lisans: https://www.naturalearthdata.com/about/
Uygulama çalışma anında çevrimiçi harita servisi çağırmaz. Ülke ölçeğidir; sokak haritası değildir.


### Harita ayrıntıları
`assets/turkey-detail.json`: Natural Earth 1:10m Admin 1 States/Provinces, Populated Places ve Lakes kaynaklarından Türkiye için seçilen 81 il, 83 yerleşim noktası ve çevredeki 10 göl geometrisi. Kaynak URL listesi JSON içindedir; public domain. İl geometrileri genelleştirilmiştir; kadastro / sokak navigasyonu verisi değildir.


### Kullanıcının Google Maps uydu paketi
`D:/turkey/googlemaps.zip` içindeki 10 adet 256×256 JPEG yerel `data/map-import/googlemaps/` altında tutulur; Git/paket dağıtımına dahil edilmez. Dosyalarda EXIF konumu bulunmadı; `z/x/y.jpg` yolları XYZ Web Mercator konumlandırması için kullanılır. Yerel dosyalar dışında Google tile indirmesi yapılmaz. Koordinat referansı: https://developers.google.com/maps/documentation/javascript/coordinates
Pillow, JPG okuma ve mevcut enlem/boylam harita projeksiyonuna raster dönüşümü için eklendi.
