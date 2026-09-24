"""Produce the BIEM RFQ/EVT technical package; source data lives beside this file."""
from pathlib import Path
import json, math
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parent
BOM=json.loads((ROOT/'bom.json').read_text())
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
for name,file in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
PW,PH=landscape(A4);M=36; CW=PW-2*M
NAVY=HexColor('#203449'); BURG=HexColor('#9c2942'); GRAY=HexColor('#657587'); LIGHT=HexColor('#eef1f4'); TEAL=HexColor('#247f78')
styles={
 'body':ParagraphStyle('body',fontName='D',fontSize=10.2,leading=14,textColor=NAVY,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='D',fontSize=8.4,leading=11.3,textColor=GRAY),
 'table':ParagraphStyle('table',fontName='D',fontSize=8.7,leading=11.5,textColor=NAVY),
 'head':ParagraphStyle('head',fontName='DB',fontSize=9,leading=12,textColor=white),
}
dest=OUT/'BM-ICC-08_Uretime_Hazirlik_RevA.pdf'
c=canvas.Canvas(str(dest),pagesize=(PW,PH));c.setTitle('BİEM BM-ICC-08 - Üretime Hazırlık / Rev A');c.setAuthor('BİEM proje çalışma dosyası')
page=0
def txt(x,y,text,size=11,bold=False,color=NAVY):
 c.setFillColor(color);c.setFont('DB' if bold else 'D',size);c.drawString(x,y,text)
def para(text,x,y,w,kind='body'):
 p=Paragraph(text,styles[kind]);_,h=p.wrap(w,1000)
 if y-h<40:raise RuntimeError(f'Page {page} content overflow: {text[:90]}')
 p.drawOn(c,x,y-h);return y-h-7
def table(headers,rows,widths,y,font=8.7):
 st=ParagraphStyle('local',parent=styles['table'],fontSize=font,leading=font+3)
 cells=[[Paragraph(escape(str(h)),styles['head']) for h in headers]]
 cells += [[Paragraph(str(v),st) for v in row] for row in rows]
 t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,LIGHT]),('LINEBELOW',(0,-1),(-1,-1),.5,HexColor('#c1cbd3'))]))
 _,h=t.wrap(CW,1000)
 if y-h<42:raise RuntimeError(f'Page {page} table overflow: {h:.1f}, available {y-42:.1f}')
 t.drawOn(c,M,y-h);return y-h-12
def new(title,kicker):
 global page
 if page:c.showPage()
 page+=1;c.setFillColor(white);c.rect(0,0,PW,PH,stroke=0,fill=1)
 txt(M,PH-29,'BİEM  /  RADIO INTEGRATED SOLUTION',9,True,GRAY)
 txt(PW-220,PH-29,'BM-ICC-08  ·  REV A',9,True,BURG)
 txt(M,PH-66,title,22,True);txt(M,PH-89,kicker,9.2,False,GRAY)
 c.setStrokeColor(BURG);c.setLineWidth(1.1);c.line(M,PH-104,PW-M,PH-104)
 c.setStrokeColor(HexColor('#d5dce2'));c.setLineWidth(.5);c.line(M,30,PW-M,30)
 txt(M,17,'14.09.2026 · RFQ / EVT · İmalat ve saha kabulü bekleniyor',8,False,GRAY)
 txt(PW-85,17,f'{page:02d}',9,True,GRAY)
 return PH-121
def money(v):return f'{v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')+' TL'
def link(url,text):return f'<link href="{escape(url)}" color="#155CC0">{escape(text)}</link>' if url else escape(text)
def front(x,y,scale=1,rack=False):
 c.saveState();c.translate(x,y);c.scale(scale,scale)
 if rack:
  c.setFillColor(NAVY);c.rect(-61.3,0,61.3,86,fill=1,stroke=0);c.rect(360,0,61.3,86,fill=1,stroke=0)
  c.setFillColor(white)
  for xx in [-52.55,412.55]:
   for z in [20.8,65.2]:c.roundRect(xx-4.5,z-5,9,10,3,fill=1,stroke=0)
 c.setFillColor(HexColor('#d9dde0'));c.setStrokeColor(HexColor('#8997a2'));c.rect(0,0,360,86,fill=1,stroke=1)
 c.setFillColor(BURG);c.rect(20,8,4,70,fill=1,stroke=0)
 c.drawImage(str(ROOT/'assets/biem-logo.png'),37,42,width=92,height=92*472/1505,mask='auto')
 txt(145,53,'BM-ICC-08',10,True)
 txt(37,37,'RADIO INTEGRATED SOLUTION',6.3)
 c.setFillColor(NAVY);c.circle(330,43,8,fill=1,stroke=0);txt(328.5,40.7,'I',5.8,True,white)
 for xx,col,n in [(250,TEAL,'PWR'),(275,BURG,'REC'),(300,HexColor('#387eae'),'LAN')]:
  c.setFillColor(col);c.circle(xx,23,2.3,fill=1,stroke=0);txt(xx-6,11,n,4.4)
 c.setFillColor(HexColor('#bdc7ce'));c.rect(182,17,36,20,fill=1,stroke=0);txt(186,10,'SERVİS',4.4)
 for xx in [6,354]:
  for z in [6,80]:c.setFillColor(GRAY);c.circle(xx,z,1.7,fill=1,stroke=0)
 c.restoreState()
def rear(x,y,scale=1):
 c.saveState();c.translate(x,y);c.scale(scale,scale);c.setFillColor(NAVY);c.rect(0,0,360,86,fill=1,stroke=0)
 for xx,r,n in [(35,4,'RF1'),(70,4,'RF2'),(112,10,'DC*'),(155,12,'LAN'),(200,12,'USB')]:
  c.setFillColor(HexColor('#c7a65e') if xx<100 else HexColor('#12212f'));c.setStrokeColor(HexColor('#a8b7c2'));c.circle(xx,43,r,fill=1,stroke=1);txt(xx-6,15,n,5,False,white)
 for xx in [250,320]:
  c.setFillColor(HexColor('#142330'));c.circle(xx,43,29,fill=1,stroke=0);c.setStrokeColor(GRAY)
  for r in [8,16,24]:c.circle(xx,43,r,fill=0,stroke=1)
 c.restoreState()
def iso():
 # Computed engineering assembly view, not a photograph or supplier rendering.
 ox,oy,s=70,210,1.10
 def p(x,y,z):return (ox+s*(x+.45*y),oy+s*(z+.23*y))
 for points,col in [([(0,0,86),(360,0,86),(360,260,86),(0,260,86)],'#343f4a'), ([(360,0,0),(360,260,0),(360,260,86),(360,0,86)],'#25313c')]:
  path=c.beginPath();path.moveTo(*p(*points[0]));[path.lineTo(*p(*v)) for v in points[1:]];path.close();c.setFillColor(HexColor(col));c.setStrokeColor(HexColor('#71818d'));c.drawPath(path,fill=1,stroke=1)
 front(ox,oy,s)
 c.setFillColor(NAVY)
 for xx in [28,310]:c.roundRect(ox+xx*s,oy-10*s,22*s,10*s,2,fill=1,stroke=0)
 for y in range(65,195,13):
  a=p(360,y,32);b=p(360,y,61);c.setStrokeColor(HexColor('#566370'));c.line(*a,*b)

net=sum(x['qty']*x['price']/(1.2 if x['vat_included'] else 1) for x in BOM['items']);gross=net*1.2;budget=gross*1.2;nre=sum(q*p for _,q,p in BOM['nre'])
y=new('Üretime hazırlık dosyası','Masaüstü kayıt cihazı · Sonradan rack dönüşümü · Türkiye tedarikli prototip')
para('Çalışan alıcı yazılımını bağımsız bir cihaza taşıyan, servis edilebilir metal gövde ve ölçülebilir kabul planı.',M,y,CW)
iso()
txt(630,378,'2U',29,True,BURG);txt(630,354,'sökülebilir kulaklar',10)
txt(630,315,'360 × 260 × 86',16,True);txt(630,294,'mm / ayak hariç',10)
txt(630,253,'2 × V3',19,True);txt(630,232,'bağımsız RF penceresi',9.5)
y=154
for x,big,small in [(M,'32 GB / 1 TB','Hazır Windows prototip'),(300,'4 → 8 RF','Kapasite test hedefi'),(568,'114.273 TL','Risk paylı prototip ödeneği')]:
 c.setFillColor(LIGHT);c.roundRect(x,y-62,238,63,5,fill=1,stroke=0);txt(x+13,y-24,big,15,True);txt(x+13,y-44,small,9.2)
para('Bütçe; malzeme, montaj, KDV varsayımı ve %20 pay içerir. Geliştirme/test ve fiyatı bilinmeyen ticari lisanslar ayrıca. Görünüş özgün mühendislik çizimidir; seri üretim serbest bırakma değildir.',M,77,CW,'small')

y=new('01 / Ürün mimarisi','Konsept notları korunur; mevcut durum ile hedef kapasite ayrı tutulur.')
rows=[['İşlem','GEEKOM IT13, tam kod GKM-MINI-IT13-G32-T1; i9-13900HK, 32 GB DDR4, 1 TB. Hazır PC modülü ilk prototipi hızlandırır.'],['Yazılım','Windows 11 Pro, mevcut kayıt motoru. Kayıt servisi oturumdan bağımsızlaştırılacak. Linux/web ve IoT OEM ayrı ürünleştirme işleri.'],['RF giriş','RF1/RF2, 50 ohm standart SMA; iki gerçek V3, kısa ekranlı USB. Her SDR kendi kabul edilen frekans penceresini işler.'],['Kayıt','Demodüle ses + tarih, kanal/title, kaynak, süre; DMR varsa doğrulanmış ID/TG/CC/slot. Bilinmeyen alanlar boş.'],['Yönetim','İlk prototipte yetkili LAN bakım oturumu ve mevcut GUI; bağımsız web konsolu hazır varsayılmaz. Servis HDMI/USB kurtarma için.'],['Sınır','Anten, UPS, ekran, LNA, splitter ve PoC lisansı ana pakette yok. 7 inç ekran ayrı 3U/harici çözüm.']]
y=table(['Alan','Tasarım kararı'],rows,[106,CW-106],y,10)
para('RF taşıyıcısı ile ses akışı farklıdır: 8 DMR taşıyıcısında iki slot kullanımı 16 eşzamanlı ses akışı doğurabilir. Tek SDR tüm VHF ve UHF bantlarını aynı anda göremez. Tarama, eşzamanlı kayıt sayılmaz.',M,y,CW)
para('Kaynak: proje konsepti; '+link(BOM['items'][0]['url'],'PC satıcı ürün kaydı')+'; '+link('https://www.rtl-sdr.com/wp-content/uploads/2018/02/RTL-SDR-Blog-V3-Datasheet.pdf','V3 resmi veri sayfası')+'. PC üreticisinin güncel IT13 Max sayfası farklı modele yönlendiği için model değişimi otomatik yapılmaz.',M,72,CW,'small')

y=new('02 / Ön panel ve rack dönüşümü','Özgün BİEM gövdesi; OEM hazır kasa panellerinden bağımsız tasarım.')
front(139,328,1.33,True)
txt(270,310,'482,6 mm toplam · 465,1 mm nominal rack merkez aralığı',9.3)
rear(139,157,1.33)
txt(139,140,'RF1   RF2     DC kablo geçişi*      LAN / USB          2 × 60 mm fan',9.4)
para('Kulaklar her yanda 4×M4 ve somun plakayla sökülür/takılır. Rack içinde raf/arka destek gerekir; ayaklar çıkarılır. 86 mm gövde ve rafın toplam düşey açıklığı hedef kabinde denenir.',M,111,CW)
para('* İlk prototip orijinal harici PC adaptörüyle çalışır. 12-24 V etiketi veya doğrulanmamış kilitli soket pinout’u kullanılmaz. Kesitler numune sonrası kesinleşir.',M,66,CW,'small')

y=new('03 / İç yerleşim ve servis','Sol RF bölmesi, sağ işlem modülü; çıkarılabilir iç tabla ve kapak.')
ox,oy,k=40,153,1.09
c.setStrokeColor(GRAY);c.setFillColor(HexColor('#f7f8fa'));c.rect(ox,oy,360*k,260*k,fill=1,stroke=1)
c.setFillColor(HexColor('#dde5eb'));c.rect(ox+30*k,oy+26*k,300*k,200*k,fill=1,stroke=0)
c.setFillColor(NAVY);c.rect(ox+208*k,oy+45*k,117*k,112*k,fill=1,stroke=0)
txt(ox+218*k,oy+103*k,'x86 PC',12,True,white)
for yy,n in [(83,'RF1 / V3'),(140,'RF2 / V3')]:
 c.setFillColor(HexColor('#a9b9c4'));c.rect(ox+43*k,oy+yy*k,105*k,35*k,fill=1,stroke=0);txt(ox+53*k,oy+(yy+14)*k,n,10)
c.setFillColor(GRAY);c.rect(ox+178*k,oy+40*k,k,185*k,fill=1,stroke=0)
for xx in [250,320]:
 c.setFillColor(HexColor('#a99277'));c.rect(ox+(xx-30)*k,oy+231*k,60*k,25*k,fill=1,stroke=0)
txt(45,136,'Ön → altta / arka → üstte · 360 × 260 mm',9)
yy=y
for p in ['<b>PC hacmi:</b> 117 × 112 × 49,2 mm; Z=12 mm başlangıcı. Üstte yaklaşık 22,8 mm boşluk. Kendi fanı ve soğutucusu korunur.', '<b>RF alıcı:</b> her V3 için 105 × 35 × 22 mm ayrılan hacim; kesin ürün ölçüsü değildir. Ayarlı kelepçe, kısa SMA kablo ve çıkarılabilir bölücü.', '<b>Servis:</b> 300 × 200 mm iç tabla, soketli kablolar. SSD/SDR değişimi için ana gövde sökülmez. Konnektörlere mekanik yük bırakılmaz.', '<b>Hava:</b> giriş menfezi → PC → arka fanlar. Sıcak çıkışın girişe dönmesi ve RF bölümüne USB/SMPS paraziti ölçülür.']:
 yy=para(p,468,yy,334)
para('Yerleşim modeli ve DXF’ler mechanical/ klasöründedir. PC port yönleri, braketler ve güç aktüatörü numuneyle DFM kontrolünden geçer.',M,86,CW,'small')

y=new('04 / Malzeme ve imalat yöntemi','İlk numune boyasız uyum kontrolü; sonraki revizyonda yüzey ve baskı.')
rows=[['C01','U şasi','360 × 254 × 84; 2 mm Al 5052-H32','İki 90° büküm; R2/K0,33 başlangıç, deneme bükümü gerekli.'],['C02 / C03','Ön / arka','360 × 86; 3 mm Al 5005','Konnektör kesitleri HOLD; ön naturel/saten, arka grafit.'],['C04','Üst kapak','360 × 254; 2 mm Al 5052-H32','6 sökülebilir M3 bağlantı, iç L braket.'],['C05 L/R','Rack kulak','61,3 ön kanat, 60 dönüş, H86; 3 mm çelik','Somun plakalı 4×M4/yan; 9×10 oval rack delikleri.'],['C06','İç tabla','300 × 200; 2 mm Al','6 yükseltici, ayarlı tutucu slotları; PC kasası delinmez.']]
y=table(['Kod','Parça','Ölçü / malzeme','Proses'],rows,[53,95,245,CW-393],y,9.3)
y=para('Gövde RAL 7024 grafit görsel hedef; ön panel saten metal ve sınırlı bordo. Logo oranları korunur. Kaplama öncesi panel bağlama yüzeyleri maskelenir; kısa örgü bağlantılar ve yıldız pullar kullanılır.',M,y,CW)
y=para('Dış ölçü hedefi ±0,5 mm; büküm açısı ±0,5°; keskin kenar kırma 0,3-0,5 mm. Tolerans ve torklar gerçek malzeme/kaplama/bağlantı elemanıyla imalatçı tarafından kesinleştirilir.',M,y,CW)
para('Hazır yedek: '+link('https://www.altinkaya.com/tr/products/19-2u-rack-tipi-aluminyum-kutu-2440','Altınkaya RM-120-360')+'; sökülebilir kulak koşulu yazılı teyit edilir. '+link('https://www.hammfg.com/electronics/small-case/rack-mount/rm','Hammond RM serisi')+' sökülebilir kulak sunar. Bu kasaların panel ölçüleri farklıdır; BİEM DXF’leri onlara doğrudan kesilmez.',M,y,CW,'small')

y=new('05 / Elektrik, RF ve fiziksel göstergeler','Prototipte orijinal adaptör korunur; çalışma anı durumları yazılımdan alınır.')
rows=[['RF1 / RF2','SMA dişi panel → RG316 25-30 cm → V3 → ayrı USB veri portu. 50 ohm ve normal SMA; RP-SMA alınmaz. Bias tee varsayılan kapalı.'],['DC güç','Harici orijinal adaptör → kesilmeyen kablo geçişi → PC. Etiket gerilimi/akımı/polaritesi numuneden doğrulanır. Şebeke gerilimi kasa içine alınmaz.'],['Soğutma','2 × NF-A6x25 5V; 0,26 A/adet azami. Her fan uygun 5 V USB güç kaynağında; USB-C adaptörü 5 V için doğru CC sonlandırmasına sahip olmalı.'],['Port bütçesi','İki SDR tipik toplam 0,56 A; iki fan azami 0,52 A; LED kartı ayrıca. Port ve ortak kök hub akım sınırları ile IQ kayıpları birlikte test edilir.'],['LAN / servis','Ekranlı panel geçişi + kısa CAT6 patch; USB panel ve servis HDMI. LAN konnektörünün PoE kabiliyeti bu cihazı PoE beslemeli yapmaz.'],['LED / düğme','RP2040 USB heartbeat; PWR = servis sağlığı, REC = gerçek arşiv yazımı, LAN = yerel link/IP. Mekanik güç aktüatörü PC’nin gerçek düğmesine basar.']]
y=table(['Bölüm','Bağlantı / davranış'],rows,[105,CW-105],y,9.3)
para('Fan gücü yetersizse ayrı sertifikalı 5 V besleme seçilip güç/RF testleri tekrarlanır. Kilitli DC giriş; gerilim, akım, temas direnci ve kablo kesiti onayından sonra ayrı imalat revizyonudur. Bakım bağlantısı işlevsel şasi bağlantısıdır; koruma sınıfı test olmadan belirtilmez.',M,y,CW,'small')

for block in range(3):
 y=new(f'06.{block+1} / Malzeme ve tedarik listesi',f'BOM {block*10+1:02d}-{block*10+10:02d} · Liste fiyatı ile plan ödeneği farklıdır.')
 rows=[]
 for x in BOM['items'][block*10:(block+1)*10]:
  price=money(x['price'])+'<br/>'+('KDV dahil' if x['vat_included'] else '+ KDV')
  rows.append([x['id'],escape(x['part']),str(x['qty']),price,escape(x['price_basis']),link(x['url'],x['supplier']),escape(x['availability'])])
 y=table(['Kod','Parça / tam kod','Adet','Birim tutar','Tutar türü','Tedarik kanalı','Stok / teklif'],rows,[37,188,43,89,75,155,CW-587],y,8.2)
 para('Tam teknik şart, alternatif ve plan terminleri bom.json / Excel ile TEDARIK_VE_RFQ.md dosyasındadır. “Ödenek” gerçek fiyat teklifi değildir. İthal muadilde kargo, gümrük ve vergi ayrıca hesaplanır.',M,y,CW,'small')

y=new('07 / Bütçe ve nakit planı','14 Eylül TL gözlemleri; KDV %20 varsayımı; bir prototip ve ürünleştirme ayrı.')
rows=[['Bir prototip malzeme + montaj / net',money(net)],['Varsayımsal KDV',money(gross-net)],['Bir prototip / KDV dahil',money(gross)],['%20 risk payı',money(gross*.2)],['Önerilen prototip ödeneği',money(budget)],['Bir defalık ürünleştirme / test net ödeneği',money(nre)],['Bir defalık ürünleştirme / test brüt ödeneği',money(nre*1.2)],['AMBE / TETRA / IoT OEM','Fiyat bilinmiyor; ticari toplam eksik']]
y=table(['Kalem','Tutar / durum'],rows,[CW-265,265],y,10)
y=para('Ürünleştirme ödeneği: 43 adam-gün × 6.500 TL + 35.000 TL ön uygunluk + 100.000 TL nihai test ödeneği = 414.500 TL net. Bunlar alınmış hizmet teklifleri değildir; BİEM iç kaynakları ve laboratuvar kapsamıyla değiştirilir.',M,y,CW)
para('Excel toplam plan adedini 10 olarak başlatır; ilk prototip bu adedin içindedir. Adet indirimi varsayılmadan risk paylı cihaz ödeneği 1.142.729,16 TL; bir defalık brüt ürünleştirme ile 1.640.129,16 TL plan tutarıdır. Ticari lisanslar hâlâ hariçtir. Bu rakam satış fiyatı değildir.',M,y,CW,'small')

y=new('08 / Hızlı tedarik ve prototip takvimi','Parça doğrulaması sürerken mekanik teklif paralel ilerler.')
rows=[['1','PC ve ilk V3','PC listesinde stokta var; V3 sepete açık. 1-3 iş günü teslim hedefi, satıcıdan teyit. Mevcut PC ile ilk V3 testi hemen planlanabilir.'],['2','Kasa / rack / tabla','Özgün kasa için 1 numune ve 10 adet teklif. 7-12 iş günü numune hedefi; onaylı CAD ve parça numunesi ön koşul.'],['3','Kablo / panel / fan','Normal SMA, kısa USB, Neutrik, 5 V fan. Fan ve panel geçişleri termin riski; yerel muadiller ayrı test ister. Pico listesinde tükendi.'],['4','Montaj / ilk alım','Parçalar geldikten sonra yaklaşık 2 iş günü montaj + güç/USB/PPM kontrolü. Boyasız mekanik uyum numunesi önce.'],['5','Servis ve iki SDR','2-4 hafta başlangıç yazılım rezervi; fault izolasyonu ve oturumsuz çalışma; RF yük testi kapıları.'],['6','EVT → pilot','8-12 hafta ürünleştirme başlangıç planı; lisans ve laboratuvar kuyruğu süreyi değiştirebilir. Kabul olmadan ticari kapasite ilan edilmez.']]
y=table(['Sıra','İş','Sonuç ve bağımlılık'],rows,[36,137,CW-173],y,9.4)
para('Hazır RFQ taslakları: PC, RF alıcı/kablo, özgün kasa, Neutrik/fan, DVSI, TETRA/OEM/laboratuvar. Sipariş/ödeme/tedarikçi mesajı yapılmadı. Firma proforması, KDV, gerçek ürün revizyonu ve teslim tarihi geldiğinde Excel güncellenir.',M,y,CW)

y=new('09 / Lisans ve ticari ürün yolu','Telif lisansı, vokoder hakkı, Windows OEM ve cihaz uygunluğu birbirinden ayrıdır.')
rows=[['BIEM + rtl-sdr','BIEM dağıtım lisansı seçilmemiş. GPL DLL bağlama ve karşılık gelen kaynak yükümlülükleri değerlendirilir. Ayrı süreç veya sonradan indirme otomatik çözüm değildir.'],['DSD-FME + Cygwin','DSD-FME COPYRIGHT karma bileşenler içerir; tek ISC/MIT etiketi yeterli değil. Cygwin API güncel metinde LGPL-3.0-or-later + istisna; yardımcı paketler ayrı.'],['AMBE / mbelib','ISC telif metni, ticari teknoloji hakkıyla aynı değildir. DVSI’den 8/16 decode akışı için SDK/donanım, NRE, birim royalty, offline ve yeniden dağıtım teklifi.'],['TETRA','Yerel DLL’nin kökeni/hak sahibi/sürümü ve ticari izin henüz doğrulanmadı. Ticari çıkış kapısı; ücret bilinmiyor.'],['Windows','Prototip PC’de Win11 Pro paketi; fatura/lisans kanıtı istenir. Yeni BIEM cihazlarında IoT OEM sözleşmesi ve imaj/aktivasyon hakları dağıtıcıyla.'],['Kendi ürün lisansı','Öneri: tek cihazda offline kalıcı çekirdek, test edilmiş RF/voice limitleri ayrı. Destek yenilememek kaydı durdurmaz; SSD değişiminde kontrollü yeniden bağlama.']]
y=table(['Bileşen','Karar / yapılacak iş'],rows,[120,CW-120],y,9.1)
para('Ayrıntı ve kaynaklar: LISANS_VE_UYGUNLUK.md. '+link('https://github.com/lwvmobile/dsd-fme/blob/audio_work/COPYRIGHT','DSD-FME')+' · '+link('https://www.cygwin.com/licensing.html','Cygwin')+' · '+link('https://www.dvsinc.com/products/price.shtml','DVSI')+' · '+link('https://learn.microsoft.com/en-us/windows/iot/iot-enterprise/commercialization/licensing','Microsoft')+'. Dağıtılan kesin sürümün SBOM, hash, bildirim, kaynak/build ve recovery dosyaları hazırlanır.',M,y,CW,'small')

y=new('10 / Son ürün uygunluğu ve veri güvenliği','Türkiye iç pazarı ilk kapsam; işaretler ve iddialar nihai kombinasyonla doğrulanır.')
rows=[['Kapsam görüşü','Telsiz alıcı cihazının Türkiye/RED kapsamı ve uygulanabilir standart sürümleri laboratuvarla yazılı belirlenir.'],['EMC / RF / güvenlik','PC + 2 SDR + kasa + adaptör + kablo kombinasyonu test edilir. Parçaların CE işareti birleşik ürünü otomatik onaylamaz.'],['Teknik dosya','BOM, çizim/bağlantı, risk değerlendirmesi, seri-sürüm izlenebilirliği, raporlar, Türkçe kullanım/servis, imalatçı beyanı.'],['Etiket','Ürün/model/seri, gerçek güç değeri, üretici ve servis bilgisi. CE, IP veya sıcaklık sınıfı test öncesi basılmaz.'],['Kayıt verisi','Müşteri bazlı amaç, hukuki dayanak, aydınlatma, yetki, saklama/silme, erişim logu. İzinli frekans kullanımı bu işlemleri otomatik tamamlamaz.'],['Anahtar / recovery','DPAPI servis hesabı ve disk değişimi senaryosu; geçici decoder WAV/raw log dahil erişim koruması. “Yalnız bizim program açar” garantisi verilmez.'],['Çevre / ihracat','Uygulanabilir RoHS/AEEE ve üretici/ambalaj kayıtları uzman teyidi. Başka ülkeye satış ilave mevzuat işi doğurur.']]
y=table(['İş','Üretime çıkış çıktısı'],rows,[137,CW-137],y,9.2)
para('EN 300 113/EN 300 086, EN 301 489 ailesi, EN IEC 62368-1 yalnız laboratuvar görüşmesinin aday başlıklarıdır. Kaynak: '+link('https://www.btk.gov.tr/en/radio-equipment-directive-red','BTK RED')+' · '+link('https://www.btk.gov.tr/en/market-surveillance-and-supervision-frequently-asked-questions','BTK SSS')+' · '+link('https://www.kvkk.gov.tr/','KVKK')+'.',M,y,CW,'small')

y=new('11 / Depolama, ısı ve kapasite hesabı','Ölçüm öncesi açık varsayımlar; Excel girdileri değiştirilebilir.')
rows=[['PCM ses','16 kHz × 16 bit × mono = 32.000 byte/s = 2,7648 GB/gün/akış.'],['1 TB / 8 ses','%20 disk rezervi ve %10 arşiv ek yüküyle yaklaşık 32,9 gün, sürekli konuşma varsayımı.'],['1 TB / 16 ses','Aynı koşullarda yaklaşık 16,4 gün. 30 gün için yaklaşık 1,825 TB nominal alan gerekir; model/SSD yeniden seçilir.'],['Ham IQ','2 × 2,4 MS/s × 8-bit I/Q = 9,6 MB/s, yaklaşık 829,4 GB/gün. Sürekli IQ, normal ses arşivi değildir.'],['90 + 2 saniye','Gerçek 2 saniye boşluk korunursa zaman oranı %97,83. Bu davranış “kesintisiz kayıt” olarak adlandırılmaz; boşluksuz rotasyon ayrı gereksinimdir.'],['Örnek ısı hesabı','70 W tahmini yük, 10 °C hava artışı, 1,2 kg/m³ ve 1005 J/(kg·K) ile ideal yaklaşık 20,9 m³/saat. İki fan serbest hava toplamı 58,4 m³/saat; gerçek kasa debisi ölçülür.']]
y=table(['Hesap','Varsayım / sonuç'],rows,[132,CW-132],y,9.4)
para('70 W ölçülmüş tüketim değildir. CPU turbo sınırları, port güçleri, fan/filtre kayıpları ve ortam sıcaklığıyla yük testi gerekir. 4/8 RF yükünde CPU p95 <= %70, USB kaynaklı kayıp 0 ve kapalı kasada RF gürültü artışı <=3 dB proje kabul hedefleridir; mevcut performans iddiası değildir.',M,y,CW)

y=new('12 / Kabul, yazılım işleri ve teslim kapıları','Her kabul kaydı gerçek donanım, yazılım hash’i ve tarih ile tutulur.')
rows=[['K1','Tek V3 / kalibrasyon','30 dk ısınma, referans RF ile Hz/ppm; taşıyıcı ofseti ve osilatör hatası ayrılır. Analog regresyon.'],['K2','İki SDR / servis','Oturumsuz kayıt, kalıcı kaynak kimliği; 20 USB çıkar-tak çevriminde diğer alıcı kesilmez.'],['K3','4 RF → 8 RF','4 RF / 24 saat; sonra 8 RF / 72 saat ve DMR için 16 ses senaryosu. Bilinen ID/TG/CC/slot ile en az 100 çağrı.'],['K4','Fault / veri','20 kontrollü güç kesintisi, 30 dk ağ kesintisi, disk dolu/yazma hatası, kurtarma ve rol testleri.'],['K5','Kasa / üretim','Kapalı kasa termal/RF testi, raf destekli rack montajı, kablo tutma, numune toleransı, etiket/recovery/FAT.'],['K6','Ticari sevk','Kesin SBOM ve kaynak/bildirim paketi; AMBE/TETRA/Windows hakları; nihai uygunluk dosyası ve imalatçı çıkış onayı.']]
y=table(['Kapı','İş','Kabul çıktısı'],rows,[44,126,CW-170],y,9.3)
y=para('DSD-FME çağrı dosyası mevcut yolda çağrı bitince içeri alınıyor; 90 saniyede canlı parça teslimi varsayılmaz. TETRA sessiz taşıyıcı için yeni 20 saniye notu, eski 120 saniye davranışıyla kod üzerinde çözülür. UI kapatmak kaydı durdurmamalıdır.',M,y,CW)
para('Teslim: teknik PDF, formüllü Excel, 6 DXF, parametrik OpenSCAD, ölçülü SVG, BOM JSON, lisans matrisi, RFQ taslakları ve Codex iş listesi. Bu çalışmada yazılım motoru değiştirilmedi; donanım testi yapılmadı. Kaynak ve ayrıntılar aynı proje klasöründedir.',M,y,CW,'small')
c.save()
print(f'{page} pages written: {dest}')
