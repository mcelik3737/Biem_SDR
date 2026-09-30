# 30 Eylül 2026 — Hytera bağlantısı, ses kabulü ve röle durumu

Bu belge konuşmanın karar özetidir; birebir tam sohbet dökümü değildir.

## Kullanıcı talepleri ve kabul

- Hytera HR659 Ethernet üzerinden ses alımı/kaydını denemek.
- Kullanıcı denemeyi yaptı ve seslerin güzel geldiğini, işlemin başarılı olduğunu bildirdi.
- Sol menüde Hytera Ethernet yanında rölenin varlığını/bağlantısını ve varsa
  arızasını görmek. Ses kayıtları mevcut arşiv ekranında kalmalı.
- SNMP ile cihaz durumunu izlemek ve tarihli günlük tutmak.
- Kullanıcı CPS'te SNMP bildirimlerini açıp ayarları röleye yazdı; yeniden test istedi.

## Uygulanan sonuç

Ses kaydı iki slot için bağımsız IP Dispatch motorunda; arşivde kaynak
DMR/Hytera-IP. Yeni SNMP servisi ses ve SDR alımından bağımsız çalışıyor.
Sol menüde metin ve renk; Hytera sayfasında Durum ve olay günlüğü düğmesi var.
9 üretici alarm alanı, güncellik ve yerel saatli olaylar gösteriliyor.
SNMP izlemesi açık kaydedildiyse programın sonraki açılışında devam ediyor.

Gerçek cihaz 7 alanı normal, ileri/yansıyan güç alanlarını tanımsız bildirdi.
Tanımlı alanlarda aktif alarm gözlenmedi. Bu, cihazın her türlü arızadan uzak
olduğuna ilişkin genel onay değildir. Güncel veri yoksa eski normal durum
yeşil arıza onayı olarak kullanılmaz. Son pozitif alarm, yalnızca aynı alanın
normal bildirimiyle temizlenir; ilgisiz paketler alarmı temizlemez.

## Korunan kurallar

- SDR alım zinciri, frekans/kazanç/PPM, USB sürücüsü ve SDR# değiştirilmedi.
- SNMP salt okunur GET ve gelen Trap alımı; SET/reboot/RF gönderimi yok.
- XNMS erişim kodu tahmin edilmez, değiştirilmez, günlüğe yazılmaz.
- Bilinmeyen OID/değerler ham tutulur; volt, derece, koordinat veya dBm uydurulmaz.
- Ses durdurma ile cihaz durum izlemesi ayrıdır. Program kapanınca ikisi de kapanır.
- Yerel cihaz IP'leri, gerçek kimlik/çağrı verileri, kayıtlar ve günlükler Git'e girmez.
- Arıza simülasyonu donanımsız testtedir; gerçek rölede arıza yaratılmadı.
- Slot 2 gerçek konuşma kabulü hâlâ bekleniyor.

Ayrıntılar: [Hytera kullanım ve teknik notları](../HYTERA_ETHERNET.md),
[Doğrulama günlüğü](../VALIDATION.md).

## Aynı gün ek talep — sayısal değerler

Kullanıcı yalnızca normal/alarm yazısını değil, SNMP'de varsa voltaj gibi ölçüm
değerlerini de görmek istedi. Röle kısa süre kapalıydı; kullanıcı açtıktan sonra
13,99 V ve 28 °C canlı olarak alındı. Ana Hytera ekranına besleme, sıcaklık,
kaynak ve batarya özeti; durum tablosuna ölçüm sütunu eklendi. Değişen değerler
günlüğe yazılıyor. Eksik/geçersiz bilgi sayı olarak doldurulmuyor; her ölçümün
güncelliği ayrı tutuluyor. Harici ölçü aletiyle kalibrasyon yapılmadı.
