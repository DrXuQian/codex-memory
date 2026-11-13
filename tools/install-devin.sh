#!/usr/bin/env bash
# Install this pack's skills as global Devin skills so they work from any directory.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -n "${APPDATA:-}" ]]; then
  DEST="$(cygpath -u "$APPDATA" 2>/dev/null || echo "$APPDATA")/devin/skills"
  PACK_ROOT="$(cygpath -m "$ROOT" 2>/dev/null || echo "$ROOT")"
else
  DEST="${XDG_CONFIG_HOME:-$HOME/.config}/devin/skills"
  PACK_ROOT="$ROOT"
fi
mkdir -p "$DEST"
for d in "$ROOT"/.devin/skills/*/; do
  name="$(basename "$d")"
  rm -rf "$DEST/$name"
  cp -r "$d" "$DEST/$name"
  echo "installed $name -> $DEST/$name"
done
sed -i "s#{{PACK_ROOT}}#$PACK_ROOT#" "$DEST/codex-history/SKILL.md"
echo "codex-history PACK_ROOT = $PACK_ROOT"
