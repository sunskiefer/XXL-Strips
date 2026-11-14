#!/usr/bin/env bash
# Build XXL STRIP BUS for MPC OS Gen1 / Akai Force (armv7-a hard-float, NEON, glibc <= 2.31 so it also loads on MPC OS 2.x).
#   ./build.sh                     (MPC_VST=../mpc-vst-plugins to use another framework checkout)
# Needs: python3 + Pillow, a host gcc (for the skin renderer shadow_art), and Zig (pip install ziglang). No Docker.
# ARM only: no desktop build of the plugin is made.
# Output: build/package/L'Cronx - VST - XXL STRIP BUS/  (skin + xxlstripbus.so) and build/pluginlist-entry.xml
set -euo pipefail
cd "$(dirname "$0")"
MPC_VST="${MPC_VST:-$PWD/third_party/mpc-vst-plugins}"
ZIG="${ZIG:-python3 -m ziglang}"
NAME="L'Cronx - VST - XXL STRIP BUS"
SO="xxlstripbus.so"
python3 tools/render_knobs.py    # knob frames from tools/knob_render.py (kept in build/knobs/)
python3 tools/gen_params.py
python3 tools/gen_presets.py
python3 tools/qlinks.py --check   # every control on a Q-Link, in reading order
mkdir -p build/host build/arm
[ -x build/host/shadow_art ] || gcc -O2 -w -I"$MPC_VST/tools/vendor/force-shadow/tools" -x c -o build/host/shadow_art "$MPC_VST/tools/shadow_art.c" -lm
rm -rf build/skin
SHADOW_TITLE_FONT="$PWD/art/fonts/TitilliumWeb-SemiBold.ttf" SHADOW_ART="$PWD/build/host/shadow_art" python3 "$MPC_VST/tools/gen_vst.py" vst.json
XXL_TEXT_PIECES=1 python3 tools/post_skin.py "build/skin/$NAME/Plugin Skins" layout.conf   # large Titillium captions (Meta4 text standard)
python3 tools/strip_skin.py "build/skin/$NAME/Plugin Skins" layout.conf --preview build/preview   # rendered knobs, dials, VU dial, ON/OFF buttons, Panel Editor layout
python3 tools/make_editor.py   # the Panel Editor page for this build
SRCS=$(python3 -c "import json; print(' '.join(json.load(open('vst.json'))['build']['sources']))")
CFLAGS=$(python3 -c "import json; print(' '.join(json.load(open('vst.json'))['build']['cflags']))")
TGT="-target arm-linux-gnueabihf.2.31 -mcpu=generic+v7a+vfp3d16-d32-neon+thumb2 -ffp-contract=off"
COMMON="-O2 -fPIC -fvisibility=hidden -ffunction-sections -fdata-sections -DNDEBUG -w"
OBJS=""
for f in $SRCS; do
  o="build/arm/$(echo "$f" | tr / _).o"
  $ZIG c++ $TGT $COMMON -std=gnu++17 -fno-exceptions -fno-rtti $CFLAGS -Ibuild -I"$MPC_VST/wrapper" -c "$f" -o "$o"
  OBJS="$OBJS $o"
done
$ZIG cc $TGT $COMMON -std=gnu11 -Ibuild -c "$MPC_VST/wrapper/vst2_wrap.c" -o build/arm/vst2_wrap.o
printf '{\n  global: VSTPluginMain;\n  local: *;\n};\n' > build/arm/exports.map
$ZIG c++ $TGT -shared -fPIC -Wl,--no-undefined -Wl,--version-script=build/arm/exports.map -Wl,--gc-sections -Wl,-s \
  $OBJS build/arm/vst2_wrap.o -lm -ldl -lpthread -o "build/arm/$SO"
echo "$SO: $(du -h "build/arm/$SO" | cut -f1), exports: $(readelf --dyn-syms -W "build/arm/$SO" | awk '$5=="GLOBAL" && $7!="UND" {print $8}' | tr '\n' ' ')"
echo "  highest glibc: $(readelf -V "build/arm/$SO" | grep -o 'GLIBC_[0-9.]*' | sort -uV | tail -1)"
echo "  machine: $(readelf -h "build/arm/$SO" | grep -E 'Machine|Flags' | tr -s ' ' | tr '\n' ' ')"
PKG="build/package/$NAME"
rm -rf build/package && mkdir -p "$PKG/licenses"
cp -r "build/skin/$NAME/." "$PKG/"
cp "build/arm/$SO" "$PKG/"
cp LICENSE "$PKG/licenses/GPL-3.0.txt"
echo "-> $PKG"
