set -euo pipefail 

RAR="${1:-task_2.rar}"
OUT="extracted"

command -v unrar >/dev/null || {echo "нужен unrar: sudo apt-get install -y unrar"; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT"
echo "[*] Распаковка $RAR (RAR5) ..."
unrar x -o+ "$RAR" "$OUT/" >/dev/null || true 

echo "[*] Поиск флага в артефактах профиля ..."
grep -rialE "ozonctf|flag\{" "$OUT" || true

echo "[*] Флаг из History (URL-decoded):"
strings -n 5 "$OUT/Default/History" \
	| grep -aoE "ozonctf%(25)?7B[^&\"]*%(25)?7D" \
	|head -n1 \
	|python3 -c 'import sys,urlib.parse as u; s=sys.stdin.read().strip;
print(u.unquoete(u.unquote(s)))'