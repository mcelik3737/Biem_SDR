import * as maplibregl from '/assets/maplibre-gl.mjs';
const $=id=>document.getElementById(id);
const selected={roads:true,labels:true,buildings:true,boundaries:true};
let dark=localStorage.getItem('biem-map-theme')==='dark';
document.body.classList.toggle('dark',dark);
const font=['Segoe UI','Arial','sans-serif'];
const name=['coalesce',['get','name'],['get','name_en'],''];
const origin=window.location.origin;
function style(){
 const c=dark?{land:'#263443',water:'#142535',park:'#28453c',urban:'#304151',building:'#4f6070',road:'#95a8b9',major:'#edb079',ink:'#e1eaf3',halo:'#263443',boundary:'#bb8296'}:{land:'#f5f2ec',water:'#bedee9',park:'#d8e5cc',urban:'#e8e5df',building:'#d5c9bf',road:'#ffffff',major:'#e5a25d',ink:'#3a4c60',halo:'#faf9f6',boundary:'#ad7891'};
 const layers=[{id:'background',type:'background',paint:{'background-color':c.land}}];
 function add(id,type,sourceLayer,paint,layout={},extra={}){layers.push({id,type,source:'turkey','source-layer':sourceLayer,paint,layout,...extra});}
 add('land','fill','land',{'fill-color':c.park});
 add('sites','fill','sites',{'fill-color':c.urban,'fill-opacity':.5});
 add('ocean','fill','ocean',{'fill-color':c.water});
 add('water','fill','water_polygons',{'fill-color':c.water});
 add('rivers','line','water_lines',{'line-color':c.water,'line-width':['interpolate',['linear'],['zoom'],7,.6,15,3]});
 add('boundaries','line','boundaries',{'line-color':c.boundary,'line-width':1.5,'line-dasharray':[4,3]});
 add('buildings','fill','buildings',{'fill-color':c.building,'fill-outline-color':dark?'#637083':'#c8bdb3'},{},{minzoom:13});
 add('roads-casing','line','streets',{'line-color':dark?'#566779':'#d6ccc2','line-width':['interpolate',['linear'],['zoom'],6,.6,10,2,14,6,18,18]},{'line-cap':'round','line-join':'round'});
 add('roads','line','streets',{'line-color':['match',['get','kind'],['motorway','trunk','primary'],c.major,c.road],'line-width':['interpolate',['linear'],['zoom'],6,.4,10,1,14,3.8,18,15]},{'line-cap':'round','line-join':'round'});
 add('street-names','symbol','street_labels',{'text-color':c.ink,'text-halo-color':c.halo,'text-halo-width':1.5},{'symbol-placement':'line','text-field':name,'text-font':font,'text-size':12,'text-max-angle':40},{minzoom:12});
 add('places','symbol','place_labels',{'text-color':c.ink,'text-halo-color':c.halo,'text-halo-width':2},{'text-field':name,'text-font':font,'text-size':['interpolate',['linear'],['zoom'],5,12,10,16,16,18],'text-padding':8});
 add('water-names','symbol','water_polygons_labels',{'text-color':dark?'#92becb':'#417a90','text-halo-color':c.water,'text-halo-width':1},{'text-field':name,'text-font':font,'text-size':12},{minzoom:9});
 return {version:8,sources:{turkey:{type:'vector',tiles:[origin+'/tiles/{z}/{x}/{y}.pbf'],minzoom:0,maxzoom:14,bounds:[25.5,35.6,45,42.3],attribution:'© OpenStreetMap contributors · Geofabrik · ODbL 1.0'}},layers};
}
const map=new maplibregl.Map({container:'map',style:style(),center:[35.2,39],zoom:5.5,minZoom:4,maxZoom:19,maxBounds:[[22,32],[49,46]],renderWorldCopies:false,attributionControl:false});
map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
map.addControl(new maplibregl.ScaleControl({unit:'metric'}),'bottom-left');
map.addControl(new maplibregl.AttributionControl({compact:false}),'bottom-right');
function country(){map.fitBounds([[25.5,35.8],[44.85,42.15]],{padding:48,duration:800});}
const groups={roads:['roads','roads-casing'],labels:['places','street-names','water-names'],buildings:['buildings'],boundaries:['boundaries']};
function applyGroups(){for(const [group,ids] of Object.entries(groups)) for(const id of ids) if(map.getLayer(id)) map.setLayoutProperty(id,'visibility',selected[group]?'visible':'none');}
map.on('style.load',applyGroups);
map.on('load',()=>{country();$('message').textContent='';});
map.on('zoom',()=>{$('zoom').textContent='Z '+map.getZoom().toFixed(1);});
map.on('error',e=>{$('message').textContent='Harita görüntüleme hatası: '+e.error.message;});
map.on('click',e=>{const text=e.lngLat.lat.toFixed(6)+'° K · '+e.lngLat.lng.toFixed(6)+'° D';$('position').textContent=text;new maplibregl.Popup().setLngLat(e.lngLat).setText(text).addTo(map);});
$('turkey').onclick=country;
$('city').onchange=e=>{if(e.target.value)map.flyTo({center:e.target.value.split(',').map(Number),zoom:14,duration:1000});};
for(const id of Object.keys(groups))$(id).onchange=e=>{selected[id]=e.target.checked;applyGroups();};
function themeLabel(){$('theme').textContent=dark?'Açık görünüm':'Koyu görünüm';}
themeLabel();
$('theme').onclick=()=>{dark=!dark;localStorage.setItem('biem-map-theme',dark?'dark':'light');document.body.classList.toggle('dark',dark);themeLabel();map.setStyle(style());};
$('coordinates').onsubmit=e=>{e.preventDefault();const data=new FormData(e.target);const lat=Number(data.get('lat')),lon=Number(data.get('lon'));if(!Number.isFinite(lat)||!Number.isFinite(lon)||lat<34||lat>44||lon<24||lon>46)return;map.flyTo({center:[lon,lat],zoom:16});};
try{const response=await fetch('/api/package');if(!response.ok)throw Error('Paket okunamadı');const data=await response.json();$('packageState').textContent='Türkiye paketi hazır';$('packageSize').textContent=(data.bytes/1e6).toFixed(0)+' MB · '+data.minzoom+'–'+data.maxzoom+' yakınlık seviyesi';$('packageDetails').textContent=JSON.stringify({dosya:data.filename,format:data.format,katmanlar:data.layers?.map(l=>l.id),lisans:'ODbL 1.0 / OpenStreetMap',kaynak:'download.geofabrik.de'},null,2);}catch(error){$('packageState').textContent='Paket okunamadı';$('message').textContent=error.message;}
