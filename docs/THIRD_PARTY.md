# Third-party components

The BIEM application source is original project code. No license granting redistribution of BIEM code has been selected by the owner.

## RTL-SDR runtime

- Upstream: https://github.com/rtlsdrblog/rtl-sdr-blog
- Release: V1.4.0
- Download: https://github.com/rtlsdrblog/rtl-sdr-blog/releases/download/V1.4.0/Release.zip
- Downloaded ZIP SHA256: `7ef33f1304647f65e5e0fde43637a73d54f076e91e651a3cecc4f55a17fd9815`
- Local path: `vendor/rtl-sdr/package/x64/rtlsdr.dll`
- This runtime is GPL software; retain the corresponding upstream license/source information when preparing distribution. Current setup downloads the upstream runtime locally, and does not commit its binaries. Distribution licensing review remains a release task.
- Existing SDR# binaries are not copied or modified.

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
