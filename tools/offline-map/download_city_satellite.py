"""Add limited city detail using small EOX 2016 WMS requests; keep nationwide pack intact."""
import io,json,math,time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from download_satellite import R,CITIES,xy
root=Path(r'D:\Projects\Biem\_SDR\data\map-packs\turkey-satellite-eox-2016')
todo=set()
for lon,lat in CITIES:
    a,b=xy(lon-.06,lat+.045,14);c,d=xy(lon+.06,lat-.045,14)
    todo.update((x,y) for x in range(a//2*2,(c//2+1)*2) for y in range(b//2*2,(d//2+1)*2))

def fetch(item):
    x,y=item;p=root/'tiles'/'14'/str(x)/f'{y}.jpg'
    if p.exists():return
    unit=2*R/2**14
    params=dict(service='WMS',version='1.1.1',request='GetMap',layers='s2cloudless_3857',styles='',srs='EPSG:3857',bbox=f'{x*unit-R},{R-(y+1)*unit},{(x+1)*unit-R},{R-y*unit}',width=256,height=256,format='image/jpeg')
    req=Request('https://tiles.maps.eox.at/wms?'+urlencode(params),headers={'User-Agent':'BIEM-OfflineMap/1.0'})
    for attempt in range(3):
        try:
            with urlopen(req,timeout=20) as response:
                data=response.read(1_000_000)
                if 'image/jpeg' not in response.headers.get('Content-Type',''):raise ValueError(data[:200])
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                if image.size!=(256,256):raise ValueError('Invalid tile size')
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);time.sleep(.15);return
        except (OSError,ValueError):
            if attempt==2:raise
            time.sleep(2**attempt)

print(f'{len(todo)} city tiles',flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:
    for n,_ in enumerate(pool.map(fetch,sorted(todo),buffersize=3),1):
        if n%20==0:print(f'{n}/{len(todo)}',flush=True)
for x,y in {(x//2,y//2) for x,y in todo}:
    image=Image.new('RGB',(512,512))
    for dx in range(2):
        for dy in range(2):
            with Image.open(root/'tiles/14'/str(x*2+dx)/f'{y*2+dy}.jpg') as tile:image.paste(tile,(256*dx,256*dy))
    p=root/'tiles/13'/str(x)/f'{y}.jpg';p.parent.mkdir(parents=True,exist_ok=True)
    image.resize((256,256),Image.Resampling.LANCZOS).save(p,'JPEG',quality=90)
path=root/'manifest.json';info=json.loads(path.read_text('utf-8'));files=list((root/'tiles').glob('*/*/*.jpg'))
info.update(tile_count=len(files),bytes=sum(p.stat().st_size for p in files),city_maxzoom=14,description='Türkiye geneli z12; İstanbul, Ankara, İzmir, Konya, Van merkezlerinde z14. 2016–2017 uydu mozaiği; güncel görüntü değildir.')
temp=path.with_suffix('.tmp');temp.write_text(json.dumps(info,ensure_ascii=False,indent=2),'utf-8');temp.replace(path)
print('City detail complete',flush=True)
