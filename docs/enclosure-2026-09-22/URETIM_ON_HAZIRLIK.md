# BİEM Radio Integrated Solution — BM-ICC-08

## Türkiye'de kasa üretimi / Revizyon A — 22 Eylül 2026

Durum: ön tasarım ve teklif hazırlığı. Üretime hazır CAD, kesim dosyası veya verilmiş sipariş değildir. Mini PC, ekran, güç girişi ve konnektörlerin kesin modelleri henüz belirlenmedi. Aşağıdaki ölçüler ve malzemeler tasarım önerisidir; onaylı ürün özellikleri değildir.

Görsel referans: [BM-ICC-08 konsepti](../product-concept-2026-09-14/biem-bm-icc-08-concept.png). Konseptteki görünüm korunacak; üretim resmi bu görselden ölçü alınarak çıkarılmayacak.

## Önerilen yöntem

İlk numune için lazer kesim ve abkant büküm alüminyum gövde, vidalı sökülebilir üst kapak, ayrı işlenen düz alüminyum ön panel ve değiştirilebilir arka panel. Bu yöntem özel ekstrüzyon veya döküm kalıbı yaptırmadan özgün ölçü ve görünüm geliştirmeye olanak verir. Kalıp maliyetinin gerekli olup olmadığı seri üretim teklifleriyle değerlendirilir.

Konseptteki kalın ve sık soğutucu kanatlar sıradan sac bükümle aynı biçimde elde edilmez. İki seçenek:

1. İlk numunede düz yan yüzeyler ve ihtiyaca göre havalandırma; özgün görünümü ön panel, bordo vurgu ve kaplama taşır.
2. Görsele daha yakın sürümde iki yana hazır ekstrüzyon soğutucu profiller. Profil maliyeti ve bağlantıları ayrıca fiyatlanır. Isıl temas tasarlanmadan bu profillerin PC'yi soğuttuğu iddia edilmez.

Tek parça dolu alüminyumdan bütün gövdeyi CNC ile işlemek veya özel döküm kalıbı açmak ilk numune için öncelikli yaklaşım değildir; işleme/kalıp maliyeti teklif gerektirir.

## Başlangıç mekanik yapısı

| Kalem | Ön öneri | Kesinleştirme koşulu |
|---|---|---|
| Dış hacim | Yaklaşık 320 genişlik × 240 derinlik × 150 yükseklik mm; ayak ve konnektör çıkıntıları hariç | Mini PC, ekranın toplam modül boyutu ve kablo bükülme paylarıyla yerleşim |
| Alt şasi | 2 mm bükülebilir alüminyum; U kesit taban ve yanlar | Montaj yükü, rijitlik ve imalatçının takım/alaşım önerisi |
| Üst kapak | 1,5–2 mm alüminyum; vidalı sökülebilir | Açıklık, titreşim ve havalandırma tasarımı |
| Ön panel | Yaklaşık 3 mm düz alüminyum; CNC/lazer açıklıklar, çapak alma | Ekran ve düğme teknik resimleri; panelin rijitliği |
| Arka panel | 1,5–2 mm alüminyum, değiştirilebilir | Gerçek konnektörlerin delik ve somun/anahtar erişimi |
| Montaj tablası | Sökülebilir iç tabla ve ara parçalar | PC'nin montaj yöntemi; SDR'ler için ayrı sabitleme |
| Bağlantılar | Tekrarlı sökmeye uygun somun/uygun insert ve vidalar | İnce sacda doğrudan vida dişine güvenilmez; bağlantı üreticisi şartları |
| Ayaklar | Dört kaydırmaz ayak | Ağırlık merkezi ve alt hava boşluğu |

Bükülen parçalar için 5052-H32 değerlendirme adayıdır. Yerel stoktaki alternatif alaşım ve temperi imalatçı bildirmeli; büküm numunesiyle doğrulamalı. Ön panelin düz işlenmesi farklı alaşım kullanımına izin verebilir. İç büküm yarıçapı, minimum kenar, delik-büküm mesafesi ve açınım payı takım/malzeme seçilmeden sabitlenmez. [Üretici teknik rehberi](https://www.protocase.com/pdf/urc/URC-DESIGN-TIPS-2018.pdf).

Ön panel: BİEM kaynak logosu, ürün adı/model, güç düğmesi ve güç/kayıt/ağ göstergeleri. Ekranlı ve ekransız ön paneller aynı gövdeye takılabilir şekilde planlanacak. Ekran seçilmeden 7 inç köşegen üzerinden kesim yapılmayacak; dış ölçü, aktif alan, bağlantılar ve montaj delikleri birlikte kullanılacak.

Arka panel: RF1/RF2 için iki 50 ohm panel konnektörü (tip satın alınacak anten/kabloya göre), LAN, servis USB, seçilen beslemeye uygun DC giriş ve gerekli şasi bağlantısı. SMA/BNC/N gibi seçimler henüz kilitli değildir. RF kablosunun çekme yükü SDR üzerindeki küçük konnektöre aktarılmayacak; panel geçişi ve iç kablo sabitlenecek.

## İç yerleşim, ısı ve alım kalitesi

- SDR'ler, PC ve anahtarlamalı güç elemanlarından mümkün olduğunca ayrılacak. İç bölme için yer bırakılacak; bölme ve kablo geçişlerinin faydası ölçülerek değerlendirilecek.
- Fansız bir mini PC'yi kapalı ikinci metal kutuya koymak yeterli soğutma tasarımı değildir. PC'nin mevcut soğutucusunun hava yolu veya dış kasaya tasarlanmış ısı yolu korunmalı; seçilen PC'nin montaj ve ortam şartlarına uyulmalı.
- İlk numunede ölçüm sonrası fan eklemeye uygun değiştirilebilir havalandırma paneli düşünülebilir. Fansız/sessiz çalışma kabul testi yapılmadan vaat edilmez.
- Numunede uygun harici AC/DC adaptör yaklaşımı tercih edilir; seçilen donanıma göre voltaj ve akım kesinleşir. Konseptteki 12–24 V yazısı doğrudan üretim etiketine taşınmayacak.
- Kapak/şasi iletken temas bölgeleri boya veya eloksalla yalıtılmamalı; maskeleme ve gerektiğinde iletken conta tasarlanmalı. Metal kasa tek başına RF/EMC yeterliliğini kanıtlamaz.
- Kasa öncesi ve sonrası aynı anten, kazanç ve kanal şartlarında gürültü tabanı, çözücü hata oranı, USB örnek kaybı ve kayıt davranışı karşılaştırılacak. Ekran ve güç dönüştürücü açık/kapalı etkisi de ölçülecek.
- Kapağı açmak, SSD/SDR değiştirmek ve kablolara erişmek için RF/USB konnektörlerini zorlamak gerekmemeli.

## Dış görünüm

Gövde için mat grafit/siyah toz boya; ön panel için fırçalanmış naturel eloksal veya eşdeğer numune onaylı metal görünüm önerilir. Bordo vurgu ve kaynak BİEM logosu UV baskı, serigrafi veya uygun panel uygulamasıyla yapılabilir. Nihai renk/parlaklık bir yüzey numunesiyle seçilecek. Logo, yapay zekâ görselinden kopyalanmayacak; özgün marka dosyası kullanılacak. Montaj çiziklerini azaltmak için panel işlemlerinin sırası imalatçıyla belirlenecek.

## Türkiye'deki teklif adayları

22 Eylül 2026 tarihinde firmaların kendi siteleri incelendi. Aşağıdakiler doğrulanmış sipariş/kalite referansı değil; ilan edilen kabiliyetlere göre teklif adaylarıdır. Numune kabulü, minimum adet, fiyat ve termin için yazılı teklif alınmalı.

| Firma | Yer | Resmî sitede görülen kabiliyet | Bizim iş için rol |
|---|---|---|---|
| [Eco Metal](https://ecometlazer.com/) | Dudullu / Ümraniye, İstanbul | Alüminyum lazer kesim, CNC abkant, özel imalat; prototip/düşük adet çalışması | Büküm gövde ve panel parçaları; bitmiş kasa montajı/yüzey işleminin kapsamı sorulmalı |
| [ECK Metal](https://eckmetal.com/hakkimizda/) | Beylikdüzü, İstanbul | Elektronik metal kutu/kasa; 3D modelleme, lazer, abkant, toz boya | Mekanik tasarım ve bitmiş kasa için teklif; alüminyum alaşım/kalınlık ve 1 adet numune kabulü teyit edilmeli |
| [Altınkaya](https://www.altinkaya.com/tr/customization) | Ankara | Hazır elektronik kutular; CNC açıklık, UV baskı ve lazer markalama | Uygun ölçüde hazır kasa + BİEM ön/arka panel alternatifi; katalogdaki küçük profil kutuların tüm cihazı alacağı varsayılmamalı |

Eco Metal sitedeki iletişim: 0216 420 0886; Dudullu OSB Mah., DES Sanayi Sitesi 117. Sokak C-24 No:15, Ümraniye/İstanbul. [Kaynak](https://ecometlazer.com/).

Altınkaya sitedeki telefon: 0312 395 27 68. [Kaynak](https://www.altinkaya.com/tr).

ECK sitedeki e-posta: info@eckmetal.com. [Kaynak](https://eckmetal.com/hakkimizda/).

## Teklif ve numune sırası

1. Mini PC, SDR, ekran seçeneği, düğme ve panel konnektörlerinin teknik resimlerini toplamak; gerçek parçaların ölçüsünü doğrulamak.
2. Dış zarf ve iç yerleşim: kablo bükülmesi, montaj erişimi, ısı yolu ve ekran derinliği dahil 3D montaj hazırlamak.
3. İmalatçıyla büküm/bağlantı/yüzey işlemi incelemesi; STEP montaj, parça listesi, ölçülü PDF ve üreticiye uygun DXF açınımlarını tamamlamak.
4. Bir adet numune için ayrı tasarım, kesim-büküm, panel işleme, kaplama, baskı ve montaj bedeli istemek. 10 ve 50 adet için aynı kapsamla karşılaştırmalı fiyat istemek. Kesin fiyat/termin henüz yok.
5. Numunede montaj, ekran/düğme kullanımı, soğutma, alım kalitesi ve uzun süreli kayıt doğrulanınca revizyonu kapatmak. Boya/baskıdan önce kuru montaj kontrolü istemek.

Bu aşamada sipariş verilmedi ve firmalara mesaj gönderilmedi. Yazılım, alıcı ayarları ve SDR# kurulumu değiştirilmedi. Bu belge hazırlanırken kod/RF testi yapılmadı; mekanik üretim ve kabul testleri bekliyor.
