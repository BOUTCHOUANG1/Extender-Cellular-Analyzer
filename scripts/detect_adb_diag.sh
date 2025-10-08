#!/usr/bin/env bash
# Detect DIAG device nodes and root status over adb
set -euo pipefail

echo "Checking adb availability..."
if ! command -v adb >/dev/null 2>&1; then
  echo "adb not found in PATH. Install android-tools-adb or platform-tools and re-run."
  exit 2
fi

echo "adb version: $(adb version 2>&1 | head -n1)"

echo "Listing adb devices..."
adb devices

echo
echo "Checking if device shell can run commands..."
if adb shell id >/dev/null 2>&1; then
  echo "adb shell reachable"
else
  echo "adb shell not reachable — ensure device authorized for this host"
  exit 2
fi

echo
echo "Device shell identity:"
adb shell id || true

echo
echo "Searching for DIAG device nodes under /dev"
adb shell 'ls -l /dev | grep -i diag || true'

echo
echo "Searching for possible diag device names (diag, diagchar, diag_mdlog, mdlog)"
adb shell 'for n in diag diagchar diag_mdlog mdlog; do if [ -e /dev/$n ]; then echo "/dev/$n exists"; ls -l /dev/$n; fi; done' || true

echo
echo "If you see a /dev/diag (or similar) entry and you have root, you can stream it with the forwarding script: scripts/forward_diag_adb.sh"
echo "If the device node is not present, consult device vendor docs or consider using vendor-specific capture utilities." 
