
#!/usr/bin/env python3
# coding: utf8
"""
NullWriter Module

Provides a stub writer class that discards all output. Used for testing or disabling output.
"""


class NullWriter:
    """
    Stub writer class that discards all output. Used for testing or disabling output.
    """
    def write_cp(self, sock_content, radio_id=0, ts=None):
        return

    def write_up(self, sock_content, radio_id=0, ts=None):
        return
