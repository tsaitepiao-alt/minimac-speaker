#!/usr/bin/env bash
# 一鍵驗證：機構出圖 → 尺寸核對 → 韌體編譯
# 用法：tools/check.sh
set -uo pipefail
cd "$(dirname "$0")/.."
FAIL=0
say(){ printf "\n=== %s ===\n" "$1"; }

say "① 機構建模與尺寸核對"
if .venv/bin/python cad/build_minimac.py > /tmp/mm_cad.log 2>&1; then
  grep -E "干涉/超界" /tmp/mm_cad.log
  if grep -q "干涉/超界： 無" /tmp/mm_cad.log; then echo "CAD: OK"; else echo "CAD: 有干涉"; FAIL=1; fi
else
  echo "CAD: 建模失敗"; tail -5 /tmp/mm_cad.log; FAIL=1
fi

say "② STL 有效性（每件都要是封閉實體、三角形數合理）"
.venv/bin/python - <<'PY'
import trimesh, os, sys
bad = 0
for f in sorted(os.listdir('stl')):
    m = trimesh.load(os.path.join('stl', f))
    ok = m.is_watertight and len(m.faces) > 100
    print(f"{f:16s} faces={len(m.faces):6d} watertight={m.is_watertight} vol={m.volume/1000:7.2f} cm3 {'OK' if ok else 'FAIL'}")
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
PY
[ $? -ne 0 ] && FAIL=1

say "③ 韌體編譯（esp32:esp32:esp32，約 5–8 分鐘）"
if timeout 900 arduino-cli compile --fqbn esp32:esp32:esp32 --board-options PartitionScheme=huge_app firmware/minimac_speaker > /tmp/mm_fw.log 2>&1; then
  grep -E "Sketch uses|Global variables" /tmp/mm_fw.log || tail -3 /tmp/mm_fw.log
  echo "FIRMWARE: OK"
else
  echo "FIRMWARE: FAIL"; grep -E "error:" /tmp/mm_fw.log | head -10; FAIL=1
fi

say "結果"
[ $FAIL -eq 0 ] && echo "CHECK OK" || echo "CHECK FAILED"
exit $FAIL
