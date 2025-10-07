
#!/usr/bin/env python3
# coding: utf8
"""
FileIO Module

Provides file-based I/O abstraction for reading log files, including support for gzip and bz2 compressed files.
Used by the main parser to read input data for offline analysis.
"""

import gzip, bz2
import scat.util as util


class FileIO:
    """
    File-based I/O abstraction for reading log files, including support for compressed formats.
    """
    def _open_file(self, fname):
        """
        Open a file for reading, supporting gzip and bz2 compression.
        """
        if self.f:
            self.f.close()
        if fname.find('.gz') > 0:
            self.f = gzip.open(fname, 'rb')
        elif fname.find('.bz2') > 0:
            self.f = bz2.open(fname, 'rb')
        else:
            self.f = open(fname, 'rb')

    def __init__(self, fnames):
        """
        Initialize FileIO with a list of filenames to read sequentially.
        """
        self.fnames = fnames[:]
        self.fnames.reverse()
        self.fname = ''
        self.file_available = True
        self.f = None
        self.block_until_data = False
        self.open_next_file()

    def read(self, read_size, decode_hdlc = False):
        """
        Read a chunk of data from the current file. Optionally decode HDLC framing.
        """
        buf = b''
        try:
            buf = self.f.read(read_size)
            buf = bytes(buf)
        except:
            return b''
        if decode_hdlc:
            buf = util.unwrap(buf)
        return buf

    def open_next_file(self):
        """
        Advance to the next file in the list and open it for reading.
        """
        try:
            self.fname = self.fnames.pop()
        except IndexError:
            self.file_available = False
            return
        self._open_file(self.fname)

    def write(self, write_buf, encode_hdlc = False):
        """
        Stub for writing data to file (not implemented).
        """
        pass

    def write_then_read_discard(self, write_buf, read_size, encode_hdlc = False):
        """
        Write data then read and discard a chunk (for compatibility).
        """
        self.write(write_buf)
        self.read(read_size)

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Close the file handle on exit.
        """
        if self.f:
            self.f.close()
