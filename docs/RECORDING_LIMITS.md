# Kayıt ve TETRA tarama sınırları

Yeni arşiv kayıtları en fazla 90 saniyedir. Sınırdan sonra 2 saniye kayıt dışı
bırakılır; sinyal/ses devam ediyorsa yeni dosya oluşur. Doğal konuşma sonlarında
ek bekleme uygulanmaz. Eski kayıtlar değiştirilmez.

Analog: örnek sayısına göre tam 90 saniyede kapanır; iki saniyelik ara ön kayıt
tamponuna da girmez. TETRA: her slot ayrı, 1500 adet 60 ms ses çerçevesinde
kapanır; o slotun yeni kaydı en az iki saniye sonra başlar. Metadata toplanmaya
devam eder.

DMR/APCO25/NXDN: mevcut DSD-FME arayüzü WAV'ı çağrı sonunda teslim eder.
Arşive aktarımda 0–90, 92–182, 184–274... saniyeler ayrı dosyalara yazılır.
ID, grup ve slot bilgileri korunur. Bu dosyalar çağrı bitince görünür; çözücünün
`data/dmr-sessions` altındaki kaynak/teşhis WAV dosyaları bu sınırla kesilmez.
Bu dijital modlarda canlı 90 saniyelik dosya teslimi henüz uygulanmadı.

TETRA tarama: RF seviyesi yüksek olsa da çözülen açık ses yoksa 120 saniyede
sonraki kanala geçilir. Ses geldiğinde sessiz bekleme süresi sıfırlanır; kayıt
arası sırasında çözülen ses de ses etkinliği sayılır. Sabit alımda frekans atlamaz.

Erken kontrol kanalı geçişi: yerel TETRA parser sözleşmesindeki MAC Broadcast
SYSINFO bilgisi üç kez hatasız çözülmeli ve bildirilen ana taşıyıcı frekansı
dinlenen frekansla tam eşleşmelidir. Son iki saniyede ses yoksa tarama sürer.
Color code tek başına kontrol kanalı sayılmaz. Aynı taşıyıcıda daha sonra ses
başlaması mümkündür; tarama başka frekanstayken bu ses kaçabilir.
Karar ve metadata günlükleri `data` altında tutulur.

Doğrulama: sentetik örneklerle tam 90 saniye / iki saniyelik boşluk, arşivdeki
ses örnekleri ve tarih ofsetleri, tekrar içe aktarma, TETRA slot kayıt arası,
kontrol kanalı kanıtı ve güçlü sessiz taşıyıcıda 120 saniyelik tarama sınırı.
Canlı TETRA kontrol kanalı ve ses doğrulaması bekleniyor.
