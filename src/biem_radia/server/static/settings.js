"use strict";
let settingsFocus = null;

function choice(options, value, label) {
  const input = el("select", { "aria-label": label });
  for (const option of options) {
    const [v, text] = Array.isArray(option) ? option : [option, option];
    input.append(el("option", { value: v }, text));
  }
  input.value = String(value);
  return input;
}
function numeric(value, min, max, step = 1) {
  return el("input", { type: "number", value, min, max, step, required: true });
}
async function loadSettings() {
  try {
    const data = await json("/api/settings");
    if (page === "settings") renderSettings(data);
  } catch (error) {
    note(error.message);
  }
}
function renderSettings(data) {
  const root = document.querySelector("#content");
  root.replaceChildren();
  const info = el(
    "p",
    { class: data.busy ? "connection-lost" : "muted" },
    data.busy
      ? "SDR veya spektrum çalışıyor. Ayarları kaydetmeden önce durdurun ve bu sayfayı yenileyin."
      : "Ayarlar sonraki alımda uygulanır. Sunucu ve masaüstü aynı ayarları kullanır; aynı SDR ile birlikte çalıştırmayın.",
  );
  root.append(
    el(
      "div",
      { class: "toolbar" },
      button("Ayarları yeniden yükle", loadSettings),
      button("■ SDR alımını durdur", () => control("receiver", "stop")),
      button("■ Spektrumu durdur", () => control("spectrum", "stop")),
    ),
    info,
  );
  root.append(
    deviceSettings(data),
    receiverSettings(data),
    channelSettings(data),
  );
}
function settingsForm(title, resource, data, collect) {
  const status = el("p", { class: "muted", role: "status" });
  const submit = el(
    "button",
    { type: "submit", class: "primary", disabled: data.busy },
    "Kaydet",
  );
  const body = el("div", { class: "settings-fields" });
  let revision = data[resource].revision;
  const form = el(
    "form",
    {
      class: "panel settings-panel",
      onsubmit: async (event) => {
        event.preventDefault();
        submit.disabled = true;
        status.textContent = "Kaydediliyor…";
        try {
          const result = await json("/api/settings/" + resource, "PUT", {
            revision,
            [resource]: collect(),
          });
          revision = result.revision;
          status.textContent = "Kaydedildi. Bir sonraki alımda kullanılacak.";
        } catch (error) {
          status.textContent = error.message;
        } finally {
          submit.disabled = data.busy;
        }
      },
    },
    el("h2", {}, title),
    ...(data[resource].error
      ? [
          el(
            "p",
            { class: "connection-lost", role: "alert" },
            data[resource].error,
          ),
        ]
      : []),
    body,
    el("div", { class: "row" }, submit, status),
  );
  return { form, body, submit, status };
}
function deviceSettings(data) {
  const stored = data.device.value;
  const select = choice(
    [["", "Cihazları yenileyin…"]],
    "",
    "Kullanılacak USB alıcı",
  );
  let items = [];
  const box = settingsForm("USB alıcı", "device", data, () => {
    const selected = items[Number(select.value)];
    if (select.value === "" || !selected)
      throw new Error("Önce cihazları yenileyip bir USB alıcı seçin.");
    return { index: selected.index, serial: selected.serial };
  });
  const status = el(
    "p",
    { class: "muted" },
    `Kayıtlı seçim: USB ${stored.index} · Seri ${stored.serial || "yok"}`,
  );
  box.body.append(field("Kullanılacak USB alıcı", select));
  box.form.insertBefore(
    el(
      "div",
      { class: "toolbar" },
      button("Cihazları yenile", async () => {
        try {
          const result = await json("/api/settings/devices");
          items = result.devices;
          select.replaceChildren(
            el("option", { value: "" }, "USB alıcı seçin…"),
          );
          items.forEach((item, i) =>
            select.append(
              el(
                "option",
                { value: i },
                `USB ${item.index} · ${item.name} · Seri ${item.serial || "yok"}`,
              ),
            ),
          );
          const match = items.findIndex(
            (item) =>
              item.index === stored.index && item.serial === stored.serial,
          );
          if (match >= 0) select.value = String(match);
          else if (items.length === 1) select.value = "0";
          status.textContent = items.length
            ? `${items.length} USB alıcı listelendi. Listelenmesi alıcının boşta olduğunu göstermez.`
            : "RTL-SDR listelenmedi. USB bağlantısını kontrol edin; SDR# ve diğer alıcı programlarını kapatın.";
        } catch (error) {
          status.textContent = error.message;
        }
      }),
      status,
    ),
    box.body,
  );
  return box.form;
}
function receiverSettings(data) {
  const saved = data.receiver.value;
  const fields = {
    source: choice(["USB", "rtl_tcp"], saved.source, "Alıcı kaynağı"),
    host: el("input", { value: saved.host, maxlength: 253, required: true }),
    port: numeric(saved.port, 1, 65535),
    ppm: numeric(saved.ppm, -200, 200),
    usb_gain: numeric(saved.usb_gain, -10, 50, 0.1),
    usb_agc: choice(["Manuel", "Tuner AGC"], saved.usb_agc, "Kazanç kontrolü"),
    receive_mode: choice(
      ["Sabit", "Tarama"],
      saved.receive_mode,
      "Alım biçimi",
    ),
    scan_dwell: numeric(saved.scan_dwell, 0.3, 10, 0.1),
    scan_release: numeric(saved.scan_release, 0.3, 10, 0.1),
  };
  const numericKeys = new Set([
    "port",
    "ppm",
    "usb_gain",
    "scan_dwell",
    "scan_release",
  ]);
  const box = settingsForm("Alıcı ve RF ayarları", "receiver", data, () =>
    Object.fromEntries(
      Object.entries(fields).map(([key, input]) => [
        key,
        numericKeys.has(key) ? Number(input.value) : input.value,
      ]),
    ),
  );
  const labels = [
    "Alıcı kaynağı",
    "rtl_tcp adresi",
    "rtl_tcp portu",
    "PPM düzeltme",
    "USB kazanç / dB",
    "Kazanç kontrolü",
    "Alım biçimi",
    "Kanal dinleme / sn",
    "Eşik altı bekleme / sn",
  ];
  Object.values(fields).forEach((input, i) =>
    box.body.append(field(labels[i], input)),
  );
  const update = () => {
    fields.host.disabled = fields.port.disabled =
      fields.source.value !== "rtl_tcp";
    fields.usb_gain.disabled =
      fields.source.value !== "USB" || fields.usb_agc.value !== "Manuel";
    fields.usb_agc.disabled = fields.source.value !== "USB";
    fields.scan_dwell.disabled = fields.scan_release.disabled =
      fields.receive_mode.value !== "Tarama";
  };
  fields.source.addEventListener("change", update);
  fields.usb_agc.addEventListener("change", update);
  fields.receive_mode.addEventListener("change", update);
  update();
  return box.form;
}
function channelSettings(data) {
  const editors = [];
  const box = settingsForm("SDR kanalları", "channels", data, () =>
    editors.map((item) => item.value()),
  );
  box.body.className = "channel-settings-list";
  box.submit.textContent = "Tüm kanal ayarlarını kaydet";
  box.form.insertBefore(
    el(
      "p",
      { class: "muted" },
      "Kanal adını değiştirirseniz kullanıcıların yeni ada erişimini Kullanıcılar ve yetkiler ekranından tanımlayın. Eski kayıtlar eski kanal adıyla kalır.",
    ),
    box.body,
  );
  const add = button("＋ Kanal ekle", () => {
    if (editors.length >= 8) return;
    append(
      {
        name: "Kanal " + (editors.length + 1),
        frequency_hz: 446000000,
        enabled: false,
        mode: "NFM",
        squelch_db: -45,
        color_code: null,
        spacing_hz: 12500,
        bandwidth_hz: 12500,
        system: "Default",
        tone_mode: "CSQ",
        tone_value: "67.0",
        follow_signal: true,
      },
      true,
    );
  });
  function append(channel, opened = false) {
    const editor = channelEditor(channel, data, opened);
    editors.push(editor);
    box.body.append(editor.node);
    add.disabled = data.busy || editors.length >= 8;
  }
  for (const channel of data.channels.value)
    append(channel, channel.name === settingsFocus);
  add.disabled = data.busy || editors.length >= 8;
  box.form.append(add);
  settingsFocus = null;
  return box.form;
}
function channelEditor(saved, data, opened) {
  const name = el("input", {
    value: saved.name,
    required: true,
    maxlength: 100,
  });
  const enabled = checkbox("Kanal etkin", "enabled", saved.enabled);
  const follow = checkbox(
    "Yakın sinyale kilitlen (±6,5 kHz)",
    "follow",
    saved.follow_signal,
  );
  const frequency = numeric(saved.frequency_hz / 1e6, 24, 1766, 0.000001);
  const mode = choice(
    [
      ["NFM", "Analog"],
      ["DMR", "DMR"],
      ["TETRA", "TETRA"],
      ["AUTO", "Otomatik"],
      ["APCO25", "APCO25"],
      ["NXDN", "NXDN"],
    ],
    saved.mode,
    "Mod",
  );
  const threshold = numeric(saved.squelch_db, -100, 0, 0.5);
  const code = el("input", {
    type: "number",
    value: saved.color_code ?? "",
    min: 0,
    max: 15,
    step: 1,
    placeholder: "Boş: otomatik",
  });
  const codeLabel = field("Color code", code);
  const spacing = choice(
    [6250, 12500, 25000],
    saved.spacing_hz,
    "Kanal aralığı / Hz",
  );
  const bandwidth = numeric(saved.bandwidth_hz, 4000, 25000, 1);
  const toneMode = choice(
    ["CSQ", "CTCSS", "DCS", "DCS-I"],
    saved.tone_mode,
    "Analog ton modu",
  );
  const tone = choice([saved.tone_value], saved.tone_value, "Ton / kod");
  function updateTone() {
    const value = tone.value;
    const options =
      toneMode.value === "CTCSS"
        ? data.ctcss.map(String)
        : toneMode.value === "CSQ"
          ? [saved.tone_value]
          : data.dcs;
    tone.replaceChildren(...options.map((v) => el("option", { value: v }, v)));
    tone.value = options.includes(value) ? value : options[0];
    toneMode.disabled = mode.value !== "NFM";
    tone.disabled = mode.value !== "NFM" || toneMode.value === "CSQ";
  }
  function updateMode(changed = false) {
    if (changed) {
      spacing.value = mode.value === "TETRA" ? "25000" : "12500";
      bandwidth.value = mode.value === "TETRA" ? 25000 : 12500;
      code.value = "";
    }
    code.disabled = ["NFM", "AUTO"].includes(mode.value);
    code.max =
      mode.value === "APCO25"
        ? 4095
        : ["TETRA", "NXDN"].includes(mode.value)
          ? 63
          : 15;
    codeLabel.firstChild.textContent =
      mode.value === "APCO25"
        ? "NAC (ondalık)"
        : mode.value === "NXDN"
          ? "RAN"
          : "CC (boş: otomatik)";
    updateTone();
  }
  mode.addEventListener("change", () => updateMode(true));
  toneMode.addEventListener("change", updateTone);
  updateMode();
  const summary = el(
    "summary",
    {},
    saved.name,
    el("span", { class: "muted" }, " · Kanal ayarları"),
  );
  const node = el(
    "details",
    { class: "channel-editor", ...(opened ? { open: "" } : {}) },
    summary,
    el(
      "div",
      { class: "settings-fields" },
      field("Kanal adı", name),
      field("Frekans / MHz", frequency),
      field("Mod", mode),
      field("Kayıt eşiği / dBFS", threshold),
      codeLabel,
      field("Kanal aralığı / Hz", spacing),
      field("Filtre genişliği / Hz", bandwidth),
      field("Analog ton modu", toneMode),
      field("Ton / kod", tone),
    ),
    el("div", { class: "row" }, enabled, follow),
  );
  return {
    node,
    value: () => ({
      ...saved,
      name: name.value.trim(),
      frequency_hz: Math.round(Number(frequency.value) * 1e6),
      mode: mode.value,
      squelch_db: Number(threshold.value),
      spacing_hz: Number(spacing.value),
      bandwidth_hz: Number(bandwidth.value),
      color_code:
        code.disabled || code.value === "" ? null : Number(code.value),
      enabled: enabled.querySelector("input").checked,
      follow_signal: follow.querySelector("input").checked,
      tone_mode: mode.value === "NFM" ? toneMode.value : "CSQ",
      tone_value: tone.value,
    }),
  };
}
