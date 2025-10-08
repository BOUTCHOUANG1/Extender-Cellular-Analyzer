#!/usr/bin/env bash
set -euo pipefail

if ! command -v adb >/dev/null 2>&1; then
  echo "adb not found. Install android-tools-adb or platform-tools and retry." >&2
  exit 2
fi

usage(){
  cat <<EOF
Usage: $0 [--to-stdout] [--to-tcp HOST PORT] [--device <serial>]

By default this script will attempt to run 'adb shell cat /dev/diag' and
stream the raw bytes to stdout. If --to-tcp is given it will forward to the
given HOST:PORT using nc (netcat).

Examples:
  # stream to parser reading stdin
  $0 --to-stdout | qmdl-parser --live-stdin -t qc --txt-file live.txt --json-file live.json --pcap-file live.pcap

  # forward to TCP listener on localhost:5000
  $0 --to-tcp 127.0.0.1 5000

If the device requires root to read /dev/diag, the script will try 'su -c'.
EOF
}

TO_STDOUT=0
TO_TCP=0
TCP_HOST=127.0.0.1
TCP_PORT=5000
DEVICE_SERIAL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to-stdout)
      TO_STDOUT=1; shift ;;
    --to-tcp)
      TO_TCP=1; TCP_HOST="$2"; TCP_PORT="$3"; shift 3 ;;
    --device)
      DEVICE_SERIAL="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 2 ;;
  esac
done

ADB_CMD=(adb)
if [[ -n "$DEVICE_SERIAL" ]]; then
  ADB_CMD+=( -s "$DEVICE_SERIAL" )
fi

# Try with su if available
STREAM_CMD="cat /dev/diag"

echo "Attempting to stream /dev/diag from device..."
echo "If this fails, ensure device is rooted or that /dev/diag exists."

set +e
${ADB_CMD[@]} shell "$STREAM_CMD" 2>/dev/null | {
  rc=${PIPESTATUS[0]}
  if [[ $rc -ne 0 ]]; then
    echo "Direct cat failed (exit $rc). Trying with su..." >&2
    ${ADB_CMD[@]} shell "su -c '$STREAM_CMD'" 2>/dev/null
  fi
}
set -e

# Above block streams to stdout by default; user can pipe or redirect as needed.
