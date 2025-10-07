
#!/usr/bin/env python3
# coding: utf8
"""
SerialIO Module

Provides serial port I/O abstraction for reading and writing data to connected devices.
Used for live device communication in supported parser modes.
"""

import serial
import scat.util as util


class SerialIO:
    """
    Serial port I/O abstraction for reading and writing data to connected devices.
    """
    def __init__(self, port_name, baudrate=115200, rts=True, dsr=True):
        """
        Initialize SerialIO with port name and serial parameters.
        """
        self.port = serial.Serial(port_name, baudrate=baudrate, timeout=0.5, rtscts=rts, dsrdtr=dsr)
        self.block_until_data = True

    def __enter__(self):
        """
        Support for context manager usage (with statement).
        """
        return self

    def read(self, read_size, decode_hdlc = False):
        """
        Read a chunk of data from the serial port. Optionally decode HDLC framing.
        """
        buf = b''
        buf = self.port.read(read_size)
        buf = bytes(buf)
        if decode_hdlc:
            buf = util.unwrap(buf)
        return buf

    def write(self, write_buf, encode_hdlc = False):
        """
        Write data to the serial port. Optionally encode HDLC framing.
        """
        if encode_hdlc:
            write_buf = util.wrap(write_buf)
        self.port.write(write_buf)

    def write_then_read_discard(self, write_buf, read_size = 0x1000, encode_hdlc = False):
        """
        Write data then read and discard a chunk (for compatibility).
        """
        self.write(write_buf, encode_hdlc)
        self.read(read_size)

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Close the serial port on exit.
        """
        self.port.close()
