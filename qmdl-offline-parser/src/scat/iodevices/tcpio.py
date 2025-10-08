#!/usr/bin/env python3
# coding: utf8
"""
Live TCP I/O device

Listens on a TCP port and accepts a single connection. Bytes received from the
client are returned by `read()` and can be fed into the existing parser run
loop. This keeps compatibility with `FileIO` and `LiveStdinIO`.

Usage:
    io_device = LiveTcpIO(listen_addr='0.0.0.0', listen_port=5000)
    parser.set_io_device(io_device)
    parser.run_diag()

Notes:
 - Single-client only: when the client disconnects, the device closes and EOF
   is returned to the parser.
 - Blocking semantics: `read()` blocks until data is available, making it
   suitable for piping live streams directly into the parser.
"""

import socket
import threading
import time


class LiveTcpIO:
    def __init__(self, listen_addr='127.0.0.1', listen_port=5000, backlog=1):
        self.listen_addr = listen_addr
        self.listen_port = int(listen_port)
        self.backlog = backlog
        self.server = None
        self.client = None
        self.client_lock = threading.Lock()
        self.fname = f'tcp://{self.listen_addr}:{self.listen_port}'
        self.file_available = True
        self.block_until_data = False
        self._setup_server()

    def _setup_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.listen_addr, self.listen_port))
        self.server.listen(self.backlog)
        # Accept in background to avoid blocking constructor
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()

    def _accept_loop(self):
        try:
            client_sock, addr = self.server.accept()
            with self.client_lock:
                self.client = client_sock
        except Exception:
            self.file_available = False

    def read(self, read_size, decode_hdlc=False):
        # Block until client connected
        while True:
            with self.client_lock:
                c = self.client
            if c is not None:
                break
            # Sleep a small amount and retry
            time.sleep(0.1)
            if not self.file_available:
                return b''
        try:
            data = c.recv(read_size)
            if not data:
                # Client disconnected
                with self.client_lock:
                    try:
                        c.close()
                    except Exception:
                        pass
                    self.client = None
                self.file_available = False
                return b''
            return data
        except Exception:
            # On error, close client and signal EOF
            with self.client_lock:
                if self.client:
                    try:
                        self.client.close()
                    except Exception:
                        pass
                    self.client = None
            self.file_available = False
            return b''

    def write(self, write_buf, encode_hdlc=False):
        # If a client is connected, send data back
        with self.client_lock:
            if self.client:
                try:
                    self.client.sendall(write_buf)
                except Exception:
                    pass

    def write_then_read_discard(self, write_buf, read_size, encode_hdlc=False):
        self.write(write_buf)
        return self.read(read_size)

    def open_next_file(self):
        # No-op for live TCP
        self.file_available = False

    def close(self):
        with self.client_lock:
            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass
                self.client = None
        if self.server:
            try:
                self.server.close()
            except Exception:
                pass
        self.file_available = False

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
