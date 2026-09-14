"""BIEM original RFQ/EVT geometry. mm units; HOLD is never a released cut layer."""
import base64
from pathlib import Path
from math import pi
import ezdxf
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
W, D, H = 360.0, 260.0, 86.0

def doc(name):
    d = ezdxf.new('R2010')
    d.units = 4
    for layer, color in [('CUT',7),('BEND',4),('HOLD',30),('TEXT',3)]:
        d.layers.new(layer, dxfattribs={'color':color})
    return d, d.modelspace(), OUT / name

def rect(m,x,y,w,h,layer='CUT'):
    m.add_lwpolyline([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],close=True,dxfattribs={'layer':layer})

def hole(m,x,y,r,layer='CUT'):
    m.add_circle((x,y),r,dxfattribs={'layer':layer})

def label(m,s,y=-12):
    m.add_text(s,dxfattribs={'height':3,'insert':(0,y),'layer':'TEXT'})

def slot(m,x,y,width,height,layer='CUT'):
    r=width/2; z=(height-width)/2
    m.add_line((x-r,y-z),(x-r,y+z),dxfattribs={'layer':layer})
    m.add_line((x+r,y-z),(x+r,y+z),dxfattribs={'layer':layer})
    m.add_arc((x,y+z),r,0,180,dxfattribs={'layer':layer})
    m.add_arc((x,y-z),r,180,360,dxfattribs={'layer':layer})

def panel(name):
    d,m,p=doc(name);rect(m,0,0,W,H)
    for x in [6,354]:
        for z in [6,80]:hole(m,x,z,1.7)
    return d,m,p

d,m,p=panel('C02_front.dxf')
hole(m,330,43,8,'HOLD')
for x in [250,275,300]:hole(m,x,23,3,'HOLD')
rect(m,182,17,36,20,'HOLD')
label(m,'C02 FRONT / Al 5005 t3 / REV A RFQ-EVT / HOLD: SAMPLE APPROVAL REQUIRED')
d.saveas(p)
d,m,p=panel('C03_rear.dxf')
for x in [35,70]:hole(m,x,43,3.25,'HOLD')
for x in [155,200]:
    hole(m,x,43,12,'HOLD')
    hole(m,x-9.5,55,1.65,'HOLD');hole(m,x+9.5,31,1.65,'HOLD')
hole(m,112,43,10,'HOLD');hole(m,130,18,2.25)
for x in [250,320]:
    hole(m,x,43,29)
    for dx in [-25,25]:
        for dz in [-25,25]:hole(m,x+dx,43+dz,2.15)
label(m,'C03 REAR / Al 5005 t3 / 5V FANS 50x50 PITCH / CONNECTORS ON HOLD')
d.saveas(p)
d,m,p=doc('C04_top.dxf');rect(m,0,0,360,254)
for x in [8,352]:
    for y in [20,127,234]:hole(m,x,y,1.7)
label(m,'C04 TOP / Al 5052-H32 t2 / 6 INTERNAL ANGLE BRACKETS REQUIRED / REV A')
d.saveas(p)
d,m,p=doc('C06_carrier.dxf');rect(m,0,0,300,200)
for x in [8,150,292]:
    for y in [8,192]:hole(m,x,y,1.7)
for x in [20,120,174,290]:
    for y in [28,95,145]:slot(m,x,y,3.5,18)
label(m,'C06 CARRIER / Al t2 / SLOT POSITIONS FOR ADJUSTABLE CLAMPS / REV A')
d.saveas(p)
BA=pi/2*(2+.33*2);BD=2*(2+2)-BA;flat=360+2*84-2*BD;bl=84-4+BA/2
d,m,p=doc('C01_tray_flat_review.dxf');rect(m,0,0,flat,254)
for x in [bl,flat-bl]:m.add_line((x,0),(x,254),dxfattribs={'layer':'BEND'})
for z in [20.8,65.2]:
    for y in [17,47]:
        hole(m,84-z,y,2.25);hole(m,flat-(84-z),y,2.25)
for z in [74]:
    for y in [20,127,234]:
        hole(m,84-z,y,1.7);hole(m,flat-(84-z),y,1.7)
# Planned inlet ventilation; open area is a thermal-test input, not an IP claim.
for side in [0,1]:
    for y in range(70,181,10):
        x=35 if side==0 else flat-40
        rect(m,x,y,5,5)
label(m,f'C01 FLAT REVIEW / Al t2 R2 K0.33 / BLANK {flat:.3f} x 254 / 2 BENDS 90 DEG')
label(m,'TRIAL BEND AND INTERNAL BRACKETS MUST BE APPROVED BEFORE CUT RELEASE',-18)
d.saveas(p)
BA=pi/2*(3+.33*3);BD=12-BA;eflat=61.3+60-BD;eb=61.3-6+BA/2
d,m,p=doc('C05_ear_flat_review.dxf');rect(m,0,0,eflat,86)
m.add_line((eb,0),(eb,86),dxfattribs={'layer':'BEND'})
for z in [20.8,65.2]:
    slot(m,8.75,z,9,10)
    for y in [20,50]:hole(m,61.3-BD+y,z,2.25)
label(m,f'C05 EAR L/R / STEEL t3 R3 K0.33 / BLANK {eflat:.3f} x 86 / MIRROR BEND')
label(m,'RACK SLOT PITCH TARGET 465.1 / REAR SHELF SUPPORT / TRIAL BEND REQUIRED',-18)
d.saveas(p)

scad='''// BIEM BM-ICC-08 original RFQ/EVT Rev A. Not released manufacturing CAD.
// Connector positions and actuator are sample-dependent. Dimensions in mm.
W=360; D=260; H=86; t=2; panel=3; rack=true; lid=true; internals=true;
$fn=48;
module rear(){
 difference(){
  translate([0,D-panel,0]) cube([W,panel,H]);
  for(x=[250,320]){
   translate([x,D+1,43])rotate([90,0,0])cylinder(h=panel+2,r=29);
   for(dx=[-25,25],dz=[-25,25])translate([x+dx,D+1,43+dz])rotate([90,0,0])cylinder(h=panel+2,r=2.15);
  }
 }
}
module chassis(){
 color([.18,.20,.23]){
  translate([0,panel,0])cube([W,D-2*panel,t]);
  translate([0,panel,t])cube([t,D-2*panel,H-2*t]);
  translate([W-t,panel,t])cube([t,D-2*panel,H-2*t]);
  if(lid)translate([0,panel,H-t])cube([W,D-2*panel,t]);
  rear();
 }
 color([.77,.79,.80])cube([W,panel,H]);
 color([.50,.09,.19])translate([17,-.3,8])cube([4,.3,70]);
}
module ear(right=false){
 sx=right ? W : -61.3;
 color([.15,.17,.20]){
  translate([sx,0,0])cube([61.3,3,H]);
  translate([right ? W : -3,0,0])cube([3,60,H]);
 }
}
chassis();
if(rack){ear(false);ear(true);}
if(internals){
 color([.55,.56,.57])translate([30,26,7])cube([300,200,2]);
 color([.25,.30,.35])translate([208,45,12])cube([117,112,49.2]);
 for(y=[83,140])color([.45,.48,.51])translate([43,y,12])cube([105,35,22]);
 color([.52,.56,.58])translate([178,40,2])cube([1,185,55]);
 for(x=[250,320])color([.34,.28,.20])translate([x-30,231,13])cube([60,25,60]);
}
// Ghost markers: HOLD positions; do not infer finished cutouts.
for(x=[35,70,155,200,112])color([.95,.55,.15,.6])translate([x,D,43])rotate([90,0,0])cylinder(h=2,r=x<100?5:12);
'''
(OUT/'BM-ICC-08_RevA.scad').write_text(scad,encoding='utf-8')

# Precise diagram renderer. No supplier CAD or generated product photograph is used.
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1080" viewBox="0 0 1440 1080">',
   '<rect width="1440" height="1080" fill="#f6f7f8"/>',
   '<style>text{font-family:Arial,sans-serif;fill:#192b3d}.title{font-size:32px;font-weight:bold}.small{font-size:15px}.label{font-size:18px}.dim{font-size:14px;fill:#617080}</style>']
def sr(x,y,w,h,fill,stroke=None):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
def tx(x,y,t,cls='label'):s.append(f'<text x="{x}" y="{y}" class="{cls}">{escape(t)}</text>')
def line(x1,y1,x2,y2,col='#70808e'):s.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{col}" fill="none"/>')
def circ(x,y,r,fill,stroke=None):s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
def dim(x,y,w,t):
    line(x,y,x+w,y);line(x,y-5,x,y+5);line(x+w,y-5,x+w,y+5);tx(x+w/2-45,y-8,t,'dim')
tx(48,54,'BİEM Radio Integrated Solution','title');tx(48,84,'BM-ICC-08  /  2U masaüstü + sökülebilir rack kulakları  /  Rev A','label')
sr(48,104,1344,3,'#a52c45')
tx(48,146,'01  ÖN GÖRÜNÜŞ · 360 × 86 mm','label')
ox,oy,k=160,181,2.3
sr(ox,oy,W*k,H*k,'#dde1e5','#8b969f');sr(ox+20*k,oy+8*k,4*k,70*k,'#a52c45')
logo=base64.b64encode((OUT.parent/'assets/biem-logo.png').read_bytes()).decode('ascii')
s.append(f'<image x="{ox+37*k}" y="{oy+16*k}" width="{92*k}" height="{92*k*472/1505}" href="data:image/png;base64,{logo}"/>')
tx(ox+145*k,oy+33*k,'BM-ICC-08','label');tx(ox+38*k,oy+49*k,'RADIO INTEGRATED SOLUTION','small')
for x,c,n in [(250,'#21886d','PWR'),(275,'#b6314b','REC'),(300,'#3483b4','LAN')]:
    circ(ox+x*k,oy+(H-23)*k,5,c);tx(ox+x*k-13,oy+(H-11)*k,n,'small')
circ(ox+330*k,oy+(H-43)*k,17,'#273442','#9aabb8');tx(ox+326*k,oy+(H-40)*k,'I','small')
sr(ox+182*k,oy+(H-37)*k,36*k,20*k,'#c7ced4','#9ba6af');tx(ox+180*k,oy+(H-11)*k,'SERVİS','small')
for x in [6,354]:
    for z in [6,80]:circ(ox+x*k,oy+(H-z)*k,3,'#7a8792')
for x in [ox-61.3*k,ox+W*k]:
    sr(x,oy,61.3*k,H*k,'#263442','#60717e')
    for z in [20.8,65.2]:sr(x+(8.75 if x<ox else 52.55)*k-4.5*k,oy+(H-z)*k-5*k,9*k,10*k,'#f6f7f8')
dim(ox-61.3*k,oy+H*k+35,482.6*k,'482,6 mm · kulaklı')
tx(1160,213,'2U rack / 86 mm gövde','label');tx(1160,244,'4×M4 bağlantı / yan','small');tx(1160,271,'Raf ile arkadan destek','small');tx(1160,298,'Rack’te ayaklar çıkarılır','small')
tx(48,467,'02  ÜSTTEN İÇ YERLEŞİM · kapak kaldırılmış','label')
ox,oy,k=70,500,1.5
sr(ox,oy,W*k,D*k,'#fff','#60717e');sr(ox+30*k,oy+26*k,300*k,200*k,'#eef1f3','#bdc7cf')
sr(ox+208*k,oy+45*k,117*k,112*k,'#344659');tx(ox+218*k,oy+92*k,'x86 PC','label');
s[-1]=s[-1].replace('class="label"','class="label" style="fill:white"')
tx(ox+210*k,oy+111*k,'117 × 112 × 49,2','small');s[-1]=s[-1].replace('class="small"','class="small" style="fill:white"')
for y,n in [(83,'RF 1 / V3'),(140,'RF 2 / V3')]:
    sr(ox+43*k,oy+y*k,105*k,35*k,'#aab7c1','#60717e');tx(ox+55*k,oy+(y+22)*k,n,'small')
sr(ox+178*k,oy+40*k,2*k,185*k,'#8b98a3')
for x in [250,320]:
    sr(ox+(x-30)*k,oy+231*k,60*k,25*k,'#d9d1c4','#887660')
    line(ox+x*k,oy+206*k,ox+x*k,oy+256*k,'#2a8e91')
tx(ox+192*k,oy+187*k,'Hava yolu → arka çıkış','small')
dim(ox,oy+D*k+27,W*k,'360 mm');tx(90,948,'Derinlik 260 mm · ayak hariç gövde 86 mm','small')
tx(700,467,'03  ARKA GÖRÜNÜŞ · RF / veri / soğutma','label')
ox,oy,k=700,530,1.7
sr(ox,oy,W*k,H*k,'#263442','#60717e')
for x,n,r in [(35,'RF1',5),(70,'RF2',5),(112,'DC*',10),(155,'LAN',12),(200,'USB',12)]:
    circ(ox+x*k,oy+(H-43)*k,r*k,'#d2ab5e' if x<100 else '#121d26','#bdc7cf')
    tx(ox+x*k-14,oy+(H-15)*k,n,'small');s[-1]=s[-1].replace('class="small"','class="small" style="fill:white"')
for x in [250,320]:
    circ(ox+x*k,oy+(H-43)*k,29*k,'#111c25','#77828c')
    for rr in [8,16,24]:circ(ox+x*k,oy+(H-43)*k,rr*k,'none','#526371')
tx(700,725,'* İlk prototip: orijinal adaptör kablosu + tutucu.','small')
tx(700,752,'Kilitli DC konnektör, elektriksel doğrulama sonrası.','small')
tx(700,799,'Malzeme: 2 mm Al şasi / kapak, 3 mm Al paneller.','small')
tx(700,826,'Kulaklar: 3 mm çelik. Ön panel: saten metal + bordo.','small')
tx(700,853,'Fanlar: 2 × 60 mm, 5 V. RF alıcılar ayrı sol bölgede.','small')
tx(700,899,'7 inç ekran: ayrı 3U revizyonu veya harici ekran.','small')
sr(48,970,1344,60,'#e9edf1')
tx(66,995,'RFQ / EVT TASARIMI · İmalat serbest bırakma öncesi numune, büküm, konnektör ve termal/RF kontrolü gerekir.','small')
tx(66,1019,'Ölçüler mm. Görünüşler farklı ölçeklerde. Ürün performansı / CE / IP kabulü verilmiş değildir. 14.09.2026','small')
s.append('</svg>');(OUT/'BM-ICC-08_Genel_Yerlesim.svg').write_text('\n'.join(s),encoding='utf-8')
print('6 DXF, 1 SCAD, 1 SVG written; RFQ/EVT revision A')
