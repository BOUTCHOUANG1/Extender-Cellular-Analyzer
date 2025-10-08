Live capture guide — QMDL Offline Parser
=======================================

Overview
--------
This document explains the live-capture feature added to the QMDL Offline Parser.
The parser was originally built for offline analysis of QMDL/SDM/LPD files. We
added two live input devices that keep compatibility with the parser's existing
I/O abstraction and writer pipeline:

- `LiveStdinIO` — read a raw DIAG HDLC byte stream from standard input. This is
  the simplest option and works well when another tool forwards device data to
  stdout (for example: adb forward, socat, or a device-specific forwarder).

- `LiveTcpIO` — listen on a TCP port and accept a single client connection. The
  connected client can forward raw DIAG HDLC bytes (for example, via socat,
  netcat, or a small forwarding tool). TCP is useful when you want to forward
  device logs from another machine or use netcat-like utilities.

Both devices provide the same minimal API that parsers expect from
`scat.iodevices.FileIO` (methods `read`, `write`, `write_then_read_discard`,
`open_next_file`, and attributes like `fname` and `file_available`). They are
intentionally small and blocking — reads block until bytes are available and
return EOF on client disconnect or closed stdin.

Goals
-----
- Allow real-time parsing of DIAG HDLC streams produced by devices.
- Reuse the existing parsing and writer stack to produce the same outputs as
  offline runs: PCAP, TXT and JSON.
- Provide clear examples and troubleshooting steps for connecting a Samsung
  device for a live test.

Files added
-----------
- `qmdl-offline-parser/src/scat/iodevices/liveio.py` — `LiveStdinIO` implementation.
- `qmdl-offline-parser/src/scat/iodevices/tcpio.py` — `LiveTcpIO` implementation.
- `qmdl-offline-parser/src/scat/iodevices/__init__.py` updated to export these.
- `qmdl-offline-parser/src/scat/main.py` updated to accept options:
  - `--live-stdin`
  - `--live-tcp <port>` and `--live-host <addr>`

How it works (high level)
-------------------------
1. When the CLI receives `--live-stdin`, `main` instantiates `LiveStdinIO` and
   passes it to the selected parser (`--type qc` for Qualcomm). For `--live-tcp`
   it instantiates `LiveTcpIO(listen_addr, listen_port)` instead.
2. The parser's `run_diag()` loop calls `io_device.read(0x1000)` in a blocking
   way and processes DIAG HDLC frames (`0x7e` delimited). The parser calls the
   same `postprocess_parse_result()` and writers used in offline mode.
3. Writers (TXT/JSON/PCAP) are created the same way as offline: pass
   `--txt-file`, `--json-file`, and `--pcap-file` on the command line. The
   composite writer will write parsed events to all requested outputs.

Commands and examples
---------------------
The examples assume you want PCAP, TXT and JSON output while capturing live
streams.

1) Using TCP on the host (device forwarding done via other tools)

Start the parser listening on port 5000:

```bash
qmdl-parser -t qc --live-tcp 5000 --live-host 0.0.0.0 --txt-file live.txt --json-file live.json --pcap-file live.pcap
```

Then forward device output to the host's port 5000. Examples:

- Using `socat` to forward a local serial/USB device:

```bash
# Example: forward a serial device to TCP
socat -u FILE:/dev/ttyUSB0 TCP:127.0.0.1:5000
```

- Using `adb` to forward QXDM output from an Android device (if you have a
  command that writes DIAG HDLC frames to stdout):

```bash
adb shell <device-side-capture-script> | nc <parser-host> 5000
```

2) Using stdin piping (simplest)

If another tool writes raw DIAG frames to stdout, pipe it directly:

```bash
other-tool-producing-diag | qmdl-parser --live-stdin -t qc --txt-file live.txt --json-file live.json --pcap-file live.pcap
```

3) Capturing from a Samsung device connected via ADB

Samsung devices might require a device-specific capture tool to produce raw
DIAG frames. The usual workflow is:

- On the device, enable diagnostics and start the capture (vendor-specific).
- Use `adb logcat`/`adb shell` or a vendor-provided utility to get the raw
  bytes out. If the bytes are presented in hex or in text form you'll need to
  convert them back to raw binary before piping to the parser.
- Forward the bytes to the parser using `--live-stdin` or `--live-tcp` as shown
  above.

Troubleshooting
---------------
- Nothing appears in outputs:
  - Ensure the forwarded stream contains raw DIAG HDLC frames (0x7e delimiters).
  - Verify the client is connected to the TCP listener (use `ss -ltn` or
    `netstat` to see if port is open).
  - Run parser with `-D` to enable debug output.

- Parser exits immediately:
  - If stdin closed or TCP client disconnected, the parser will see EOF and
    stop. Reconnect or restart the parser.

- Partial frames or truncation:
  - The parser expects complete HDLC frames delimited by 0x7e. If the forwarder
    splits frames across writes, the parser still handles reassembly (it keeps
    leftover bytes in its loop), but ensure the forwarding tool doesn't alter
    byte order or escape framing bytes.

Security and performance
------------------------
- Live TCP listener binds to the requested address; prefer binding to
  `127.0.0.1` for local-only access unless you intentionally want remote
  machines to connect.
- `LiveTcpIO` accepts a single client (one connection). If you need multiple
  concurrent clients, we can extend it to buffer data from multiple sources or
  use a producer thread with a shared queue.

Extending the feature
---------------------
- Add a `LiveSerialIO` that uses `pyserial` to read from a USB-serial device.
- Add non-blocking and reconnection semantics: keep listening after client
  disconnect and accept new clients.
- Add authentication for TCP (TLS or simple token) if exposing an open port.

Contact and testing notes
-------------------------
Once you connect your Samsung device and forward its diagnostic stream into
either TCP or stdin, run the parser with all three outputs requested. The
parser will write to `live.txt`, `live.json` and `live.pcap` as the data
arrives. If you want, I can add a small helper script that forwards ADB
logcat output into the parser in the correct binary format if you provide a
short example of the device's capture output.
