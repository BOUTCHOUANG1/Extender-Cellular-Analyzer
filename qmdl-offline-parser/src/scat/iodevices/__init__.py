#!/usr/bin/env python3
# coding: utf8

# QMDL Offline Parser - USB and Serial support removed for offline-only operation
# This fork only supports file-based input

from scat.iodevices.fileio import FileIO

# Stub classes for compatibility with existing code
class USBIO:
    def __init__(self):
        raise NotImplementedError("USB support removed in QMDL Offline Parser fork. Use file input only.")
        
class SerialIO:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Serial support removed in QMDL Offline Parser fork. Use file input only.")
