#!/usr/bin/env bash
# Package XXL STRIP as the real release zip (mpc-vst-plugins tools/release.py) into dist/.
#   ./release.sh 0.1.0 [owner/repo]        (run ./build.sh first)
# The L'Cronx apostrophe: the framework's release tools are patched first (tools/release_quotes.py), and the release
# FAILS unless install.sh and uninstall.sh pass `sh -n`.
set -euo pipefail
cd "$(dirname "$0")"
VER="${1:?version, e.g. 0.1.0}"
REPO="${2:-}"
MPC_VST="${MPC_VST:-$PWD/third_party/mpc-vst-plugins}"
NAME="L'Cronx - VST - XXL STRIP"
python3 tools/release_quotes.py "$MPC_VST"
rm -rf dist && mkdir -p dist
ARGS=(--so build/arm/xxlstrip.so --skin "build/skin/$NAME" --entry build/pluginlist-entry.xml --version "$VER"
      --about "SSL-style channel strip: filters, four-band EQ (E Brown, E Black, G), compressor, gate/expander, VU."
      --license GPL-3.0-or-later -o dist)
[ -n "$REPO" ] && ARGS+=(--repo "$REPO")
[ -f build/bench.txt ] && ARGS+=(--bench build/bench.txt)
python3 "$MPC_VST/tools/release.py" "${ARGS[@]}"
ZIP="dist/XXL-STRIP-$VER-mpc-armv7.zip"
T="$(mktemp -d)"
python3 -m zipfile -e "$ZIP" "$T"
for f in install.sh uninstall.sh; do
  sh -n "$T/XXL-STRIP-$VER/$f" || { echo "release: $f fails sh -n (apostrophe?)"; exit 1; }
  echo "release: $f passes sh -n"
done
rm -rf "$T"
python3 "$MPC_VST/tools/catalog_check.py" "$ZIP" ${REPO:+--catalog}
sha256sum "$ZIP"
