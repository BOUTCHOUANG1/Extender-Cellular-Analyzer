
#!/usr/bin/env python3
# coding: utf8
"""
RawWriter Module

Provides a class for writing raw binary data to a file, optionally with header and trailer.
Used for debugging or exporting raw protocol data.
"""

import datetime


class RawWriter:
    """
    Handles writing raw binary data to a file, optionally with header and trailer.
    Used for debugging or exporting raw protocol data.
    """
    def __init__(self, fname, header=b'', trailer=b''):
        """
        Initialize RawWriter with output filename, header, and trailer.
        """
        self.raw_file = open(fname, 'wb')
        self.raw_file.write(header)
        self.trailer = trailer

    def __enter__(self):
        """
        Support for context manager usage (with statement).
        """
        return self

    def write_cp(self, sock_content, radio_id=0, ts=datetime.datetime.now()):
        """
        Write control plane data to the raw file.
        """
        self.raw_file.write(sock_content)

    def write_up(self, sock_content, radio_id=0, ts=datetime.datetime.now()):
        """
        Write user plane data to the raw file.
        """
        self.raw_file.write(sock_content)

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Write trailer and close the file on exit.
        """
        self.raw_file.write(self.trailer)
        self.raw_file.close()
