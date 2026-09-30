"""Build an offline XYZ pack from EOX's explicitly downloadable 2016 imagery.

Source / stitching permission: https://cloudless.eox.at/license-non-commercial
2016 licence: CC BY 4.0. Newer non-commercial layers are intentionally not used.
At most three requests at a time, 4096px maximum, resumable blocks, bounded disk use.
"""
import argparse
import io
import json
import math
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image

R = 20037508.342789244
BBOX = (25.5, 35.7, 44.9, 42.2)
CITIES = [(28.9784,41.0082), (32.8597,39.9334), (27.1428,38.4237), (32.4932,37.8746), (43.373,38.501)]


def xy(lon, lat, z):
    return math.floor((lon+180)/360*2**z), math.floor((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)


def blocks(z, bounds):
    west,south,east,north = bounds
    x0,y0 = xy(west,north,z)
    x1,y1 = xy(east,south,z)
    return [(z,x,y) for x in range(x0//16*16,x1+1,16) for y in range(y0//16*16,y1+1,16)]


def request_block(z,x,y):
    n=2**z; size=min(16,n)
    unit=2*R/n
    params=dict(service='WMS',version='1.1.1',request='GetMap',layers='s2cloudless_3857',styles='',srs='EPSG:3857',
                bbox=f'{x*unit-R},{R-(y+size)*unit},{(x+size)*unit-R},{R-y*unit}',width=256*size,height=256*size,format='image/jpeg')
    request=Request('https://tiles.maps.eox.at/wms?'+urlencode(params),headers={'User-Agent':'BIEM-OfflineMap/1.0'})
    for attempt in range(4):
        try:
            with urlopen(request,timeout=90) as response:
                data=response.read(40_000_001)
                if 'image/jpeg' not in response.headers.get('Content-Type','') or len(data)>40_000_000:
                    raise ValueError('Unexpected map response')
            with Image.open(io.BytesIO(data)) as im:
                if im.size!=(256*size,256*size):
                    raise ValueError('Unexpected map size')
                im.load()
            return data,size
        except (OSError,HTTPError):
            if attempt==3:
                raise
            time.sleep(2**(attempt+2))
    raise RuntimeError('No image')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--zoom',type=int,choices=[10,11,12,13,14],default=12)
    ap.add_argument('--city-detail',action='store_true')
    args=ap.parse_args()
    dest=args.output.resolve();dest.mkdir(parents=True,exist_ok=True)
    todo=blocks(args.zoom,BBOX)
    if args.city_detail and args.zoom<14:
        for lon,lat in CITIES:
            todo+=blocks(14,(lon-.06,lat-.045,lon+.06,lat+.045))
    todo=sorted(set(todo))
    marker=dest/'completed-blocks.json'
    done=set(map(tuple,json.loads(marker.read_text()))) if marker.exists() else set()
    print(f'{len(todo)} blocks, {len(done)} already complete',flush=True)
    remaining=[block for block in todo if block not in done]
    pool=ThreadPoolExecutor(max_workers=3)
    # map preserves order and buffers only three fetched blocks, keeping memory bounded.
    fetched=pool.map(lambda block: (block,request_block(*block)),remaining,buffersize=3)
    for number,((z,x,y),(data,size)) in enumerate(fetched,len(done)+1):
        if shutil.disk_usage(dest).free<5_000_000_000:
            raise RuntimeError('Less than 5 GB free; stopped with completed blocks retained')
        with Image.open(io.BytesIO(data)) as im:
            for dx in range(size):
                folder=dest/'tiles'/str(z)/str(x+dx);folder.mkdir(parents=True,exist_ok=True)
                for dy in range(size):
                    path=folder/f'{y+dy}.jpg'
                    im.crop((dx*256,dy*256,(dx+1)*256,(dy+1)*256)).save(path,'JPEG',quality=90)
        done.add((z,x,y))
        temp=marker.with_suffix('.tmp');temp.write_text(json.dumps(sorted(done)));temp.replace(marker)
        print(f'{number}/{len(todo)} z{z} {x}/{y} {len(data)/1e6:.1f} MB',flush=True)
        time.sleep(.25)
    pool.shutdown()
    # Build coarse levels locally, preserving detailed city coverage. No network here.
    maximum=max(z for z,x,y in done)
    for z in range(maximum,0,-1):
        paths=list((dest/'tiles'/str(z)).glob('*/*.jpg'))
        parents={(int(p.parent.name)//2,int(p.stem)//2) for p in paths}
        for x,y in parents:
            target=dest/'tiles'/str(z-1)/str(x)/f'{y}.jpg'
            if target.exists():
                continue
            picture=Image.new('RGB',(512,512),'#152b39')
            for dx in range(2):
                for dy in range(2):
                    source=dest/'tiles'/str(z)/str(x*2+dx)/f'{y*2+dy}.jpg'
                    if source.exists():
                        with Image.open(source) as tile: picture.paste(tile,(dx*256,dy*256))
            target.parent.mkdir(parents=True,exist_ok=True)
            picture.resize((256,256),Image.Resampling.LANCZOS).save(target,'JPEG',quality=90)
        print(f'Parent level {z-1} ready',flush=True)
    files=list((dest/'tiles').glob('*/*/*.jpg'))
    manifest={'format':'biem-xyz-v1','name':'Türkiye uydu • EOX 2016','tile_count':len(files),'bytes':sum(p.stat().st_size for p in files),
              'source':'https://cloudless.eox.at/license-non-commercial','license':'CC BY 4.0',
              'attribution':'EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2016 & 2017)',
              'description':f'Türkiye geneli z{args.zoom}; '+('İstanbul, Ankara, İzmir, Konya, Van merkezleri z14. ' if args.city_detail else '')+'2016–2017 uydu mozaiği; güncel görüntü değildir.',
              'bbox':BBOX,'country_maxzoom':args.zoom,'city_maxzoom':14 if args.city_detail else None,'network_required_for_viewing':False}
    temp=dest/'manifest.tmp';temp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8');temp.replace(dest/'manifest.json')
    print(json.dumps(manifest,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
