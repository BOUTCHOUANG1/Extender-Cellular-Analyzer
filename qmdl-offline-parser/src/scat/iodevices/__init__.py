#!/usr/bin/env python3
# coding: utf8

# Extender-Cellular-Analyzer - All-in-one tool with live capture and offline analysis

from scat.iodevices.fileio import FileIO
from scat.iodevices.liveio import LiveStdinIO
from scat.iodevices.tcpio import LiveTcpIO
from scat.iodevices.usbio import USBIO
from scat.iodevices.serialio import SerialIO

# Live input devices
# LiveStdinIO can be used for piping a raw DIAG HDLC stream into the parser
# Example: cat stream.bin | qmdl-parser --live-stdin -t qc --txt-file out.txt
class LiveIO:
    """Backward-compatible alias exposing stdin live device."""
    def __init__(self):
        # Provide the same constructor semantics as the original Serial/USB stubs
        self._dev = LiveStdinIO()
    def __getattr__(self, name):
        return getattr(self._dev, name)

# Convenience factory for TCP live input
def LiveTcp(listen_addr='127.0.0.1', listen_port=5000):
    return LiveTcpIO(listen_addr=listen_addr, listen_port=listen_port)
