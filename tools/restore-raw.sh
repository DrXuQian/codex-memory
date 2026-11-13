#!/usr/bin/env bash
# Reassemble and extract the original Codex/Claude data from raw/ into restore/.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
git lfs pull --include "raw/*"
mkdir -p restore
cat raw/part2-codex-main-sessions.tar.xz.* > restore/part2-codex-main-sessions.tar.xz
(cd raw && sha256sum -c --ignore-missing SHA256SUMS)
(cd restore && grep ' *part2-codex-main-sessions.tar.xz$' ../raw/SHA256SUMS | sha256sum -c)
tar -xJf raw/part1-config-skills-db-claude.tar.xz -C restore
tar -xJf restore/part2-codex-main-sessions.tar.xz -C restore
rm restore/part2-codex-main-sessions.tar.xz
echo "Restored into $(pwd)/restore/root"
