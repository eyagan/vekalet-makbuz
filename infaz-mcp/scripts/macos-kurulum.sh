#!/usr/bin/env bash
# infaz-mcp — macOS / Claude Desktop tek adım kurulum.
# Yaptıkları: bağımlılıkları kurar (uv sync), Claude Desktop config'ine
# "infaz" sunucusunu MEVCUT sunucuları bozmadan ekler (önce yedek alır).
# Yeniden çalıştırılması güvenlidir (idempotent).
set -euo pipefail

# 1) Yollar
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFAZ_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# 2) uv'yi bul
UV="$(command -v uv || true)"
[ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ] && UV="$HOME/.local/bin/uv"
if [ -z "$UV" ]; then
  echo "HATA: 'uv' bulunamadı. Önce kurun:  brew install uv" >&2
  exit 1
fi
echo "• uv: $UV"
echo "• proje: $INFAZ_DIR"

# 3) Bağımlılıklar + testler
echo "• Bağımlılıklar kuruluyor (uv sync)..."
( cd "$INFAZ_DIR" && "$UV" sync --quiet )
echo "• Testler çalıştırılıyor..."
( cd "$INFAZ_DIR" && "$UV" run --quiet pytest -q ) && echo "  → testler geçti."

# 4) Config'e "infaz" bloğunu güvenle ekle (Python ile JSON birleştirme)
if [ ! -f "$CONFIG" ]; then
  echo "• Config bulunamadı, yeni oluşturulacak: $CONFIG"
  mkdir -p "$(dirname "$CONFIG")"
  printf '{\n  "mcpServers": {}\n}\n' > "$CONFIG"
fi

UV="$UV" INFAZ_DIR="$INFAZ_DIR" CONFIG="$CONFIG" "$UV" run --quiet python - <<'PY'
import json, os, shutil, datetime, sys

cfg = os.environ["CONFIG"]
uv = os.environ["UV"]
infaz_dir = os.environ["INFAZ_DIR"]

with open(cfg, encoding="utf-8") as f:
    data = json.load(f)

# Yedek
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = f"{cfg}.yedek-{stamp}"
shutil.copy2(cfg, backup)

servers = data.setdefault("mcpServers", {})
servers["infaz"] = {
    "command": uv,
    "args": ["run", "--directory", infaz_dir, "python", "-m", "infaz_mcp.server"],
}

with open(cfg, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"• Config güncellendi (yedek: {os.path.basename(backup)})")
print(f"• Tanımlı sunucular: {', '.join(sorted(servers))}")
PY

echo
echo "✓ Kurulum tamam. Son adım: Claude Desktop'ı Cmd+Q ile TAMAMEN kapatıp yeniden açın."
echo "  Ardından araç menüsünde 'infaz' görünür. Deneyin:"
echo '  "TCK 86/1, 4 yıl 2 ay, suç tarihi 15.05.2021, infaz 01.02.2024, 90 gün tutuklu — infaz tarihlerini hesapla."'
