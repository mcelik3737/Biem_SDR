/* Design reference only. All data below is fictional; no receiver, network or audio access. */
'use strict';
const state = { direction: 'operations', view: 'live', selected: 1, record: 1, acquiring: true, measuring: false, muted: new Set(), playing: false, progress: 6, speed: 1, columns: 'auto', toastTimer: null };
const channels = [
  {id:1,name:'Güvenlik',mode:'DMR',frequency:'460.10000',status:'receiving',caller:'Devriye 02',radio:1002,group:101,groupName:'Güvenlik ekibi',slot:1,cc:1,duration:'00:18',level:-42,source:'RTL-SDR 01',enabled:true},
  {id:2,name:'Teknik ekip',mode:'DMR',frequency:'460.12500',status:'receiving',caller:'Teknik 03',radio:2003,group:201,groupName:'Teknik ekip',slot:2,cc:1,duration:'00:07',level:-47,source:'RTL-SDR 01',enabled:true},
  {id:3,name:'Lojistik',mode:'NFM',frequency:'460.15000',status:'idle',caller:null,radio:null,group:null,slot:null,cc:null,duration:null,level:-63,source:'RTL-SDR 01',enabled:true},
  {id:4,name:'Üretim',mode:'DMR',frequency:'460.17500',status:'warning',caller:null,radio:null,group:null,slot:null,cc:null,duration:null,level:-51,source:'RTL-SDR 01',enabled:true},
  {id:5,name:'Saha destek',mode:'NFM',frequency:'460.20000',status:'idle',caller:null,radio:null,group:null,slot:null,cc:null,duration:null,level:-67,source:'RTL-SDR 01',enabled:true},
  {id:6,name:'Yedek kanal',mode:'TETRA',frequency:'460.22500',status:'disabled',caller:null,radio:null,group:null,slot:null,cc:null,duration:null,level:null,source:'RTL-SDR 01',enabled:false}
];
const records = [
  {id:1,time:'14:31:52',channel:1,caller:'Devriye 02',radio:1002,group:101,slot:1,seconds:22},
  {id:2,time:'14:30:41',channel:2,caller:'Teknik 03',radio:2003,group:201,slot:2,seconds:14},
  {id:3,time:'14:29:18',channel:3,caller:null,radio:null,group:null,slot:null,seconds:31},
  {id:4,time:'14:28:04',channel:1,caller:'Devriye 01',radio:1001,group:101,slot:1,seconds:12},
  {id:5,time:'14:26:57',channel:5,caller:null,radio:null,group:null,slot:null,seconds:9},
  {id:6,time:'14:25:36',channel:2,caller:'Teknik 01',radio:2001,group:201,slot:2,seconds:19},
  {id:7,time:'14:24:02',channel:1,caller:'Devriye 02',radio:1002,group:101,slot:1,seconds:8},
  {id:8,time:'14:22:49',channel:3,caller:null,radio:null,group:null,slot:null,seconds:17},
  {id:9,time:'14:21:06',channel:1,caller:'Devriye 01',radio:1001,group:101,slot:1,seconds:26}
];
const main = document.getElementById('main');
const escapeHtml = value => String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon = name => '<i data-icon="' + name + '"></i>';
const pad = n => String(n).padStart(2, '0');
const duration = n => pad(Math.floor(n / 60)) + ':' + pad(Math.floor(n % 60));
const lookup = id => channels.find(c => c.id === Number(id));
const active = c => state.acquiring && c.enabled && c.status === 'receiving';
const activeCount = () => channels.filter(active).length;
const lower = s => String(s ?? '').toLocaleLowerCase('tr-TR');
const button = (text, action, name, extra = '') => '<button class="button ' + extra + '" data-action="' + action + '">' + (name ? icon(name) : '') + text + '</button>';
function mountIcons(root = document) {
  root.querySelectorAll('[data-icon]').forEach(node => {
    const definition = window.RADIA_ICONS[node.dataset.icon];
    if (!definition) return;
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 24 24'); svg.setAttribute('class','icon'); svg.setAttribute('aria-hidden','true');
    for (const [tag, attributes] of definition) {
      const child = document.createElementNS(svg.namespaceURI, tag);
      for (const [key, value] of Object.entries(attributes)) child.setAttribute(key, value);
      svg.appendChild(child);
    }
    node.replaceWith(svg);
  });
}
function toast(message) {
  const el = document.getElementById('toast'); el.textContent = message; el.classList.add('visible');
  clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => el.classList.remove('visible'), 4200);
}
function updateChrome() {
  document.body.dataset.theme = state.direction;
  document.querySelectorAll('[data-direction]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.direction === state.direction)));
  document.querySelectorAll('[data-view]').forEach(b => { b.classList.toggle('selected',b.dataset.view === state.view); b.setAttribute('aria-current',b.dataset.view === state.view ? 'page' : 'false'); });
  document.getElementById('global-status').textContent = state.acquiring ? 'Alıcı çalışıyor' : state.measuring ? 'Spektrum ölçülüyor' : 'Alıcı durduruldu';
  document.querySelector('.health .dot').className = 'dot ' + (state.acquiring ? 'green' : state.measuring ? 'amber' : '');
  document.getElementById('receiver-toggle').innerHTML = icon(state.acquiring ? 'Square' : 'Play') + (state.acquiring ? 'Alımı durdur' : 'Alımı başlat');
  document.getElementById('footer-recording').textContent = activeCount() ? activeCount() + ' çağrı kaydediliyor' : 'Kayıt alınmıyor';
  document.getElementById('footer-state').textContent = state.measuring ? 'SDR spektrum ölçümünde' : state.acquiring ? 'USB · RTL-SDR 01' : 'Alıcı durduruldu';
}
function heading(title, sub, actions='') {
  return '<div class="page-heading"><div><h1>' + title + '</h1><p>' + sub + '</p></div><div class="heading-actions">' + actions + '</div></div>';
}
function render() {
  updateChrome();
  const screens = {live:liveView,archive:archiveView,spectrum:spectrumView,sources:sourcesView,directory:directoryView};
  main.innerHTML = screens[state.view]();
  mountIcons();
  if (state.view === 'live') filterChannels();
  if (state.view === 'archive') filterRecords();
}
function navigate(view) {
  if (state.view !== view) { state.playing = false; state.view = view; main.scrollTop = 0; }
  render();
}
function setDirection(direction) {
  state.direction = direction; state.playing = false;
  state.view = direction === 'review' ? 'archive' : 'live';
  history.replaceState(null,'','#' + direction); main.scrollTop = 0; render();
}
function liveView() {
  return heading('Canlı izleme', 'Kanallar, konuşan ekipler ve kayıtlar tek bakışta.',
    button('Kanal düzeni','layout','LayoutGrid') + button('Kanal ayarları','edit-selected','SlidersHorizontal')) +
    '<div class="source-strip"><span class="source-chip">' + icon('Usb') + '<strong>RTL-SDR 01</strong><span class="muted">USB</span></span><span class="source-separator"></span><span class="source-chip"><i class="dot ' + (state.acquiring?'green':'') + '"></i><span>' + (state.acquiring?'Sabit alım':'Alım durdu') + '</span></span><span class="source-caption">Aynı RF bandında eşzamanlı izleme</span><span class="source-separator"></span><span class="source-chip"><i class="dot red"></i><strong>' + activeCount() + ' aktif kayıt</strong></span><button class="source-link" data-action="sources">Kaynak ayrıntıları ' + icon('ChevronRight') + '</button></div>' +
    '<div class="live-workspace"><section class="channel-area"><div class="section-toolbar"><div class="section-label"><h2>Kanallar</h2><span class="count-badge">6</span></div><div class="toolbar-filters"><label class="search">' + icon('Search') + '<input id="channel-search" aria-label="Kanal, kişi veya grup ara" placeholder="Kanal, kişi veya grup ara"></label><label class="checkbox"><input id="active-only" type="checkbox">Yalnız aktif</label></div></div><div class="channel-grid" id="channel-grid"></div>' +
    '<section class="recent-panel"><div class="panel-heading"><div class="section-label"><h2>Son tamamlanan kayıtlar</h2><span class="count-badge">Bugün</span></div>' + button('Kayıt arşivini aç','archive','ArrowRight','subtle') + '</div><div class="table-wrap">' + recordsTable(records.slice(0,3),true) + '</div></section></section><aside class="detail-panel" id="live-detail">' + liveDetail(lookup(state.selected)) + '</aside></div>';
}
function card(c) {
  const receiving = active(c);
  const status = !c.enabled ? 'Devre dışı' : !state.acquiring ? 'Alım durdu' : receiving ? 'Alınıyor' : c.status === 'warning' ? 'Senkron yok' : 'Beklemede';
  const cls = receiving?'rx':state.acquiring && c.status==='warning'?'warning':'';
  const identity = receiving ? '<div><div class="caller-name">' + escapeHtml(c.caller) + '</div><div class="caller-meta">ID ' + c.radio + ' · TG ' + c.group + ' · Slot ' + c.slot + '</div></div><strong class="call-timer">' + c.duration + '</strong>' : '<span class="idle-label">' + (!c.enabled ? 'Deneysel · etkin değil' : !state.acquiring ? 'Alıcı başlatılmayı bekliyor' : c.status==='warning' ? 'Sinyal var, ses çözülemedi' : 'Yeni çağrı bekleniyor') + '</span>';
  const level = c.enabled && state.acquiring ? c.level : null;
  const lit = level === null ? 0 : Math.max(0,Math.round((level+85)/6));
  const meter = Array.from({length:12},(_,i) => '<span class="' + (i<lit?'on':'') + '"></span>').join('');
  return '<article class="channel-card ' + (receiving?'receiving ':'') + (state.acquiring&&c.status==='warning'?'warning ':'') + (state.selected===c.id?'selected':'') + '" data-channel-card="' + c.id + '">' +
    '<button class="card-main" data-select-channel="' + c.id + '" aria-pressed="' + (state.selected===c.id) + '" aria-label="' + escapeHtml(c.name + ', ' + status + ', ayrıntıları göster') + '"><div class="card-top"><span class="channel-number">CH ' + pad(c.id) + '</span><span class="mode-badge">' + c.mode + '</span><span class="state-badge ' + cls + '"><i class="dot ' + (receiving?'blue':cls==='warning'?'amber':'') + '"></i>' + status + '</span></div><div class="card-name">' + escapeHtml(c.name) + '</div><div class="frequency">' + c.frequency + ' MHz</div><div class="card-identity">' + identity + '</div><div class="signal-row"><div class="meter" aria-hidden="true">' + meter + '</div><span class="mono">' + (level===null?'—':level+' dBFS') + '</span></div></button>' +
    '<div class="card-footer"><span class="record-status ' + (receiving?'active':'muted') + '"><i class="dot ' + (receiving?'red':'') + '"></i>' + (receiving?'Kaydediliyor':!c.enabled?'Kayıt kapalı':c.status==='warning'&&state.acquiring?'Ses kaydı yok':'Kayıt bekliyor') + '</span><div><button class="icon-button" data-mute="' + c.id + '" aria-pressed="' + state.muted.has(c.id) + '" aria-label="' + escapeHtml(c.name + (state.muted.has(c.id)?' dinleme sesini aç':' dinleme sesini kapat')) + '" title="Yerel dinleme sesi; kayıt etkilenmez">' + icon(state.muted.has(c.id)?'VolumeX':'Volume2') + '</button><button class="icon-button" data-edit-channel="' + c.id + '" aria-label="' + escapeHtml(c.name+' ayarları') + '">' + icon('Settings2') + '</button></div></div></article>';
}
function filterChannels() {
  const term = lower(document.getElementById('channel-search')?.value);
  const only = document.getElementById('active-only')?.checked;
  const filtered = channels.filter(c => (!only||active(c)) && lower([c.name,c.caller,c.radio,c.group,c.groupName,c.mode,c.frequency].join(' ')).includes(term));
  const grid = document.getElementById('channel-grid');
  if (!grid) return;
  grid.innerHTML = filtered.map(card).join('') || '<div class="empty"><strong>Kanal bulunamadı</strong><small>Arama metnini veya aktif kanal filtresini değiştirin.</small></div>';
  grid.style.gridTemplateColumns = state.columns === 'auto' ? '' : 'repeat(' + Math.min(Number(state.columns), Math.max(1, Math.floor(grid.clientWidth / 260))) + ',minmax(0,1fr))';
  mountIcons(grid);
}
function liveDetail(c) {
  const receiving = active(c);
  return '<div class="detail-header"><strong>Seçili kanal</strong><span class="mono">CH ' + pad(c.id) + '</span></div><div class="detail-body"><div class="detail-eyebrow"><i class="dot ' + (receiving?'blue':'') + '"></i>' + (receiving?'GELEN GRUP ÇAĞRISI':'KANAL DURUMU') + '</div><div class="avatar-call">' + icon(c.mode==='NFM'?'Radio':'Users') + '</div><h3>' + escapeHtml(receiving?c.caller:c.name) + '</h3><p class="detail-subtitle">' + escapeHtml(receiving?c.groupName:c.mode+' · '+c.frequency+' MHz') + '</p><dl class="detail-grid"><div><dt>Telsiz ID</dt><dd>' + (receiving?c.radio:'—') + '</dd></div><div><dt>Grup ID</dt><dd>' + (receiving?c.group:'—') + '</dd></div><div><dt>Zaman dilimi</dt><dd>' + (receiving?'Slot '+c.slot:'—') + '</dd></div><div><dt>Color code</dt><dd>' + (receiving?c.cc:'—') + '</dd></div><div><dt>Kanal</dt><dd>' + escapeHtml(c.name) + '</dd></div><div><dt>Kaynak</dt><dd>USB · 01</dd></div></dl><div class="detail-record"><span class="record-status ' + (receiving?'active':'muted') + '"><i class="dot ' + (receiving?'red':'') + '"></i>' + (receiving?'Ses kaydediliyor':'Aktif ses kaydı yok') + '</span><span class="mono">' + (receiving?c.duration:'—') + '</span></div><div class="detail-actions"><button class="button" data-mute="' + c.id + '">' + icon(state.muted.has(c.id)?'VolumeX':'Volume2') + (state.muted.has(c.id)?'Sesi aç':'Sesi kapat') + '</button><button class="button" data-channel-history="' + c.id + '">' + icon('Archive') + 'Geçmiş</button></div><p class="detail-note">' + (c.mode==='NFM'?'Analog FM kayıtlarında otomatik telsiz ID, grup ve slot bulunmaz.':c.mode==='TETRA'?'Deneysel kanal; saha doğrulaması bekliyor.':'Kimlik bilgisi çözülemediğinde alanlar boş kalır.') + ' Dinleme sesini kapatmak kaydı durdurmaz.</p></div>';
}
function selectChannel(id) {
  state.selected = Number(id); filterChannels();
  const detail = document.getElementById('live-detail');
  if (detail) {detail.innerHTML = liveDetail(lookup(id));mountIcons(detail);}
  if (window.innerWidth<=1160 || state.direction==='night') {
    showDrawer('Kanal ayrıntıları','<div class="detail-panel" style="margin:0;border:0">' + liveDetail(lookup(id)) + '</div>');
  }
}
function recordsTable(items, compact=false) {
  return '<table><thead><tr><th>Saat</th><th>Kanal</th><th>Konuşan / ID</th>' + (compact?'<th>Grup / Slot</th>':'<th>Grup</th><th>Slot</th>') + '<th>Süre</th><th>Durum</th><th><span class="muted">Dinle</span></th></tr></thead><tbody id="' + (compact?'recent-rows':'archive-rows') + '">' + recordRows(items,compact) + '</tbody></table>';
}
function recordRows(items,compact=false) {
  return items.map(r => {
    const c=lookup(r.channel);
    return '<tr data-record-row="' + r.id + '" class="' + (state.record===r.id&&!compact?'selected':'') + '"><td class="mono">' + r.time + '</td><td class="table-channel">' + escapeHtml(c.name) + '<small>' + c.mode + '</small></td><td>' + escapeHtml(r.caller || 'Analog çağrı') + '<span class="muted">' + (r.radio?' · '+r.radio:'') + '</span></td>' + (compact?'<td>' + (r.group?'TG '+r.group+' · Slot '+r.slot:'—') + '</td>':'<td>' + escapeHtml(r.group) + '</td><td>' + escapeHtml(r.slot) + '</td>') + '<td class="mono">' + duration(r.seconds) + '</td><td><span class="table-status">' + icon('CheckCheck') + 'Kaydedildi</span></td><td><button class="row-play" data-play-record="' + r.id + '" aria-label="' + escapeHtml(r.time+' '+c.name+' kaydını seç ve oynatımı önizle') + '">' + icon('Play') + '</button></td></tr>';
  }).join('');
}
function archiveView() {
  return heading('Kayıt arşivi','Çağrıyı bulun. Bağlamıyla inceleyin. Tek noktadan dinleyin.',
    '<span class="small-pill">12 Eylül 2026</span>') +
    '<div class="archive-filters"><label class="field grow">Başlık, kişi, kanal veya ID<input id="archive-search" placeholder="Örn. Devriye 02 veya 1002" type="search"></label><label class="field">Tarih<input id="archive-date" aria-label="Kayıt tarihi" type="date" value="2026-09-12"></label><label class="field">Slot<select id="archive-slot" aria-label="Slot filtresi"><option value="">Tümü</option><option value="1">Slot 1</option><option value="2">Slot 2</option><option value="analog">Analog / yok</option></select></label>' + button('Temizle','reset-filters','RotateCcw') + '</div>' +
    (state.direction==='review'?timeline():'') +
    '<div class="archive-workspace"><div class="archive-main"><section class="recent-panel"><div class="panel-heading"><div class="section-label"><h2>Konuşma kayıtları</h2><span class="count-badge" id="archive-count">9</span></div><div class="archive-stats"><span>En yeni önce</span><span><b id="total-duration">02:38</b> toplam</span></div></div><div class="table-wrap">' + recordsTable(records) + '</div><div class="archive-caption" id="archive-caption">9 örnek kayıt · Kaydı seçin veya oynatma düğmesine basın.</div></section><div id="player-container">' + player() + '</div></div><aside class="detail-panel" id="record-detail">' + recordDetail(records.find(r=>r.id===state.record)) + '</aside></div>';
}
function timeline() {
  return '<section class="review-timeline"><div class="timeline-top"><strong>Çağrı zaman çizelgesi</strong><span class="muted">14:20 — 14:32 · Örnek çağrı dağılımı</span></div>' +
    ['Güvenlik','Teknik ekip','Analog kanallar'].map((name,i)=>'<div class="timeline-track"><span>'+name+'</span><div class="timeline-track-area">'+[4,19,43,63,85].slice(i,5).map((n,j)=>'<span class="timeline-block '+(i===1?'burgundy':'')+'" style="left:'+(n-i*2)+'%;width:'+(2+j%3)+'%"></span>').join('')+'</div></div>').join('') + '</section>';
}
function filterRecords() {
  const term=lower(document.getElementById('archive-search')?.value), day=document.getElementById('archive-date')?.value, slot=document.getElementById('archive-slot')?.value;
  const items=records.filter(r=>(!day||day==='2026-09-12')&&(!slot||(slot==='analog'?r.slot===null:r.slot===Number(slot)))&&lower([lookup(r.channel).name,r.caller,r.radio,r.group].join(' ')).includes(term));
  const tbody=document.getElementById('archive-rows');if(!tbody)return;
  tbody.innerHTML=items.length?recordRows(items):'<tr><td colspan="8"><div class="empty"><strong>Kayıt bulunamadı</strong>Örnek kayıtlar 12 Eylül 2026 tarihindedir. Filtreleri genişletin.</div></td></tr>';
  document.getElementById('archive-count').textContent=items.length;
  document.getElementById('total-duration').textContent=duration(items.reduce((n,r)=>n+r.seconds,0));
  document.getElementById('archive-caption').textContent=items.length+' örnek kayıt · Seçili kayıt oynatıcıda korunur.';
  mountIcons(tbody);
}
function recordDetail(r) {
  const c=lookup(r.channel);
  return '<div class="detail-header"><strong>Kayıt ayrıntıları</strong><span class="table-status">'+icon('Check')+'WAV</span></div><div class="detail-body"><div class="detail-eyebrow">TAMAMLANAN ÇAĞRI</div><h3>'+escapeHtml(r.caller||c.name)+'</h3><p class="detail-subtitle">'+c.name+' · 12.09.2026 / '+r.time+'</p><dl class="detail-grid"><div><dt>Telsiz ID</dt><dd>'+escapeHtml(r.radio)+'</dd></div><div><dt>Grup ID</dt><dd>'+escapeHtml(r.group)+'</dd></div><div><dt>Slot</dt><dd>'+escapeHtml(r.slot)+'</dd></div><div><dt>Kayıt süresi</dt><dd>'+duration(r.seconds)+'</dd></div><div><dt>Frekans</dt><dd>'+c.frequency+' MHz</dd></div><div><dt>Modülasyon</dt><dd>'+c.mode+'</dd></div></dl><p class="detail-note">Kaynak: USB · RTL-SDR 01<br>Mono · '+(c.mode==='NFM'?'16':'8')+' kHz · PCM<br>Örnek kayıt; gerçek ses dosyası içermez.</p>'+button('Bu kanaldaki kayıtlar','filter-current-channel','Search','subtle')+'</div>';
}
function waveform() {
  return Array.from({length:150},(_,i)=>'<span style="height:'+(7+Math.abs(Math.sin(i*1.7)*Math.cos(i*.29))*64*(i%33<4?.16:1))+'px"></span>').join('');
}
function player() {
  const r=records.find(r=>r.id===state.record),c=lookup(r.channel);
  state.progress=Math.min(state.progress,r.seconds);
  return '<section class="player"><div class="player-info"><div><h2>'+escapeHtml(r.caller||c.name)+' <span class="muted">/ '+c.name+'</span></h2><p>'+r.time+' · '+c.mode+' · '+(r.group?'TG '+r.group+' · Slot '+r.slot:'Analog çağrı')+'</p></div><span class="small-pill">SEÇİLİ KAYIT</span></div><div class="waveform" aria-label="Temsili ses dalga biçimi">'+waveform()+'<i class="playhead" id="playhead" style="left:'+(state.progress/r.seconds*100)+'%"></i></div><div class="wave-labels"><span>00:00</span><span>'+duration(r.seconds/4)+'</span><span>'+duration(r.seconds/2)+'</span><span>'+duration(r.seconds*.75)+'</span><span>'+duration(r.seconds)+'</span></div><div class="player-controls"><button class="button primary" data-action="playback" id="play-button">'+icon(state.playing?'Pause':'Play')+(state.playing?'Duraklat':'Oynatımı önizle')+'</button><span class="mono" id="play-time">'+duration(state.progress)+' / '+duration(r.seconds)+'</span><input id="seek" type="range" min="0" max="'+r.seconds+'" value="'+state.progress+'" step=".1" aria-label="Kayıt içinde ilerle"><button class="button compact" data-action="speed" id="speed-button">'+state.speed+'×</button><span class="player-note">Temsili dalga biçimi · ses dosyası yok</span></div></section>';
}
function selectRecord(id,play=false) {
  state.record=Number(id);state.progress=0;state.playing=play;
  if(state.view!=='archive'){state.view='archive';render();return;}
  document.getElementById('record-detail').innerHTML=recordDetail(records.find(r=>r.id===state.record));
  document.getElementById('player-container').innerHTML=player();filterRecords();mountIcons();
}
function sourcesView() {
  return heading('Kaynaklar ve ayarlar','Alıcı bağlantıları ve gelişmiş kanal yapılandırması.') +
    '<div class="source-cards"><section class="source-card"><div class="source-card-title">'+icon('Usb')+'<h3>RTL-SDR 01</h3><span class="small-pill">USB</span></div><p>Altı tanımlı kanal bu alıcıya bağlı. RF ayarları kaynak düzeyinde yönetilir.</p><dl class="detail-grid"><div><dt>Durum</dt><dd>'+(state.acquiring?'Alım açık':'Alım kapalı')+'</dd></div><div><dt>Alım biçimi</dt><dd>Sabit / bant içi</dd></div><div><dt>Kazanç</dt><dd>19 dB · manuel</dd></div><div><dt>Frekans düzeltme</dt><dd>0 PPM</dd></div></dl>'+button('Alıcı ayarlarını aç','receiver-settings','SlidersHorizontal')+'</section>' +
    '<section class="source-card"><div class="source-card-title">'+icon('Network')+'<h3>Ağ kaynağı</h3><span class="mode-badge">BAĞLANTI YOK</span></div><p>rtl_tcp IQ alımı ve üretici repeater entegrasyonu ayrı bağlantı türleridir.</p><dl class="detail-grid"><div><dt>rtl_tcp</dt><dd>Yapılandırılmadı</dd></div><div><dt>Hytera Ethernet</dt><dd>Doğrulama bekliyor</dd></div></dl>'+button('Bağlantı türlerini incele','network-info','ChevronRight')+'</section></div><p class="settings-help"><strong>Kanal ayarları</strong> seçili kanalın yan panelinde açılır. Analog FM için CTCSS/DCS, DMR için color code ve slot filtreleri gösterilir. Tarama modunda kanallar sırayla dinlenir; aynı anda alındıkları izlenimi verilmez.</p>';
}
function directoryView() {
  return heading('Kimlik rehberi','Telsiz ve grup kimliklerini anlamlı adlarla eşleştirin.')+
    '<section class="recent-panel" style="margin-top:0"><div class="panel-heading"><h2>Demo tesis / Kimlik eşleştirmeleri</h2><span class="small-pill">Sistem kapsamı: Demo tesis</span></div><div class="table-wrap"><table><thead><tr><th>Tür</th><th>Kimlik</th><th>Görünen ad</th><th>Kapsam</th><th></th></tr></thead><tbody>'+
    [{type:'Telsiz',id:1001,name:'Devriye 01'},{type:'Telsiz',id:1002,name:'Devriye 02'},{type:'Telsiz',id:2003,name:'Teknik 03'},{type:'Grup',id:101,name:'Güvenlik ekibi'},{type:'Grup',id:201,name:'Teknik ekip'}].map(r=>'<tr><td>'+r.type+'</td><td class="mono">'+r.id+'</td><td class="table-channel">'+r.name+'</td><td>Demo tesis</td><td><button class="button compact" data-alias="'+r.id+'" data-alias-name="'+r.name+'">İncele</button></td></tr>').join('')+'</tbody></table></div></section><p class="directory-note">Aynı ID başka bir müşteride farklı bir kişiye ait olabilir. Eşleşmeler sistem / müşteri kapsamında tutulur; bilinmeyen ID için ad üretilmez.</p>';
}
function spectrumView() {
  const points=Array.from({length:240},(_,i)=> {
    const y=160-9*Math.sin(i*4.1)-4*Math.cos(i*1.6)-66*Math.exp(-Math.pow((i-63)/2.5,2))-91*Math.exp(-Math.pow((i-150)/3,2))-40*Math.exp(-Math.pow((i-204)/4,2));
    return (i*1000/239).toFixed(1)+','+y.toFixed(1);
  }).join(' ');
  return heading('Spektrum','RF incelemesi · örnek grafik · ölçüm birimi dBFS',
    button(state.measuring?'Ölçümü durdur':'Ölçümü başlat',state.measuring?'stop-measurement':'measurement',state.measuring?'Square':'Activity')) +
    '<div class="notice">'+icon('CircleAlert')+'<div><strong>'+(state.acquiring?'Alıcı şu anda kayıt için kullanılıyor':state.measuring?'Ölçüm önizlemesi açık; çağrı kaydı kapalı':'Ölçüm için alıcı hazır')+'</strong><p>Aynı cihazda bu ölçüm çalışırken çağrı alımı ve kayıt durur.</p></div></div>' +
    '<section class="source-card"><div class="section-toolbar"><h2>460.000 — 460.500 MHz</h2><span class="small-pill">ÖRNEK GRAFİK</span></div><div class="spectrum-chart"><svg viewBox="0 0 1040 230" role="img" aria-label="Temsili RF spektrumu, gerçek ölçüm değildir">'+[20,60,100,140,180].map((n,i)=>'<line x1="40" x2="1040" y1="'+n+'" y2="'+n+'" stroke="#32475e" stroke-width=".7"/><text x="2" y="'+(n+3)+'" fill="#93a8c0" font-size="10">'+(-i*20)+'</text>').join('')+'<polyline transform="translate(40,0)" points="'+points+'" fill="none" stroke="#63c9d4" stroke-width="1.4"/>'+[0,1,2,3,4].map((n)=>'<text x="'+(40+n*239)+'" y="220" fill="#93a8c0" font-size="10">'+(460+n*.125).toFixed(3)+'</text>').join('')+'</svg></div><div class="chart-waterfall" aria-label="Temsili şelale görüntüsü">'+Array.from({length:28},(_,i)=>'<div class="waterfall-row" style="opacity:'+(0.3+(i%7)/12)+'"></div>').join('')+'</div><div class="chart-caption"><span>Gösterim: Spektrum + şelale</span><span>dBFS · kalibre dBm değildir</span></div></section>';
}
function showDrawer(title,body,footer='') {
  const drawer=document.getElementById('drawer');
  drawer.innerHTML='<div class="drawer-top"><h2 id="drawer-title">'+title+'</h2><button class="icon-button" data-action="close-drawer" aria-label="Paneli kapat">'+icon('X')+'</button></div><div class="drawer-content">'+body+'</div>'+(footer?'<div class="drawer-footer">'+footer+'</div>':'');
  mountIcons(drawer); if(!drawer.open)drawer.showModal();
}
function editChannel(id) {
  const c=lookup(id);state.selected=c.id;
  showDrawer('Kanal ayarları',
    '<label class="field">Kanal adı<input id="edit-name" value="'+escapeHtml(c.name)+'" maxlength="60"></label><div class="field-row"><label class="field">Mod<select id="edit-mode"><option'+(c.mode==='NFM'?' selected':'')+'>NFM</option><option'+(c.mode==='DMR'?' selected':'')+'>DMR</option><option'+(c.mode==='TETRA'?' selected':'')+'>TETRA</option></select></label><label class="field">Frekans / MHz<input id="edit-frequency" type="number" min="1" step=".00001" value="'+c.frequency+'"></label></div><div class="field-row"><label class="field">Kanal aralığı<select><option>12,5 kHz</option><option>6,25 kHz</option><option>25 kHz</option></select></label><label class="field">Eşik / dBFS<input type="number" value="-60" min="-120" max="0"></label></div><div id="mode-fields">'+modeFields(c.mode)+'</div><p class="helper">Bu taslakta ad, mod ve frekans önizlemeye uygulanır. Diğer alanlar yerleşim örneğidir; ayarlar diske kaydedilmez.</p><div class="notice">'+icon('CircleAlert')+'<span>Alım açıkken kaydetmek için önce alımın durdurulması gerekir.</span></div>',
    button('Vazgeç','close-drawer',null)+button('Önizlemeye uygula','save-channel','Check','primary'));
}
function modeFields(mode) {
  if(mode==='DMR')return '<div class="field-row"><label class="field">Color code<input placeholder="Tümü" type="number" min="0" max="15" value="1"></label><label class="field">Slot filtresi<select><option>Tümü</option><option>Slot 1</option><option>Slot 2</option></select></label></div><p class="helper" style="margin-top:10px">DMR: 12,5 kHz RF kanalı. Slot ve color code, analog ton ayarlarından ayrıdır.</p>';
  if(mode==='NFM')return '<div class="field-row"><label class="field">Squelch türü<select><option>CSQ / Taşıyıcı</option><option>CTCSS</option><option>DCS</option></select></label><label class="field">Ton / kod<input placeholder="CSQ için kullanılmaz" disabled></label></div>';
  return '<div class="notice">'+icon('CircleAlert')+'<span>TETRA deneysel. Destek ve saha kabulü doğrulanmadan etkin gösterilmez.</span></div>';
}
function confirmAction(title,description,label,callback) {
  const dialog=document.getElementById('confirmation');
  dialog.innerHTML='<h2 id="confirmation-title">'+title+'</h2><p>'+description+'</p><div class="confirmation-actions">'+button('Vazgeç','cancel-confirmation',null)+'<button class="button danger" id="confirm-action">'+label+'</button></div>';
  document.getElementById('confirm-action').onclick=()=>{dialog.close();callback();};
  dialog.showModal();
}
function saveChannel() {
  const name=document.getElementById('edit-name').value.trim(),frequency=Number(document.getElementById('edit-frequency').value),mode=document.getElementById('edit-mode').value;
  if(!name||!Number.isFinite(frequency)||frequency<=0){toast('Kanal adı ve geçerli bir frekans girin.');return;}
  const save=()=>{const c=lookup(state.selected);c.name=name;c.frequency=frequency.toFixed(5);c.mode=mode;if(mode==='TETRA'){c.enabled=false;c.status='disabled';}if(mode!=='DMR'){c.radio=null;c.group=null;c.slot=null;c.cc=null;c.caller=null;c.status=mode==='TETRA'?'disabled':'idle';}state.acquiring=false;state.measuring=false;document.getElementById('drawer').close();render();toast('Önizleme ayarları uygulandı. Alım durduruldu; gerçek cihaza değişiklik gönderilmedi.');};
  if(state.acquiring)confirmAction('Alımı durdur ve uygula?','Aktif kayıtlar tamamlanacak. Alım yeniden başlatılana kadar yeni çağrı kaydı alınmayacak.','Durdur ve uygula',save);else save();
}
function receiverToggle() {
  if(state.acquiring)confirmAction('Alım durdurulsun mu?','Bu kaynağa bağlı kanalların aktif kayıtları tamamlanacak. Alım yeniden başlatılana kadar yeni çağrı kaydı alınmayacak.','Alımı durdur',()=>{state.acquiring=false;render();toast('Önizleme: alım durduruldu.');});
  else{state.acquiring=true;state.measuring=false;render();toast('Önizleme: alım senaryosu başlatıldı.');}
}
function startMeasurement() {
  const start=()=>{state.acquiring=false;state.measuring=true;state.view='spectrum';render();toast('Ölçüm senaryosu açıldı; gösterilen grafik temsili.');};
  if(state.acquiring)confirmAction('Kayıttan ölçüme geçilsin mi?','Aktif kayıtlar tamamlanacak. Spektrum ölçümü boyunca bu USB alıcıdan çağrı kaydı alınmayacak.','Alımı durdur, ölçüme geç',start);else start();
}
const actions = {
  'archive':()=>navigate('archive'),'sources':()=>navigate('sources'),'edit-selected':()=>editChannel(state.selected),
  'layout':()=>showDrawer('Kanal düzeni','<label class="field">Sütun sayısı<select id="column-layout"><option value="auto">Otomatik / pencereye göre</option><option value="2">2 sütun</option><option value="3">3 sütun</option></select></label><p class="helper">Kartların sırası korunur. Dar pencerede sütun sayısı okunurluk için azalır.</p>',button('Tamam','close-drawer',null)),
  'close-drawer':()=>document.getElementById('drawer').close(),'cancel-confirmation':()=>document.getElementById('confirmation').close(),
  'save-channel':saveChannel,'measurement':startMeasurement,'stop-measurement':()=>{state.measuring=false;render();toast('Ölçüm durduruldu. Çağrı alımını üst çubuktan başlatabilirsiniz.');},
  'reset-filters':()=>{document.getElementById('archive-search').value='';document.getElementById('archive-date').value='2026-09-12';document.getElementById('archive-slot').value='';filterRecords();},
  'filter-current-channel':()=>{document.getElementById('archive-search').value=lookup(records.find(r=>r.id===state.record).channel).name;filterRecords();},
  'playback':()=>{const r=records.find(r=>r.id===state.record);if(state.progress>=r.seconds)state.progress=0;state.playing=!state.playing;document.getElementById('player-container').innerHTML=player();mountIcons();},
  'speed':()=>{state.speed=state.speed===1?1.5:state.speed===1.5?2:1;document.getElementById('speed-button').textContent=state.speed+'×';},
  'receiver-settings':()=>showDrawer('Alıcı ayarları','<label class="field">Kaynak<input value="USB · RTL-SDR 01" disabled></label><div class="field-row"><label class="field">Kazanç / dB<input value="19" type="number"></label><label class="field">PPM düzeltme<input value="0" type="number"></label></div><label class="field">Alım biçimi<select id="receive-mode"><option>Sabit / bant içi</option><option>Sıralı tarama</option></select></label><p class="helper" id="receive-help">Sabit alım: kanallar kullanılabilir RF bandına sığmalıdır.</p><p class="helper">Bu panel görsel yerleşim örneğidir; alıcı parametreleri donanıma uygulanmaz.</p>',button('Kapat','close-drawer',null)),
  'network-info':()=>showDrawer('Ağ bağlantısı türleri','<h3>rtl_tcp / IQ</h3><p class="helper">Ethernet üzerinden ham SDR verisi. Sunucu adresi ve portu kaynağa aittir.</p><h3>Hytera / Repeater</h3><p class="helper">Üreticiye özgü ses ve olay entegrasyonu. Bağlantı kurulması, sesin doğru çözüldüğü anlamına gelmez. Ses, metadata ve kayıt durumları ayrı doğrulanır.</p>',button('Kapat','close-drawer',null))
};
document.addEventListener('click',event=>{
  const b=event.target.closest('button');
  if(!b) {const row=event.target.closest('[data-record-row]');if(row&&state.view==='archive')selectRecord(row.dataset.recordRow);return;}
  if(b.dataset.direction)setDirection(b.dataset.direction);
  else if(b.dataset.view)navigate(b.dataset.view);
  else if(b.dataset.selectChannel)selectChannel(b.dataset.selectChannel);
  else if(b.dataset.editChannel)editChannel(b.dataset.editChannel);
  else if(b.dataset.playRecord)selectRecord(b.dataset.playRecord,true);
  else if(b.dataset.mute) {
    const id=Number(b.dataset.mute);state.muted.has(id)?state.muted.delete(id):state.muted.add(id);const drawer=document.getElementById('drawer');if(drawer.open)drawer.close();filterChannels();const detail=document.getElementById('live-detail');if(detail)detail.innerHTML=liveDetail(lookup(state.selected));mountIcons();toast(state.muted.has(id)?'Yerel dinleme sesi kapalı. Ses kaydı devam eder.':'Yerel dinleme sesi açık.');
  }
  else if(b.dataset.channelHistory){document.getElementById('drawer').close();navigate('archive');document.getElementById('archive-search').value=lookup(b.dataset.channelHistory).name;filterRecords();}
  else if(b.dataset.alias)showDrawer('Kimlik eşleştirmesi','<label class="field">Sistem / müşteri<input value="Demo tesis" disabled></label><label class="field">Kimlik<input value="'+b.dataset.alias+'" disabled></label><label class="field">Görünen ad<input value="'+escapeHtml(b.dataset.aliasName)+'" readonly></label><p class="helper">Aynı ID, farklı sistemlerde ayrı eşleştirilir. Bu prototip rehber verisini kaydetmez.</p>',button('Kapat','close-drawer',null));
  else if(b.dataset.action&&actions[b.dataset.action])actions[b.dataset.action]();
});
document.getElementById('receiver-toggle').addEventListener('click',receiverToggle);
document.addEventListener('input',e=>{
  if(['channel-search','active-only'].includes(e.target.id))filterChannels();
  if(['archive-search','archive-date','archive-slot'].includes(e.target.id))filterRecords();
  if(e.target.id==='seek'){state.progress=Number(e.target.value);updatePlayerPosition();}
});
document.addEventListener('change',e=>{
  if(e.target.id==='column-layout'){state.columns=e.target.value;filterChannels();}
  if(e.target.id==='edit-mode'){document.getElementById('mode-fields').innerHTML=modeFields(e.target.value);mountIcons();}
  if(e.target.id==='receive-mode')document.getElementById('receive-help').textContent=e.target.value.startsWith('Sıralı')?'Tarama: tek tuner kanalları sırayla dinler. Diğer kanallar sıra bekler; eşzamanlı kayıt garantisi verilmez.':'Sabit alım: kanallar kullanılabilir RF bandına sığmalıdır.';
  if(['archive-slot','archive-date'].includes(e.target.id))filterRecords();
});
document.addEventListener('dblclick',e=>{const row=e.target.closest('[data-record-row]');if(row)selectRecord(row.dataset.recordRow,true);});
function updatePlayerPosition(){
  if(state.view!=='archive')return;
  const r=records.find(r=>r.id===state.record);
  document.getElementById('play-time').textContent=duration(state.progress)+' / '+duration(r.seconds);
  document.getElementById('playhead').style.left=(state.progress/r.seconds*100)+'%';
  document.getElementById('seek').value=state.progress;
}
setInterval(()=>{
  if(!state.playing||state.view!=='archive')return;
  const r=records.find(r=>r.id===state.record);state.progress=Math.min(r.seconds,state.progress+.25*state.speed);updatePlayerPosition();
  if(state.progress>=r.seconds){state.playing=false;document.getElementById('play-button').innerHTML=icon('Play')+'Oynatımı önizle';mountIcons();}
},250);
const initial=location.hash.slice(1);
if(['operations','night','review'].includes(initial)){state.direction=initial;state.view=initial==='review'?'archive':'live';}
render();
