# BIEM Radia development

- Canonical project directory is `D:\Projects\Biem\_SDR`.
- Preserve the user's SDR# installation at `D:\Depo\SDR\sdr-install\sdrsharp`; do not change its DLLs, configuration or Windows USB drivers without a specific need and authorization.
- The receive-only analog FM milestone takes priority over digital or transmitter features.
- Never populate radio ID, group, slot or caller aliases from guesses. Analog records keep those values NULL.
- Do not treat a simulated signal or captured RF noise as proof of successful intelligible over-the-air voice reception.
- Runtime recordings, logs, configuration and third-party binary checkouts stay outside Git.
- Run `Check-Radia.ps1` and `python -m uv build` for meaningful changes. The hardware-free test suite must not open a real SDR.
- Close the app gracefully before replacing a running receiver implementation; preserve unfinished audio files after crashes.
- Document whether a feature is implemented, simulated-tested, hardware-tested or awaiting user validation.
