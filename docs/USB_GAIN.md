# USB tuner gain

Live Channels offers manual gain, Tuner AGC, +10 dB and Apply. Changes run on
receiver worker between IQ blocks; the actual supported manual step is displayed.
Tuner AGC uses rtlsdr_set_tuner_gain_mode(0), manual mode uses (1). This is tuner
AGC, not RTL2832 digital AGC or playback volume. FM RADIO is excluded from live
updates. Settings persist in data/receiver.json. Scanning retains updated settings.

Hardware verification: local E4000 supports -1, 1.5, 4, 6.5, 9, 11.5, 14, 16.5,
19, 21.5, 24, 29, 34, 42 dB. Manual 29 dB, tuner auto, back to manual 29 dB
all returned success, 16384 IQ samples received, device closed cleanly.
Saved user setting raised from 19 to 29 dB. Voice quality improvement requires
comparison on a real transmission. Gain raises noise too; reduce if overloaded.

Hardware-free test verifies mode commands, supported-step rounding and return
from auto to manual. No SDR# installation or driver was changed.
