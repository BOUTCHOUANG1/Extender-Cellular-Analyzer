#!/usr/bin/env python3
# coding: utf8

# QMDL Offline Parser - USB and Serial support removed for offline-only operation
# This fork only supports file-based input

from scat.iodevices.fileio import FileIO
from scat.iodevices.liveio import LiveStdinIO
from scat.iodevices.tcpio import LiveTcpIO

# Stub classes for compatibility with existing code
class USBIO:
    def __init__(self):
        raise NotImplementedError("USB support removed in QMDL Offline Parser fork. Use file input only.")
        
class SerialIO:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Serial support removed in QMDL Offline Parser fork. Use file input only.")

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
