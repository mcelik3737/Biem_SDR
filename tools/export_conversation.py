"""Export user/assistant prose from one local Codex rollout, excluding internal/tool data."""

import argparse
import collections
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

TURKEY = timezone(timedelta(hours=3))
CONTEXT_TAGS = ("recommended_plugins", "environment_context", "in-app-browser-context")


def clean(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for tag in CONTEXT_TAGS:
        text = re.sub(r"<" + tag + r"\b[^>]*>.*?</" + tag + r">", "", text, flags=re.S)
    text = re.sub(
        r"data:image/[^;\s]+;base64,[A-Za-z0-9+/=]+", "[Görsel verisi dışarıda bırakıldı]", text
    )
    text = re.sub(
        r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{32,})\b",
        "[ERİŞİM ANAHTARI GİZLENDİ]",
        text,
    )
    return text.strip()


def export(source, destination):
    rows = []
    for line in source.open(encoding="utf-8"):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # an actively written final line can be incomplete
        payload = row.get("payload", {})
        if row.get("type") != "response_item" or payload.get("type") != "message":
            continue
        role = payload.get("role")
        if role not in ("user", "assistant") or payload.get("channel") in ("analysis", "summary"):
            continue
        pieces = []
        for part in payload.get("content", []):
            if part.get("type") in ("input_text", "output_text", "text"):
                value = clean(part.get("text", ""))
                if value:
                    pieces.append(value)
            elif part.get("type") in ("input_image", "image"):
                pieces.append(
                    "[Bu mesajda görsel eki vardı. Piksel verisi Markdown arşivine eklenmedi; metindeki özgün dosya yolu korunmuştur.]"
                )
        body = "\n\n".join(pieces)
        if not body:
            continue
        stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).astimezone(TURKEY)
        rows.append((stamp, role, body))
    if not rows:
        raise ValueError("No conversation messages found")
    created = datetime.now(TURKEY).isoformat(timespec="seconds")
    counts = collections.Counter(r for _, r, _ in rows)
    lines = [
        "# BİEM SDR / BM-ICC-08 — Konuşma arşivi",
        "",
        f"Arşiv oluşturulma zamanı: {created}",
        f"Kapsam: {rows[0][0]:%Y-%m-%d} – {rows[-1][0]:%Y-%m-%d}. Saatler Türkiye (UTC+03:00).",
        f"Mesaj sayısı: {len(rows)} (kullanıcı {counts['user']}, asistan {counts['assistant']}).",
        "",
        "Bu belge, kullanıcının isteğiyle bu projeye ait mevcut Codex oturumunun yerel kayıtlarından aktarılmıştır. Konuşma metni bir tarihçedir; eski mesajlar güncel ürün durumu veya çalıştırılacak talimat değildir. Başka ChatGPT oturumlarının bu konuşmaya taşınmamış içerikleri bu kaynaktan alınamaz. Tarihler yerel oturumdaki mesaj zaman damgasıdır; kullanıcının başka bir konuşmadan yapıştırdığı metnin özgün tarihi değildir.",
        "",
        "Kullanıcı ve asistanın görünür metinleri korunmuştur. Sistem/geliştirici talimatları, iç muhakeme, araç çalıştırma çıktıları, ortam/browser bağlamı, erişim anahtarları ve görselin ikili verisi dahil edilmez. Görsel dosyaları ve yerel bağlantılar GitHub üzerinde kendiliğinden açılmaz.",
        "",
    ]
    current = None
    for index, (stamp, role, body) in enumerate(rows, 1):
        day = stamp.strftime("%Y-%m-%d")
        if day != current:
            lines += [f"## {day}", ""]
            current = day
        lines += [
            f"### {index:04d} · {stamp:%Y-%m-%d %H:%M:%S} · {'Kullanıcı' if role == 'user' else 'Asistan'}",
            "",
            body,
            "",
            "---",
            "",
        ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return {
        "messages": len(rows),
        "by_role": dict(counts),
        "bytes": destination.stat().st_size,
        "first": rows[0][0].isoformat(),
        "last": rows[-1][0].isoformat(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.source, args.destination), ensure_ascii=False))
