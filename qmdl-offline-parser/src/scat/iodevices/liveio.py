#!/usr/bin/env python3
# coding: utf8
"""
Live I/O devices for real-time capture.

This module provides a minimal stdin-based live IO device that can be
plugged into existing parsers. It exposes the same API surface the
parsers expect from `FileIO` (read, write, write_then_read_discard, fname,
file_available, block_until_data).

The implementation is intentionally tiny: it reads raw bytes from
`sys.stdin.buffer` (blocking) and returns them to the parser. When stdin
is closed (EOF) reads will return an empty bytes() and the parser will
exit its loop.
"""

import sys


class LiveStdinIO:
    """Live input device reading from standard input (binary).

    Usage:
        io_device = LiveStdinIO()
        parser.set_io_device(io_device)
        parser.run_diag()
    """

    def __init__(self):
        # name presented in logs
        self.fname = 'stdin'
        # treat as always-available until EOF
        self.file_available = True
        # no underlying file object needed
        self.f = None
        # when True the parser loop will spin when no data is available.
        # For blocking stdin reads this should be False.
        self.block_until_data = False

    def read(self, read_size, decode_hdlc=False):
        """Read up to read_size bytes from stdin (blocking).

        The return value is raw bytes. If stdin is closed, an empty
        bytes object is returned which signals EOF to the caller.
        """
        try:
            # sys.stdin.buffer is binary and provides a blocking read
            data = sys.stdin.buffer.read(read_size)
            if data is None:
                return b''
            # Ensure bytes type
            return bytes(data)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            # On unexpected errors, signal EOF
            return b''

    def write(self, write_buf, encode_hdlc=False):
        # Live stdin device is read-only; ignore writes
        return

    def write_then_read_discard(self, write_buf, read_size, encode_hdlc=False):
        # Compatibility shim used by parsers: perform a write and discard
        # followed by a read. For stdin this is a no-op for write.
        self.write(write_buf)
        return self.read(read_size)

    def open_next_file(self):
        # Compatibility with FileIO API: there is no next file for live IO.
        self.file_available = False

    def __exit__(self, exc_type, exc_value, traceback):
        # Nothing to close for stdin
        return
