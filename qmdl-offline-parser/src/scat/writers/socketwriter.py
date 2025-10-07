
#!/usr/bin/env python3
# coding: utf8
"""
SocketWriter Module

Provides a class for sending parsed cellular log data over UDP sockets to specified addresses and ports.
Used for network streaming or integration with external tools.
"""

import socket
import struct


class SocketWriter:
    """
    Handles sending parsed cellular log data over UDP sockets to specified addresses and ports.
    Used for network streaming or integration with external tools.
    """
    def __init__(self, base_address, port_cp = 4729, port_up = 47290):
        """
        Initialize SocketWriter with base address and UDP ports for control/user plane.
        """
        self.base_address = struct.unpack('!I', socket.inet_pton(socket.AF_INET, base_address))[0]
        self.port_cp = port_cp
        self.sock_cp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_cp_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port_up = port_up
        self.sock_up = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_up_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __enter__(self):
        """
        Support for context manager usage (with statement).
        """
        return self

    def write_cp(self, sock_content, radio_id=0, ts=None):
        """
        Send control plane data over UDP socket to the specified address/port.
        """
        if radio_id <= 0:
            dest_address = self.base_address
        else:
            dest_address = self.base_address + radio_id
        dest_address_str = socket.inet_ntoa(struct.pack('!I', dest_address))
        self.sock_cp.sendto(sock_content, (dest_address_str, self.port_cp))

    def write_up(self, sock_content, radio_id=0, ts=None):
        """
        Send user plane data over UDP socket to the specified address/port.
        """
        if radio_id <= 0:
            dest_address = self.base_address
        else:
            dest_address = self.base_address + radio_id
        dest_address_str = socket.inet_ntoa(struct.pack('!I', dest_address))
        self.sock_up.sendto(sock_content, (dest_address_str, self.port_up))

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Close UDP sockets on exit.
        """
        self.sock_cp_recv.close()
        self.sock_up_recv.close()
