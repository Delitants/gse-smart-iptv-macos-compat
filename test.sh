#!/bin/sh
set -eu
cd "$(dirname "$0")"
target_arch="${1:-$(uname -m)}"
case "$target_arch" in arm64|x86_64) ;; *) echo 'Expected arm64 or x86_64' >&2; exit 1;; esac
mkdir -p "build/tests/$target_arch"
xcrun clang -arch "$target_arch" -fobjc-arc -O2 -dynamiclib -framework Cocoa \
  src/GSECompatibility.m -o "build/tests/$target_arch/GSECompatibility.dylib"
xcrun clang -arch "$target_arch" -fobjc-arc -framework Cocoa \
  tests/compatibility.m tests/epg_callsite.S -o "build/tests/$target_arch/compatibility-test"
/usr/bin/arch "-$target_arch" "build/tests/$target_arch/compatibility-test" \
  "$PWD/build/tests/$target_arch/GSECompatibility.dylib"
