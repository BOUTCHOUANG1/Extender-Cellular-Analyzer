#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later
"""
QCAT-style TXT Writer - Matches QCAT output format exactly
"""

import datetime
import os
import binascii


class QcatTxtWriter:
    """Writes output in QCAT-compatible TXT format"""
    
    def __init__(self, txt_filename):
        self.txt_filename = txt_filename
        self.file_handle = open(txt_filename, 'w', encoding='utf-8')
        self._write_header()
    
    def _write_header(self):
        """Write QCAT-style header"""
        self.file_handle.write("%MOBILE PARSED MESSAGE FILE\n")
        self.file_handle.write("%QCAT VERSION   : QCAT 07.01.250 patch 03\n")
        self.file_handle.write("%SILK VERSION   : SILK_9.83\n")
        self.file_handle.write(f"%LOG FILE NAME  : {os.path.basename(self.txt_filename)}\n\n")
        self.file_handle.write("%Confidential - Qualcomm Technologies, Inc.and / or its affiliated companies - May Contain Trade Secrets\n")
    
    def set_input_filename(self, filename):
        """Set input filename - not used in QCAT format"""
        pass
    
    def write_cp(self, sock_content, radio_id, ts):
        """Write control plane - not displayed in QCAT event format"""
        pass
    
    def write_up(self, sock_content, radio_id, ts):
        """Write user plane - not displayed in QCAT event format"""
        pass
    
    def write_parsed_data(self, parsed_result, radio_id=0, ts=None):
        """Write parsed data in QCAT format"""
        if 'event' in parsed_result:
            events = parsed_result['event']
            if isinstance(events, list):
                for event in events:
                    self._write_event_qcat(event, radio_id, ts)
            elif isinstance(events, dict):
                self._write_event_qcat(events, radio_id, ts)
    
    def _write_event_qcat(self, event, radio_id, ts):
        """Write event in exact QCAT format"""
        # Extract event details
        event_id = event.get('id', 0)
        event_name = event.get('type', 'Unknown')
        payload = event.get('payload', '')
        payload_str = event.get('payload_str', '')
        thread = event.get('thread', '00')
        
        # Get timestamp
        if 'timestamp' in event:
            ts = event['timestamp']
        if ts is None:
            ts = datetime.datetime.now()
        
        # Format timestamp: "YYYY Mon DD HH:MM:SS.mmm"
        if isinstance(ts, datetime.datetime):
            ts_full = ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            ts_time = ts.strftime('%H:%M:%S.%f')[:-3]
        else:
            ts_full = str(ts)
            ts_time = str(ts)
        
        # Format thread as hex
        if isinstance(thread, int):
            thread_hex = f"{thread:02X}"
        else:
            try:
                thread_hex = f"{int(str(thread), 0):02X}"
            except:
                thread_hex = str(thread).upper()
        
        # Format payload
        if isinstance(payload, (bytes, bytearray)):
            payload_hex = '0x' + ' '.join(f"{b:02X}" for b in payload)
        elif isinstance(payload, str) and payload.startswith('0x'):
            payload_hex = payload
        else:
            payload_hex = ''
        
        # Write event line
        self.file_handle.write(f"{ts_full}  [{thread_hex}]  0x1FFB  Event  --  {event_name}\n")
        
        # Write payload line with proper indentation
        if payload_hex:
            self.file_handle.write(f"\t{ts_time} Event  0 : {event_name} (ID={event_id})  Payload = {payload_hex}\n")
        else:
            self.file_handle.write(f"\t{ts_time} Event  0 : {event_name} (ID={event_id})  Payload = \n")
        
        # Write payload string line
        self.file_handle.write(f"\t\tPayload String = {payload_str}\n\n")
    
    def write_stdout_data(self, stdout_text, radio_id=0, ts=None):
        """Write stdout data - not used in QCAT format"""
        pass
    
    def finalize(self):
        """Finalize output"""
        pass
    
    def close(self):
        """Close file"""
        self.finalize()
        self.file_handle.close()
