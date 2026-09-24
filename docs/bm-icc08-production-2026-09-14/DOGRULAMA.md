# Rev A dosya doğrulama kaydı

14 Eylül 2026. Bu kayıt doküman ve hesap kontrolüdür; fiziksel cihaz kabulü değildir.

| Kontrol | Sonuç |
|---|---|
| Konsept dayanağı | `acef9c0d68a1ccac633cfda1e36ef89795c5400a` sürümündeki son ürün notları ve görünür isim güncellemesiyle uyum kontrol edildi. Önceki `9901504` sürümüne göre donanım kapsamını değiştiren fark bulunmadı. |
| PDF | 15 sayfa üretildi; sayfa görselleri kontrol edildi, satır/sütun ve kapak yerleşimleri düzeltildi. |
| Excel | 4 sayfa; bütçe, KDV, risk, adet, geliştirme ve depolama hesapları formüllüdür. Formül hata taraması 0 sonuç. |
| Hesap değişikliği | Risk girdisi %20 → %10 değiştirildi ve beklenen bütçe yeniden hesaplandı; teslimde %20 geri yüklendi. |
| Eksik lisanslar | Fiyatı girilmemiş lisans ücretsiz sayılmıyor; bir lisansa 0 girilse de diğer eksik teklifler toplamı kesinleştirmiyor. |
| Bağımsız toplam | JSON'dan hesaplanan 114.272,916 TL, Excel formül sonucuyla 0,01 TL içinde eşleşti. |
| Kaynaklar | Excel M sütunu hücre notlarında 32 doğrudan URL bulunuyor; PDF ve kaynak listesinde bağlantılar var. |
| DXF | 6 dosya ezdxf ile açıldı; birimler mm (`INSUNITS=4`), audit hatası/düzeltmesi 0. `HOLD` katmanı imalatçı onayı bekler. |
| Yerleşim | SVG çizimi render edilerek incelendi. Rack genişliği 360 + 2×61,3 = 482,6 mm; delik merkez aralığı 465,1 mm. |
| Marka | Orijinal logo dosyası bayt bazında aynı; SHA-256 `aa22a2fdd6d97985ff64e21c8d9f8f63df31e8f975a7cc807893512eb6e64305`. |
| Uygulama paketi | `python -m uv build` başarılı: sdist ve wheel üretildi. Bunlar donanım kabulü anlamına gelmez. |
| Windows kontrolü | `Check-Radia.ps1` bu Linux çalışma ortamında çalıştırılmadı. Windows'taki güncel uygulama/donanım ayrıca kontrol edilecek. |

Prototip montajı, gerçek alım, 4/8 RF kapasitesi, fan/RF gürültüsü, mekanik tolerans/yük ve EMC/RED deneyleri yapılmadı. OpenSCAD yerleşim modeli; nihai STEP montajı, numune konnektör kesitleri ve imalat serbest bırakma bu revizyonda onaylı değildir. Lisans veya tedarikçi teklifi alındığı iddia edilmez.

Çıktılar `bom.json`, PDF üreticisi ve mekanik üretici betiğiyle birlikte tutulur. Excel dosyasındaki fiyat/miktar/KDV girdileri düzenlenebilir; PDF tutarları bu revizyonun anlık görüntüsüdür.
