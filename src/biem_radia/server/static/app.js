"use strict";
const app = document.querySelector("#app");
let session = null,
  page = "",
  timer = null,
  busy = null,
  adminData = null,
  editId = null;
let setupToken = new URLSearchParams(location.hash.slice(1)).get("setup") || "";
let epoch = 0;
let pageOffset = 0;
const pendingRequests = new Set();
function invalidateView() {
  epoch++;
  for (const controller of pendingRequests) controller.abort();
  pendingRequests.clear();
}
function setSession(value) {
  invalidateView();
  session = value;
  adminData = null;
  settingsFocus = null;
  editId = null;
  liveStates = [];
  lastLocation = null;
  lastSessionCheck = 0;
  if (mapURL) URL.revokeObjectURL(mapURL);
  mapURL = null;
}
history.replaceState(null, "", location.pathname);
let theme = localStorage.getItem("biem-theme") || "light";
document.documentElement.dataset.theme = theme;
let audioContext = null,
  listening = null,
  audioBusy = false,
  audioTimer = null,
  audioNext = 0;
let playbackURL = null,
  mapURL = null,
  liveStates = [],
  lastSessionCheck = 0;
const titles = {
  live: "Canlı izleme",
  archive: "Kayıt arşivi",
  messages: "Gelen mesajlar",
  map: "Harita",
  repeater: "Röle izleme",
  spectrum: "Spektrum",
  admin: "Kullanıcılar ve yetkiler",
  settings: "Alıcı / kanal ayarları",
};
const navSpec = [
  ["live", "◉", "live.view"],
  ["archive", "▤", "archive.view"],
  ["messages", "✉", "messages.view"],
  ["map", "⌖", "map.view"],
  ["repeater", "⇄", "repeater.view"],
  ["spectrum", "∿", "spectrum.view"],
  ["settings", "⚙", "admin"],
  ["admin", "⚙", "admin"],
];
const can = (p) =>
  !!session && (session.user.admin || session.user.permissions.includes(p));
function el(tag, attrs = {}, ...children) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k === "class") n.className = v;
    else if (k === "checked" || k === "disabled") n[k] = v;
    else n.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c !== null && c !== undefined)
      n.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return n;
}
function button(text, fn, cls = "") {
  return el("button", { type: "button", class: cls, onclick: fn }, text);
}
function note(text) {
  if (!text || text === "İstek iptal edildi." || text.includes("aborted"))
    return;
  const n = document.querySelector("#notice");
  n.textContent = text;
  n.classList.add("visible");
  clearTimeout(note.timeout);
  note.timeout = setTimeout(() => n.classList.remove("visible"), 6000);
}
function toggleTheme() {
  theme = theme === "light" ? "dark" : "light";
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("biem-theme", theme);
}
async function api(url, method = "GET", body) {
  const version = epoch;
  const controller = new AbortController();
  pendingRequests.add(controller);
  const headers = {};
  if (method !== "GET") {
    headers["Content-Type"] = "application/json";
    if (session) headers["X-CSRF-Token"] = session.csrf;
    if (url === "/api/setup") headers["X-Setup-Token"] = setupToken;
  }
  let r;
  try {
    r = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
      signal: controller.signal,
    });
  } finally {
    pendingRequests.delete(controller);
  }
  if (version !== epoch) throw new Error("İstek iptal edildi.");
  if (!r.ok) {
    let msg = "Sunucuya ulaşılamadı.";
    try {
      msg = (await r.json()).detail || msg;
    } catch {}
    if (r.status === 401 && session) {
      setSession(null);
      stopAudio();
      showLogin(false);
    }
    throw new Error(msg);
  }
  return r;
}
async function json(url, method = "GET", body) {
  const version = epoch;
  const result = await (await api(url, method, body)).json();
  if (version !== epoch) throw new Error("İstek iptal edildi.");
  return result;
}
function logo() {
  return el("img", {
    class: "logo",
    src: "/assets/logo.png",
    alt: "Biem Elektronik",
  });
}
function field(label, input) {
  return el("label", { class: "field" }, label, input);
}
function checkbox(label, name, checked = false) {
  return el(
    "label",
    { class: "check" },
    el("input", { type: "checkbox", name, checked }),
    label,
  );
}
function clearTimers() {
  clearInterval(timer);
  timer = null;
}
function showLogin(setup) {
  invalidateView();
  clearTimers();
  page = "";
  app.replaceChildren();
  const user = el("input", {
    name: "username",
    autocomplete: "username",
    required: true,
    minlength: 3,
    maxlength: 40,
    placeholder: setup ? "Yönetici kullanıcı adı" : "Kullanıcı adınız",
  });
  const pass = el("input", {
    name: "password",
    type: "password",
    autocomplete: setup ? "new-password" : "current-password",
    required: true,
    minlength: setup ? 12 : 1,
    maxlength: 128,
    placeholder: setup ? "En az 12 karakter" : "Şifreniz",
  });
  const err = el("div", { class: "error-inline", role: "alert" });
  const submit = el(
    "button",
    { class: "primary", type: "submit" },
    setup ? "Yönetici hesabını oluştur" : "Giriş yap →",
  );
  const form = el(
    "form",
    {
      onsubmit: async (e) => {
        e.preventDefault();
        submit.disabled = true;
        err.textContent = "";
        try {
          if (setup) {
            await json("/api/setup", "POST", {
              username: user.value,
              password: pass.value,
            });
            setupToken = "";
          }
          setSession(
            await json("/api/login", "POST", {
              username: user.value,
              password: pass.value,
            }),
          );
          pass.value = "";
          showShell();
        } catch (ex) {
          err.textContent = ex.message;
        } finally {
          submit.disabled = false;
        }
      },
    },
    field("Kullanıcı adı", user),
    field("Şifre", pass),
    err,
    submit,
  );
  app.append(
    el(
      "div",
      { class: "login-wrap" },
      el(
        "section",
        { class: "login-intro" },
        logo(),
        el("div", { class: "eyebrow" }, "RADIO INTEGRATED SOLUTION"),
        el("h1", {}, "Tüm kanallar.", el("br"), "Tek merkez."),
        el(
          "p",
          { class: "muted" },
          "Ofiste kesintisiz alım ve kayıt. Ekibiniz için yetkilendirilmiş, ortak bir çalışma alanı.",
        ),
        el(
          "div",
          { class: "row" },
          el("span", { class: "badge" }, "BIEM-ICC-SERVER"),
          el("span", { class: "small" }, "Güvenli ekip erişimi"),
        ),
      ),
      el(
        "section",
        { class: "login-form" },
        el(
          "div",
          {},
          el(
            "div",
            { class: "row spread" },
            el(
              "span",
              { class: "eyebrow" },
              setup ? "İLK KURULUM" : "ÇALIŞMA ALANINA GİRİŞ",
            ),
            button("◐", toggleTheme),
          ),
          el("h2", {}, setup ? "Yöneticiyi tanımlayın" : "Tekrar hoş geldiniz"),
          el(
            "p",
            { class: "muted" },
            setup
              ? "Bu hesap kullanıcıları ve erişim yetkilerini yönetecek. Şifrenizi güvenli bir yerde saklayın."
              : "Kullanıcı hesabınıza tanımlanan kanallara ve ekranlara erişin.",
          ),
          form,
          el(
            "p",
            { class: "login-foot muted" },
            setup
              ? "İlk kurulum yalnızca sunucu bilgisayarında yapılır."
              : "Erişim için sistem yöneticinizden bir hesap isteyin.",
          ),
        ),
      ),
    ),
  );
}
function showShell() {
  clearTimers();
  app.replaceChildren();
  const sidebar = el(
    "aside",
    { class: "sidebar" },
    el("div", { class: "eyebrow" }, "OPERASYON"),
  );
  for (const [key, icon, permission] of navSpec) {
    if (permission === "admin" ? !session.user.admin : !can(permission))
      continue;
    sidebar.append(
      button(icon + "  " + titles[key], () => navigate(key), "nav"),
    );
    sidebar.lastChild.dataset.page = key;
  }
  sidebar.append(
    el(
      "div",
      { class: "sidebar-foot" },
      "BIEM-ICC-SERVER",
      el("br"),
      "Alım sunucuda devam eder.",
      el("br"),
      "Tarayıcıyı kapatabilirsiniz.",
    ),
  );
  app.append(
    el(
      "header",
      { class: "header" },
      el(
        "div",
        { class: "brand" },
        logo(),
        el(
          "div",
          {},
          el("strong", {}, "BIEM-ICC-SERVER"),
          el("small", {}, "MERKEZİ TELSİZ İZLEME VE KAYIT"),
        ),
      ),
      el(
        "div",
        { class: "row" },
        el(
          "span",
          { class: "user-label badge" },
          session.user.username,
          session.user.admin ? " · Yönetici" : " · Kullanıcı",
        ),
        button("◐", toggleTheme),
        button("Çıkış", async () => {
          try {
            await json("/api/logout", "POST", {});
          } catch {}
          setSession(null);
          stopAudio();
          showLogin(false);
        }),
      ),
    ),
    el(
      "div",
      { class: "layout" },
      sidebar,
      el("main", { class: "main", id: "main" }),
    ),
  );
  const first = navSpec.find(([, , p]) =>
    p === "admin" ? session.user.admin : can(p),
  );
  if (first) navigate(first[0]);
  else
    document
      .querySelector("#main")
      .append(
        el(
          "div",
          { class: "empty" },
          "Hesabınıza henüz ekran yetkisi verilmedi. Yöneticinizle iletişime geçin.",
        ),
      );
}
function heading(subtitle = "") {
  return el(
    "div",
    { class: "page-heading" },
    el(
      "div",
      {},
      el("h1", {}, titles[page]),
      el("p", { class: "muted" }, subtitle),
    ),
    el("span", { class: "badge" }, "● Sunucu bağlantısı"),
  );
}
function targetControls(target) {
  return [
    button("▶ Başlat", () => control(target, "start"), "primary"),
    button("■ Durdur", () => control(target, "stop")),
  ];
}
async function control(target, action, extra = {}) {
  try {
    await json("/api/control", "POST", { target, action, ...extra });
    note(
      action === "start"
        ? "Başlatma isteği alındı."
        : "Durdurma isteği alındı; kayıt tamamlanıyor.",
    );
    await refresh();
  } catch (e) {
    note(e.message);
  }
}
async function navigate(next) {
  invalidateView();
  adminData = null;
  pageOffset = 0;
  stopAudio();
  clearTimers();
  page = next;
  document
    .querySelectorAll(".nav")
    .forEach((n) => n.classList.toggle("selected", n.dataset.page === next));
  const m = document.querySelector("#main");
  m.replaceChildren(
    heading(
      next === "admin"
        ? "Kimin, hangi kanala ve ekrana erişeceğini siz belirleyin."
        : "Sunucudan gelen güncel bilgiler · Yetkiniz kapsamındaki kanallar",
    ),
  );
  if (next === "live") {
    const bar = el("div", { class: "toolbar" });
    if (can("receiver.control"))
      bar.append(
        el("span", { class: "muted" }, "SDR alımı"),
        ...targetControls("receiver"),
      );
    if (session.user.admin)
      bar.append(button("⚙ Kanal ayarları", () => navigate("settings")));
    m.append(
      bar,
      el("div", { id: "live-status", class: "muted" }),
      el("div", { id: "content", class: "channel-grid" }),
    );
  } else if (["archive", "messages"].includes(next)) {
    const search = el("input", {
      type: "search",
      id: "search",
      placeholder:
        next === "archive"
          ? "Kanal, telsiz ID veya grup ara"
          : "Mesaj içinde ara",
      "aria-label": "Ara",
    });
    m.append(
      el(
        "form",
        {
          class: "toolbar",
          onsubmit: (e) => {
            e.preventDefault();
            pageOffset = 0;
            refresh();
          },
        },
        search,
        el("button", { type: "submit" }, "Ara"),
      ),
      el("div", { id: "player" }),
      el("div", { id: "content" }),
    );
  } else if (next === "admin") {
    m.append(el("div", { id: "content" }));
  } else if (next === "settings") {
    m.append(el("div", { id: "content" }));
    await loadSettings();
  } else if (next === "map") {
    mapCenter = { lon: 35, lat: 39, zoom: 6 };
    m.append(
      el(
        "div",
        { class: "toolbar" },
        button("Türkiye", () => {
          mapCenter = { lon: 35, lat: 39, zoom: 6 };
          loadMap();
        }),
        button("Son konuma yaklaş", focusLocation),
        button("＋", () => mapStep(1)),
        button("−", () => mapStep(-1)),
        button("←", () => panMap(-1, 0)),
        button("→", () => panMap(1, 0)),
        button("↑", () => panMap(0, 1)),
        button("↓", () => panMap(0, -1)),
      ),
      el("p", { id: "map-position", class: "muted" }),
      el("div", { class: "map-frame", id: "map-frame" }),
      el(
        "p",
        { class: "map-note" },
        "Çevrimdışı sokak haritası · © OpenStreetMap katkıcıları / Geofabrik · ODbL 1.0. Ayrıntı sunucudaki pakete bağlıdır.",
      ),
    );
    loadMap();
  } else if (next === "repeater") {
    const bar = el(
      "div",
      { class: "toolbar" },
      button("RSSI oku", async () => {
        try {
          await json("/api/repeater/rssi", "POST", {});
          note("İki slot için güncel RSSI isteniyor.");
        } catch (e) {
          note(e.message);
        }
      }),
    );
    if (can("receiver.control")) bar.append(...targetControls("hytera"));
    m.append(bar, el("div", { id: "content" }));
  } else if (next === "spectrum") {
    if (can("spectrum.control")) {
      const low = el("input", {
          type: "number",
          value: 420,
          step: 0.001,
          "aria-label": "Başlangıç MHz",
        }),
        high = el("input", {
          type: "number",
          value: 421,
          step: 0.001,
          "aria-label": "Bitiş MHz",
        });
      m.append(
        el(
          "div",
          { class: "toolbar" },
          field("Başlangıç MHz", low),
          field("Bitiş MHz", high),
          button(
            "Ölçümü başlat",
            () =>
              control("spectrum", "start", {
                low: Number(low.value),
                high: Number(high.value),
              }),
            "primary",
          ),
          button("Durdur", () => control("spectrum", "stop")),
        ),
      );
    }
    m.append(
      el(
        "p",
        { class: "muted" },
        "Tüm RF bandı için yetkili görünüm · Spektrum ve SDR canlı alımı aynı cihazı sırayla kullanır.",
      ),
      el("p", { id: "spectrum-status", class: "muted" }),
      el("canvas", {
        id: "spectrum",
        class: "spectrum",
        width: 1100,
        height: 340,
      }),
    );
  }
  await refresh();
  timer = setInterval(
    refresh,
    ["live", "spectrum"].includes(next) ? 1000 : 5000,
  );
}
async function refresh() {
  if (busy === epoch || !session) return;
  const version = epoch;
  busy = version;
  const current = page;
  try {
    if (Date.now() - lastSessionCheck > 8000) {
      await json("/api/me");
      lastSessionCheck = Date.now();
    }
    if (current === "live") {
      const d = await json("/api/live");
      if (current !== page) return;
      liveStates = d.channels;
      document.querySelector("#live-status").textContent = d.status || "";
      document.querySelector("#live-status").className = "muted";
      renderLive(d);
    } else if (current === "archive" || current === "messages") {
      const q = document.querySelector("#search").value;
      const d = await json(
        "/api/" +
          (current === "archive" ? "calls" : "messages") +
          "?q=" +
          encodeURIComponent(q) +
          "&offset=" +
          pageOffset,
      );
      if (current === page) renderTable(d, current);
    } else if (current === "admin") {
      if (!adminData) {
        adminData = await json("/api/admin");
        if (current === page) renderAdmin();
      }
    } else if (current === "map") {
      const d = await json("/api/map/location");
      lastLocation = d.location;
      if (current === page)
        document.querySelector("#map-position").textContent = d.location
          ? `${d.location.channel} · Telsiz ${d.location.source_id} · ${d.location.latitude.toFixed(6)}, ${d.location.longitude.toFixed(6)} · ${date(d.location.observed_utc)}`
          : "Yetkili kanallarınız için son konum bilgisi bulunmuyor.";
    } else if (current === "repeater") {
      const d = await json("/api/repeater");
      if (current === page) renderRepeater(d);
    } else if (current === "spectrum") {
      const d = await json("/api/spectrum");
      if (current === page) drawSpectrum(d);
    }
  } catch (e) {
    if (session && version === epoch) {
      note(e.message);
      if (current === "live") {
        await stopAudio();
        const label = document.querySelector("#live-status");
        label.textContent =
          "Sunucu bağlantısı kesildi. Gösterilen veriler güncel değil.";
        label.className = "connection-lost";
        renderLive({
          channels: liveStates.map((c) => ({ ...c, connected: false })),
        });
      }
    }
  } finally {
    if (busy === version) busy = null;
  }
}
function date(v) {
  return v ? new Date(v).toLocaleString("tr-TR") : "—";
}
function num(v, suffix = "", digits = 1) {
  return typeof v === "number" ? v.toFixed(digits) + suffix : "—";
}
function renderLive(data) {
  const root = document.querySelector("#content");
  root.replaceChildren();
  if (!data.channels.length) {
    root.append(
      el(
        "div",
        { class: "empty" },
        "Görüntüleyebileceğiniz kanal tanımlı değil.",
      ),
    );
    return;
  }
  for (const c of data.channels) {
    const signal =
        typeof c.level === "number" && c.level >= (c.squelch_db ?? -100),
      isAudio = !!c.audio_present,
      gray = !c.connected,
      noaudio = c.connected && signal && !isAudio;
    const label = gray
      ? !c.enabled
        ? "Kanal devre dışı"
        : c.frequency_hz && !data.running
          ? "Alım kapalı"
          : "Bağlı değil"
      : noaudio
        ? "Sinyal var · ses yok"
        : isAudio
          ? "Ses alınıyor"
          : "Kanal hazır · sinyal bekleniyor";
    const card = el(
      "article",
      {
        class:
          "panel channel" +
          (gray ? " disconnected" : noaudio ? " noaudio" : ""),
      },
      el(
        "div",
        { class: "row spread" },
        el("h2", {}, c.name),
        el("span", { class: "badge orange" }, c.mode),
      ),
      el(
        "p",
        { class: "muted mono" },
        num(c.frequency_hz ? c.frequency_hz / 1e6 : null, " MHz", 5),
      ),
      el(
        "div",
        { class: "status-line " + (gray ? "gray" : noaudio ? "red" : "green") },
        "● " + label,
      ),
    );
    for (const [label, value] of [
      ["RF", c.level],
      ["SES", c.audio_dbfs],
    ])
      card.append(
        el(
          "div",
          { class: "meter-row" },
          label,
          el("meter", {
            min: -120,
            max: 0,
            value: gray ? -120 : (value ?? -120),
            "aria-label": label + " seviyesi",
          }),
          num(gray ? null : value, " dBFS", 0),
        ),
      );
    card.append(
      el(
        "div",
        { class: "channel-meta" },
        typeof c.data === "string" ? c.data : "Senkron / çağrı bekleniyor",
        el("br"),
        el(
          "span",
          { class: "mono" },
          "Kayma " +
            num(
              c.offset_hz === undefined ? null : c.offset_hz / 1000,
              " kHz",
              2,
            ),
        ),
      ),
    );
    const actions = el("div", { class: "actions" });
    if (can("live.listen") && c.streams?.length > 1) {
      const select = el("select", {
        "aria-label": c.name + " ses akışı",
        onchange: () => toggleListen(c, select.value),
      });
      select.append(el("option", { value: "" }, "Ses akışı seçin…"));
      for (const stream of c.streams)
        select.append(
          el("option", { value: stream.id }, stream.label + " · " + stream.id),
        );
      if (listening?.channel === c.name) select.value = listening.stream || "";
      card.append(select);
    }
    if (can("live.listen"))
      actions.append(
        button(
          listening?.channel === c.name ? "■ Dinlemeyi bırak" : "▶ Dinle",
          () => toggleListen(c),
        ),
      );
    if (can("messages.view"))
      actions.append(button("✉ Mesajlar", () => navigate("messages")));
    if (session.user.admin && c.frequency_hz)
      actions.append(
        button("⚙ Ayarlar", () => {
          settingsFocus = c.name;
          navigate("settings");
        }),
      );
    card.append(actions);
    root.append(card);
  }
}
async function stopAudio() {
  listening = null;
  clearInterval(audioTimer);
  audioTimer = null;
  const old = audioContext;
  audioContext = null;
  audioNext = 0;
  if (playbackURL) {
    URL.revokeObjectURL(playbackURL);
    playbackURL = null;
  }
  document.querySelectorAll("audio").forEach((a) => {
    a.pause();
    a.removeAttribute("src");
    a.load();
  });
  if (old) await old.close();
}
async function toggleListen(c, stream = null) {
  const version = epoch;
  if (listening?.channel === c.name && !stream) {
    await stopAudio();
    refresh();
    return;
  }
  await stopAudio();
  if (version !== epoch) return;
  audioContext = new AudioContext();
  await audioContext.resume();
  if (version !== epoch) {
    await stopAudio();
    return;
  }
  listening = {
    channel: c.name,
    stream: stream || c.streams?.[0]?.id || null,
    pinned: !!stream,
    after: 0,
  };
  audioTimer = setInterval(pullAudio, 220);
  note(c.name + " canlı dinleme açıldı.");
  refresh();
}
async function pullAudio() {
  if (audioBusy || !listening || !audioContext) return;
  audioBusy = true;
  const selected = listening,
    ctx = audioContext;
  try {
    const state = liveStates.find((c) => c.name === selected.channel);
    if (!state?.connected) return;
    if (
      !selected.stream ||
      (!selected.pinned &&
        !state.streams?.some((s) => s.id === selected.stream))
    ) {
      selected.stream = state.streams?.[0]?.id || null;
      selected.after = 0;
    }
    if (!selected.stream) return;
    const d = await json(
      "/api/live/audio?channel=" +
        encodeURIComponent(selected.channel) +
        "&stream=" +
        encodeURIComponent(selected.stream) +
        "&after=" +
        selected.after,
    );
    if (listening !== selected || ctx !== audioContext) return;
    for (const p of d.packets) {
      selected.after = Math.max(selected.after, p.sequence);
      const raw = atob(p.pcm),
        buffer = ctx.createBuffer(1, raw.length / 2, p.rate),
        samples = buffer.getChannelData(0);
      for (let i = 0; i < samples.length; i++) {
        let v = raw.charCodeAt(i * 2) | (raw.charCodeAt(i * 2 + 1) << 8);
        samples[i] = (v > 32767 ? v - 65536 : v) / 32768;
      }
      if (audioNext - ctx.currentTime > 1.5) continue;
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      audioNext = Math.max(audioNext, ctx.currentTime + 0.04);
      source.start(audioNext);
      audioNext += buffer.duration;
    }
  } catch (e) {
    await stopAudio();
    note(e.message);
  } finally {
    audioBusy = false;
  }
}
function renderTable(data, kind) {
  const root = document.querySelector("#content");
  if (!data.rows.length) {
    root.replaceChildren(
      el(
        "div",
        { class: "empty" },
        "Gösterilecek kayıt yok. Yalnızca izin verilen kanallar listelenir.",
      ),
    );
    return;
  }
  const table = el("table");
  const headers =
    kind === "archive"
      ? [
          "Tarih / saat",
          "Kanal",
          "Kaynak",
          "ID / Grup",
          "Slot / CC",
          "Süre",
          "Dinle",
        ]
      : ["Tarih / saat", "Kanal", "ID / Grup", "Tür", "Mesaj"];
  table.append(
    el(
      "thead",
      {},
      el(
        "tr",
        {},
        headers.map((h) => el("th", {}, h)),
      ),
    ),
  );
  const tbody = el("tbody");
  for (const r of data.rows) {
    const row = el("tr");
    if (kind === "archive") {
      const slot =
        r.protocol_slot ??
        r.slot ??
        (r.decoder_slot ? `${r.decoder_slot} (çözücü)` : "—");
      row.append(
        el("td", {}, date(r.started_utc)),
        el(
          "td",
          {},
          r.title || r.channel,
          el(
            "div",
            { class: "muted small" },
            num(r.frequency_hz ? r.frequency_hz / 1e6 : null, " MHz", 5),
          ),
        ),
        el("td", {}, r.source),
        el("td", {}, `${r.radio_id ?? "—"} / ${r.group_id ?? "—"}`),
        el("td", {}, `${slot} / CC ${r.color_code ?? "—"}`),
        el("td", {}, num(r.duration, " sn", 1)),
        el(
          "td",
          {},
          can("archive.play")
            ? button("▷ Dinle", () => playCall(r))
            : "Yetki yok",
        ),
      );
    } else
      row.append(
        el("td", {}, r.at_local),
        el("td", {}, r.channel),
        el("td", {}, `${r.source_id || "—"} / ${r.group_id || "—"}`),
        el("td", {}, r.kind),
        el("td", { class: "wrap" }, r.text),
      );
    tbody.append(row);
  }
  table.append(tbody);
  root.replaceChildren(
    el("div", { class: "table-wrap" }, table),
    el(
      "p",
      { class: "muted small" },
      `${pageOffset + 1}–${pageOffset + data.rows.length} arası sonuçlar`,
    ),
  );
  const previous = button("← Önceki", () => {
    pageOffset = Math.max(0, pageOffset - 100);
    refresh();
  });
  const next = button("Sonraki →", () => {
    pageOffset += 100;
    refresh();
  });
  previous.disabled = pageOffset === 0;
  next.disabled = !data.more;
  root.append(el("div", { class: "row" }, previous, next));
}
async function playCall(r) {
  const version = epoch;
  try {
    await stopAudio();
    const response = await api(
      "/api/calls/" + encodeURIComponent(r.id) + "/audio",
    );
    const blob = await response.blob();
    if (version !== epoch) return;
    playbackURL = URL.createObjectURL(blob);
    const audio = el("audio", { controls: true, src: playbackURL });
    document
      .querySelector("#player")
      .replaceChildren(
        el(
          "div",
          { class: "panel player" },
          el("strong", {}, r.channel + " · " + date(r.started_utc)),
          audio,
        ),
      );
    await audio.play();
  } catch (e) {
    note(e.message);
  }
}
function renderAdmin() {
  const root = document.querySelector("#content");
  root.replaceChildren();
  const list = el(
    "div",
    { class: "stack" },
    el(
      "div",
      { class: "row spread" },
      el("h2", {}, "Kullanıcılar"),
      button(
        "＋ Yeni kullanıcı",
        () => {
          editId = null;
          renderAdmin();
        },
        "primary",
      ),
    ),
  );
  for (const u of adminData.users)
    list.append(
      el(
        "div",
        { class: "user-item" + (editId === u.id ? " selected" : "") },
        el(
          "div",
          {},
          el("strong", {}, u.username),
          el(
            "p",
            { class: "muted small" },
            `${u.admin ? "Yönetici" : "Kullanıcı"} · ${u.enabled ? "Etkin" : "Kapalı"}`,
          ),
        ),
        button("Düzenle", () => {
          editId = u.id;
          renderAdmin();
        }),
      ),
    );
  const u = adminData.users.find((v) => v.id === editId) || {
    username: "",
    permissions: [],
    channels: [],
    enabled: true,
    admin: false,
    all_channels: false,
  };
  const username = el("input", {
      name: "username",
      value: u.username,
      required: true,
      minlength: 3,
      maxlength: 40,
      autocomplete: "off",
    }),
    password = el("input", {
      name: "password",
      type: "password",
      minlength: 12,
      maxlength: 128,
      autocomplete: "new-password",
      placeholder: editId ? "Değişmeyecekse boş bırakın" : "En az 12 karakter",
    });
  if (!editId) password.required = true;
  const form = el(
    "form",
    { class: "panel" },
    el("div", { class: "eyebrow" }, "ERİŞİM POLİTİKASI"),
    el(
      "h2",
      {},
      editId ? u.username + " · hesabı düzenle" : "Yeni hesap oluştur",
    ),
    el(
      "div",
      { class: "row" },
      field("Kullanıcı adı", username),
      field("Şifre", password),
    ),
    checkbox("Hesap etkin", "enabled", u.enabled),
    checkbox(
      "Yönetici · tüm ekranlar, tüm kanallar ve kullanıcı yönetimi",
      "admin",
      u.admin,
    ),
  );
  const perms = el(
    "fieldset",
    { class: "check-group" },
    el("legend", {}, "Ekranlar ve işlemler"),
    el(
      "div",
      { class: "checks" },
      Object.entries(adminData.permissions).map(([key, label]) =>
        checkbox(label, "perm:" + key, u.permissions.includes(key)),
      ),
    ),
  );
  const scopes = el(
    "fieldset",
    { class: "check-group" },
    el("legend", {}, "Kanal erişimi"),
    checkbox(
      "Tüm mevcut ve gelecekteki kanallar",
      "all_channels",
      u.all_channels,
    ),
    el(
      "div",
      { class: "checks" },
      adminData.channels.map((name) =>
        checkbox(name, "channel:" + name, u.channels.includes(name)),
      ),
    ),
  );
  form.append(
    perms,
    scopes,
    el(
      "div",
      { class: "info" },
      "İşaretlenmeyen yetki kapalıdır. Kanal seçilmezse kanal verisi gösterilmez. Spektrum tüm bandı; alım kontrolü tüm kanalları etkiler. Yetki veya şifre değişikliği kullanıcının oturumlarını kapatır.",
    ),
    el(
      "button",
      { class: "primary", type: "submit" },
      editId ? "Değişiklikleri kaydet" : "Kullanıcıyı oluştur",
    ),
  );
  function adjust() {
    const admin = form.elements.namedItem("admin").checked;
    perms.disabled = admin;
    scopes.disabled = admin;
    const all = form.elements.namedItem("all_channels").checked;
    scopes
      .querySelectorAll('[name^="channel:"]')
      .forEach((i) => (i.disabled = all));
  }
  form.addEventListener("change", (e) => {
    const n = e.target.name;
    if (n?.startsWith("perm:")) {
      const key = n.slice(5);
      if (e.target.checked && adminData.dependencies[key])
        form.elements.namedItem("perm:" + adminData.dependencies[key]).checked =
          true;
      else if (!e.target.checked)
        for (const [child, parent] of Object.entries(adminData.dependencies))
          if (parent === key)
            form.elements.namedItem("perm:" + child).checked = false;
    }
    adjust();
  });
  adjust();
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const vals = new FormData(form);
    const body = {
      username: username.value,
      password: password.value,
      admin: form.elements.namedItem("admin").checked,
      enabled: form.elements.namedItem("enabled").checked,
      all_channels: form.elements.namedItem("all_channels").checked,
      permissions: [...vals.keys()]
        .filter((k) => k.startsWith("perm:"))
        .map((k) => k.slice(5)),
      channels: [...vals.keys()]
        .filter((k) => k.startsWith("channel:"))
        .map((k) => k.slice(8)),
    };
    const submit = form.querySelector("[type=submit]");
    submit.disabled = true;
    try {
      await json(
        "/api/admin/users" + (editId ? "/" + editId : ""),
        editId ? "PUT" : "POST",
        body,
      );
      password.value = "";
      adminData = null;
      note("Kullanıcı yetkileri kaydedildi.");
      await refresh();
    } catch (ex) {
      note(ex.message);
    } finally {
      submit.disabled = false;
    }
  });
  root.append(
    el(
      "div",
      { class: "admin-grid" },
      el(
        "div",
        { class: "stack" },
        el("section", { class: "panel" }, list),
        startupForm(),
      ),
      form,
    ),
  );
  const audit = el(
    "details",
    { class: "panel audit" },
    el("summary", {}, "Erişim ve yönetim günlüğü"),
  );
  const t = el(
    "table",
    {},
    el(
      "thead",
      {},
      el(
        "tr",
        {},
        ["Zaman", "Kullanıcı", "İşlem", "Hedef"].map((v) => el("th", {}, v)),
      ),
    ),
  );
  t.append(
    el(
      "tbody",
      {},
      adminData.history
        .slice(0, 50)
        .map((r) =>
          el(
            "tr",
            {},
            el("td", {}, date(r.at * 1000)),
            el("td", {}, r.actor),
            el("td", {}, r.action),
            el("td", {}, r.target),
          ),
        ),
    ),
  );
  audit.append(el("div", { class: "table-wrap" }, t));
  root.append(audit);
}
function startupForm() {
  const p = adminData.startup;
  const f = el(
    "form",
    { class: "panel" },
    el("h2", {}, "Sunucu başlangıcı"),
    el(
      "p",
      { class: "muted" },
      "Sunucu açılınca seçili alımlar otomatik başlar. Kanal ve RF ayarları mevcut yerel yapılandırmadan alınır.",
    ),
    checkbox("SDR alımını başlat", "receiver", p.receiver),
    checkbox("Hytera ses alımını başlat", "hytera", p.hytera),
    checkbox("Röle SNMP izlemesini başlat", "snmp", p.snmp),
    el("button", { type: "submit" }, "Başlangıcı kaydet"),
  );
  f.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await json(
        "/api/admin/startup",
        "PUT",
        Object.fromEntries(
          ["receiver", "hytera", "snmp"].map((k) => [
            k,
            f.elements.namedItem(k).checked,
          ]),
        ),
      );
      note("Başlangıç ayarları kaydedildi.");
    } catch (ex) {
      note(ex.message);
    }
  });
  return f;
}
let mapCenter = { lon: 35, lat: 39, zoom: 6 },
  lastLocation = null;
function mapStep(d) {
  mapCenter.zoom = Math.min(18, Math.max(5, mapCenter.zoom + d));
  loadMap();
}
function panMap(x, y) {
  const step = 90 / 2 ** mapCenter.zoom;
  mapCenter.lon = Math.min(46, Math.max(24, mapCenter.lon + x * step));
  mapCenter.lat = Math.min(43, Math.max(34, mapCenter.lat + y * step));
  loadMap();
}
function focusLocation() {
  if (!lastLocation) {
    note("Yetkili kanallar için konum bilgisi yok.");
    return;
  }
  mapCenter = {
    lon: lastLocation.longitude,
    lat: lastLocation.latitude,
    zoom: 15,
  };
  loadMap();
}
async function loadMap() {
  const version = epoch;
  const frame = document.querySelector("#map-frame");
  if (!frame) return;
  const center = { ...mapCenter };
  frame.replaceChildren(
    el("p", { class: "empty" }, "Çevrimdışı harita hazırlanıyor…"),
  );
  try {
    const r = await api(
      `/api/map/image?lon=${center.lon}&lat=${center.lat}&zoom=${center.zoom}`,
    );
    const blob = await r.blob();
    if (
      version !== epoch ||
      page !== "map" ||
      JSON.stringify(center) !== JSON.stringify(mapCenter)
    )
      return;
    if (mapURL) URL.revokeObjectURL(mapURL);
    mapURL = URL.createObjectURL(blob);
    frame.replaceChildren(
      el("img", { src: mapURL, alt: "Çevrimdışı Türkiye sokak haritası" }),
    );
    if (
      lastLocation &&
      Math.abs(center.lon - lastLocation.longitude) < 0.00001 &&
      Math.abs(center.lat - lastLocation.latitude) < 0.00001
    )
      frame.append(
        el("span", { class: "map-marker" }, "⌖ " + lastLocation.source_id),
      );
  } catch (e) {
    frame.replaceChildren(el("p", { class: "empty" }, e.message));
  }
}
function renderRepeater(d) {
  const root = document.querySelector("#content");
  root.replaceChildren(
    el(
      "div",
      { class: "panel row spread" },
      el(
        "div",
        {},
        el("h2", {}, d.identity?.alias || "Hytera röle"),
        el(
          "p",
          { class: "muted" },
          "SNMP · " + (d.identity?.radio_id ?? "ID bekleniyor"),
        ),
      ),
      el(
        "span",
        { class: "badge " + (d.fresh ? "green" : "gray") },
        d.fresh ? "● Bağlı" : "● Güncel veri yok",
      ),
    ),
  );
  const grid = el("div", { class: "metric-grid" });
  for (const [key, m] of Object.entries(d.measurements || {}))
    grid.append(
      el(
        "div",
        { class: "panel metric" },
        el("p", { class: "muted" }, m.label || m.name || "Ölçüm " + key),
        el("strong", {}, m.text ?? m.value ?? "—"),
        el("p", { class: "muted small" }, m.freshness || ""),
      ),
    );
  for (const [slot, r] of Object.entries(d.rssi_read || {}))
    grid.append(
      el(
        "div",
        { class: "panel metric" },
        el("p", { class: "muted" }, "RSSI · Slot " + slot),
        el("strong", {}, r.text || "—"),
      ),
    );
  root.append(
    el(
      "div",
      { class: "stack" },
      el(
        "p",
        { class: "muted" },
        d.error ||
          d.receiver_status ||
          (!d.running
            ? "SNMP kapalı. Yönetici, sunucu başlangıcından SNMP izlemeyi etkinleştirebilir."
            : ""),
      ),
      grid,
    ),
  );
  if (d.active?.length)
    root.append(el("div", { class: "info red" }, d.active.join(" · ")));
}
function drawSpectrum(d) {
  document.querySelector("#spectrum-status").textContent =
    d.status || "Ölçüm bekleniyor";
  const canvas = document.querySelector("#spectrum"),
    ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = "12px Segoe UI";
  for (let db = 0; db >= -120; db -= 20) {
    const y = 20 - db * 2.3;
    ctx.strokeStyle = "#304a61";
    ctx.beginPath();
    ctx.moveTo(50, y);
    ctx.lineTo(1080, y);
    ctx.stroke();
    ctx.fillStyle = "#aebdce";
    ctx.fillText(db + "", 12, y + 4);
  }
  if (!d.values) return;
  ctx.strokeStyle = "#55d9bd";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  d.values.forEach((v, i) => {
    const x = 50 + (i / (d.values.length - 1)) * 1030,
      y = 20 - Math.max(-120, Math.min(0, v)) * 2.3;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = "#aebdce";
  ctx.fillText((d.low / 1e6).toFixed(4) + " MHz", 50, 326);
  ctx.fillText((d.high / 1e6).toFixed(4) + " MHz", 970, 326);
  ctx.fillText("dBFS / FFT bin", 55, 14);
}
async function boot() {
  try {
    const setup = await json("/api/setup");
    if (setup.required) {
      showLogin(true);
      return;
    }
    try {
      setSession(await json("/api/me"));
      showShell();
    } catch {
      showLogin(false);
    }
  } catch (e) {
    app.replaceChildren(
      el(
        "div",
        { class: "panel" },
        el("h1", {}, "BIEM-ICC-SERVER"),
        el("p", {}, e.message),
        button("Yeniden dene", boot),
      ),
    );
  }
}
boot();
