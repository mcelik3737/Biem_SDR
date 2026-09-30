# DMR Tier III gözlemleri — 13 Eylül 2026

Bu belge saha gözlemi ve kullanıcı bildirimi kaydıdır. Kanal ayarlarını, çözücüyü, tarama davranışını veya kayıt veritabanını değiştirmez. Çalışan EXE'ye yeni özellik yüklendiği anlamına gelmez.

## 439.942 MHz

Etiket: **DMR Tier III kontrol bilgisi gözlendi — üretici bilinmiyor.**

Yerel çözücü günlüğünde tekrarlanan `C_ALOHA_SYS_PARMS`, `SLC_C_SYS_PARMS` ve `C_BCAST` sistem mesajları görüldü. CC 1; çözücü gösterimiyle Net ID 13, Site ID 1.2, SYS 2C01. Kullanıcının paylaştığı SLC satırında ayrıca Reg Req 1 ve CSC 395 vardı. Bu alanlar telsiz ID'si veya konuşma grubu olarak kaydedilmemelidir.

Dayanak oturum: `data/dmr-sessions/05fd990de81c4b738d69b15d023541d3/decoder.log`. Ham günlük özel çalışma verisidir, Git'e eklenmez. Hatalı CRC/FEC satırları da mevcuttur; gözlem temiz ve tekrarlanan sistem mesajlarına dayanır. Ağ/site gösterimi çözücünün yorumudur; bağımsız ağ yapılandırmasıyla doğrulanmamıştır.

Capacity Max, XPT veya belirli bir üretici doğrulanmadı. Anlaşılır ses, çağrı tahsisinden otomatik frekans takibi ve tüm sistem çağrılarının kaydı doğrulanmadı.

## 439.4189 MHz

Etiket: **DMR Tier III adayı — kullanıcı bildirimi, doğrulanmadı.**

Kullanıcı son yayınların Tier III olabileceğini, daha önce benzerini gördüğünü bildirdi. İncelenen oturum NXDN96 modunda çalışıyordu; kontrol paketleri CRC hatalıydı. Bu çıktı NXDN, Kenwood veya DMR Tier III için teknik doğrulama sayılmaz.

Dayanak oturum: `data/dmr-sessions/beda1255e3d043ca9c0fa5828319ab6e/decoder.log`. Önceki frekanstaki ağ/site bilgileri bu frekansa taşınmamalıdır.

## Ürün için etiketleme kuralı

- DMR, alım/çözüm modu olarak kalır; Tier III sistem türü bilgisidir.
- Kullanıcının bildirimi ile çözücüden gözlenen sistem türü ayrı gösterilmelidir.
- Yalnız `+DMR`, NXDN senkron metni veya CRC hatalı paketler sistem türünü doğrulamaz.
- Üretici kanıtı yoksa Motorola, Hytera veya Kenwood etiketi kullanılmaz.
- Sistem kontrol bilgisini okumak, ses çözmek ve çağrıyı başka frekansta takip etmek ayrı yeteneklerdir.
- Bu belgeyle otomatik ekran etiketi veya trunk takip özelliği uygulanmış değildir; sonraki geliştirmede bu ayrım korunacaktır.

## Araştırma

DMR Tier III, ETSI'nin trunking standardıdır. Markalar arası çalışma hedeflenir; uyumluluk belirli üreticiler, modeller ve zorunlu/isteğe bağlı özellikler için değerlendirilir. Her marka/modelin tüm özelliklerde otomatik uyumlu olduğu söylenemez.

- ETSI standartları: https://www.dmrassociation.org/dmr-standards.html
- DMR Association uyumluluk süreci: https://www.dmrassociation.org/dmr-iop-certification.html
- Uyumluluk sertifikaları: https://www.dmrassociation.org/iop-certificates-and-test-results.html
