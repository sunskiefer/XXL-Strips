#!/usr/bin/env bash
# XXL STRIP tests, ARM only: the engine and the whole plugin (wrapper + parameters + presets) are compiled for ARMv7
# (static) and run under an ARM emulator. No desktop build of the plugin is made.
#   test/run_arm_tests.sh          (QEMU_ARM=/path/to/qemu-arm-static; run ./build.sh first: it makes build/params.h)
set -euo pipefail
cd "$(dirname "$0")/.."
Q="${QEMU_ARM:-qemu-arm-static}"
Z="${ZIG:-python3 -m ziglang}"
W="${MPC_VST:-$PWD/third_party/mpc-vst-plugins}"
TGT="-target arm-linux-musleabihf -mcpu=generic+v7a+vfp3d16-d32-neon+thumb2 -ffp-contract=off"
CXX="-O2 -DNDEBUG -w -std=gnu++17 -fno-exceptions -fno-rtti -Isrc -Ithird_party/dusk/dsp -I$W/wrapper"
mkdir -p build/armtest
$Z c++ $TGT $CXX -c src/engine.cc -o build/armtest/engine.o
$Z c++ $TGT $CXX -c third_party/dusk/dsp/FourKEQDSP.cpp -o build/armtest/dusk.o
$Z c++ $TGT $CXX -c test/arm_check.cc -o build/armtest/arm_check.o
$Z cc $TGT -O1 -w -std=gnu11 -Ibuild -I"$W/wrapper" -c "$W/wrapper/vst2_wrap.c" -o build/armtest/wrap.o
$Z cc $TGT -O1 -w -std=gnu11 -Ibuild -I"$W/wrapper" -c "$W/tools/host_test.c" -o build/armtest/host_test.o
$Z c++ $TGT -static build/armtest/arm_check.o build/armtest/engine.o build/armtest/dusk.o -lm -o build/armtest/arm_check 2>/dev/null
$Z c++ $TGT -static build/armtest/host_test.o build/armtest/wrap.o build/armtest/engine.o build/armtest/dusk.o -lm -lpthread -o build/armtest/host_test 2>/dev/null
echo "---- engine check (ARM)"
"$Q" build/armtest/arm_check
echo "---- plugin test through the wrapper (ARM)"
"$Q" build/armtest/host_test > build/armtest/host_test.log 2>&1 || true
echo "$(grep -c '^ok' build/armtest/host_test.log) checks ok, $(grep -c '^FAIL' build/armtest/host_test.log) failed"
grep '^FAIL' build/armtest/host_test.log || true
tail -1 build/armtest/host_test.log | grep -q PASSED
