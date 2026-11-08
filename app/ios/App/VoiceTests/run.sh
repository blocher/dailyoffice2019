#!/bin/sh
# Runs the voice matcher's tests on the Mac (no simulator needed).
set -e
here="$(cd "$(dirname "$0")" && pwd)"
out="$(mktemp -d)"
PATH=/usr/bin:/bin:/usr/sbin:/sbin xcrun swiftc -o "$out/voice-tests" \
  "$here/../App/Voice/VoiceModel.swift" "$here/main.swift"
"$out/voice-tests"
