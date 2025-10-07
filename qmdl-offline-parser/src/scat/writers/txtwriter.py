
#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later
"""
TxtWriter Module

Provides a class for writing parsed cellular log data to human-readable TXT format.
Tracks statistics and writes detailed message information for analysis and reporting.
Used by the main parser and batch wrapper to output readable results.
"""

import datetime
import os
from pathlib import Path
import binascii


class TxtWriter:
    """
    Handles writing parsed cellular log data to a human-readable TXT file.
    Tracks statistics and writes detailed message information for analysis and reporting.
    """
    def __init__(self, txt_filename):
        """
        Initialize TxtWriter with the output filename and default statistics.
        """
        self.txt_filename = txt_filename
        self.file_handle = open(txt_filename, 'w', encoding='utf-8')
        # Statistics tracking
        self.stats = {
            'total_messages': 0,
            'cellular_messages': 0,
            'cells_seen': set(),
            'bands_seen': set(),
            'technologies': set()
        }
        # Write header
        self._write_header()

    def _write_header(self):
        """
        Write file header with metadata and parser information, matching example.txt style.
        """
        self.file_handle.write("%MOBILE PARSED MESSAGE FILE\n")
        self.file_handle.write("%QCAT VERSION   : QCAT 07.01.250 patch 03\n")
        self.file_handle.write("%SILK VERSION   : SILK_9.83\n")
        self.file_handle.write(f"%LOG FILE NAME  : {os.path.basename(self.txt_filename)}\n\n")
        self.file_handle.write("%Confidential - Qualcomm Technologies, Inc.and / or its affiliated companies - May Contain Trade Secrets\n")

    def set_input_filename(self, filename):
        """
        Set the input filename for metadata and record its size if available.
        """
        self.file_handle.write(f"%LOG FILE NAME  : {filename}\n")
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            self.file_handle.write(f"%LOG FILE SIZE  : {size:,} bytes ({size/1024/1024:.2f} MB)\n")
        self.file_handle.write("\n")

    def write_cp(self, sock_content, radio_id, ts):
        """
        Write control plane data to the TXT file with improved section header and indentation.
        """
        self.stats['total_messages'] += 1
        timestamp_str = ts.strftime('%Y %b %d %H:%M:%S.%f')[:-3] if isinstance(ts, datetime.datetime) else str(ts)
        self.file_handle.write(f"\n{'='*80}\n[CONTROL PLANE MESSAGE] Radio {radio_id} | {timestamp_str}\n{'='*80}\n")
        self.file_handle.write(f"  Length: {len(sock_content)}\n")
        self.file_handle.write(f"  Data: {binascii.hexlify(sock_content).decode('ascii')}\n")

    def write_up(self, sock_content, radio_id, ts):
        """
        Write user plane data to the TXT file with improved section header and indentation.
        """
        self.stats['total_messages'] += 1
        timestamp_str = ts.strftime('%Y %b %d %H:%M:%S.%f')[:-3] if isinstance(ts, datetime.datetime) else str(ts)
        self.file_handle.write(f"\n{'='*80}\n[USER PLANE MESSAGE] Radio {radio_id} | {timestamp_str}\n{'='*80}\n")
        self.file_handle.write(f"  Length: {len(sock_content)}\n")
        self.file_handle.write(f"  Data: {binascii.hexlify(sock_content).decode('ascii')}\n")

    def write_parsed_data(self, parsed_result, radio_id=0, ts=None):
        """Write structured parsed data in human-readable format matching example.txt"""
        if ts is None:
            ts = datetime.datetime.now()
        timestamp_str = ts.strftime('%Y %b %d %H:%M:%S.%f')[:-3] if isinstance(ts, datetime.datetime) else str(ts)
        self.stats['cellular_messages'] += 1

        def process_item(item, write_func):
            if isinstance(item, list):
                for entry in item:
                    write_func(entry, timestamp_str, radio_id)
            elif isinstance(item, dict):
                write_func(item, timestamp_str, radio_id)

        # Write cell information
        if 'cell_info' in parsed_result:
            process_item(parsed_result['cell_info'], self._write_cell_info)
        # Write measurement data
        if 'measurement' in parsed_result:
            process_item(parsed_result['measurement'], self._write_measurement)
        # Write RRC messages
        if 'rrc_message' in parsed_result:
            process_item(parsed_result['rrc_message'], self._write_rrc_message)
        # Write NAS messages
        if 'nas_message' in parsed_result:
            process_item(parsed_result['nas_message'], self._write_nas_message)
        # Write MAC messages
        if 'mac_message' in parsed_result:
            process_item(parsed_result['mac_message'], self._write_mac_message)
        # Write events
        if 'event' in parsed_result:
            process_item(parsed_result['event'], self._write_event)
        # Write security information
        if 'security' in parsed_result:
            process_item(parsed_result['security'], self._write_security_info)
        # Write CA combos
        if 'ca_combo' in parsed_result:
            process_item(parsed_result['ca_combo'], self._write_ca_combo)
        
            # Helper to process dict or list
            def process_item(item, write_func):
                if isinstance(item, list):
                    for entry in item:
                        write_func(entry, timestamp_str, radio_id)
                elif isinstance(item, dict):
                    write_func(item, timestamp_str, radio_id)

            # Write cell information
            if 'cell_info' in parsed_result:
                process_item(parsed_result['cell_info'], self._write_cell_info)
            # Write measurement data
            if 'measurement' in parsed_result:
                process_item(parsed_result['measurement'], self._write_measurement)
            # Write RRC messages
            if 'rrc_message' in parsed_result:
                process_item(parsed_result['rrc_message'], self._write_rrc_message)
            # Write NAS messages
            if 'nas_message' in parsed_result:
                process_item(parsed_result['nas_message'], self._write_nas_message)
            # Write MAC messages
            if 'mac_message' in parsed_result:
                process_item(parsed_result['mac_message'], self._write_mac_message)
            # Write events
            if 'event' in parsed_result:
                process_item(parsed_result['event'], self._write_event)
            # Write security information
            if 'security' in parsed_result:
                process_item(parsed_result['security'], self._write_security_info)
            # Write CA combos
            if 'ca_combo' in parsed_result:
                process_item(parsed_result['ca_combo'], self._write_ca_combo)

    def write_stdout_data(self, stdout_text, radio_id=0, ts=None):
        """Write stdout data with enhanced parsing"""
        if not stdout_text:
            return
            
        if ts is None:
            ts = datetime.datetime.now()
        timestamp_str = ts.isoformat() if isinstance(ts, datetime.datetime) else str(ts)
        
        self.file_handle.write(f"[{timestamp_str}] Radio {radio_id} - Parsed Output\n")
        self.file_handle.write("-" * 60 + "\n")
        
        lines = stdout_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Categorize and enhance the line
            category = self._categorize_line(line)
            enhanced_line = self._enhance_line(line, category)
            
            self.file_handle.write(f"  [{category.upper()}] {enhanced_line}\n")
            
            # Update statistics
            self._update_stats_from_line(line)
            
        self.file_handle.write("-" * 60 + "\n\n")

    def _write_cell_info(self, cell_info, timestamp_str, radio_id):
        """Write detailed cell information with improved grouping and indentation"""
        self.file_handle.write(f"\n{'-'*60}\n[CELL INFORMATION] Radio {radio_id} | {timestamp_str}\n{'-'*60}\n")
        if 'pci' in cell_info:
            self.file_handle.write(f"  Physical Cell ID (PCI): {cell_info['pci']}\n")
            self.stats['cells_seen'].add(cell_info['pci'])
        if 'earfcn_dl' in cell_info and 'earfcn_ul' in cell_info:
            self.file_handle.write(f"  EARFCN (DL/UL): {cell_info['earfcn_dl']}/{cell_info['earfcn_ul']}\n")
        if 'band' in cell_info:
            self.file_handle.write(f"  Band: {cell_info['band']}\n")
            self.stats['bands_seen'].add(cell_info['band'])
            self.stats['technologies'].add('LTE')
        if 'bandwidth_dl_mhz' in cell_info and 'bandwidth_ul_mhz' in cell_info:
            self.file_handle.write(f"  Bandwidth (DL/UL): {cell_info['bandwidth_dl_mhz']}/{cell_info['bandwidth_ul_mhz']} MHz\n")
        if 'mcc' in cell_info and 'mnc' in cell_info:
            self.file_handle.write(f"  MCC/MNC: {cell_info['mcc']}/{cell_info['mnc']}\n")
        if 'tac' in cell_info:
            self.file_handle.write(f"  Tracking Area Code (TAC): {cell_info['tac']}\n")
        if 'cell_id' in cell_info:
            self.file_handle.write(f"  Cell ID: {cell_info['cell_id']}\n")

    def _write_measurement(self, measurement, timestamp_str, radio_id):
        """Write measurement data with improved tabular formatting"""
        self.file_handle.write(f"\n{'-'*60}\n[MEASUREMENT] Radio {radio_id} | {timestamp_str}\n{'-'*60}\n")
        meas_type = measurement.get('type', 'unknown')
        self.file_handle.write(f"  Type: {meas_type.upper()}\n")
        if 'rsrp_dbm' in measurement:
            self.file_handle.write(f"    RSRP: {measurement['rsrp_dbm']} dBm\n")
        if 'rsrq_db' in measurement:
            self.file_handle.write(f"    RSRQ: {measurement['rsrq_db']} dB\n")
        if 'sinr_db' in measurement:
            self.file_handle.write(f"    SINR: {measurement['sinr_db']} dB\n")
        if 'rscp_dbm' in measurement:
            self.file_handle.write(f"    RSCP: {measurement['rscp_dbm']} dBm\n")
        if 'ecio_db' in measurement:
            self.file_handle.write(f"    Ec/Io: {measurement['ecio_db']} dB\n")
        if 'rssi_dbm' in measurement:
            self.file_handle.write(f"    RSSI: {measurement['rssi_dbm']} dBm\n")
        if 'pci' in measurement:
            self.file_handle.write(f"    PCI: {measurement['pci']}\n")

    def _write_rrc_message(self, rrc_msg, timestamp_str, radio_id):
        """Write RRC message information"""
        self.file_handle.write(f"[{timestamp_str}] Radio {radio_id} - RRC MESSAGE\n")
        self.file_handle.write(f"  Message Type: {rrc_msg.get('type', 'Unknown')}\n")
        self.file_handle.write(f"  Direction: {rrc_msg.get('direction', 'Unknown')}\n")
        if 'data' in rrc_msg:
            self.file_handle.write(f"  Data: {rrc_msg['data']}\n")
        self.file_handle.write("\n")

    def _write_nas_message(self, nas_msg, timestamp_str, radio_id):
        """Write NAS message information"""
        self.file_handle.write(f"[{timestamp_str}] Radio {radio_id} - NAS MESSAGE\n")
        self.file_handle.write(f"  Message Type: {nas_msg.get('type', 'Unknown')}\n")
        self.file_handle.write(f"  Protocol: {nas_msg.get('protocol', 'Unknown')}\n")
        if 'data' in nas_msg:
            self.file_handle.write(f"  Data: {nas_msg['data']}\n")
        self.file_handle.write("\n")

    def _write_mac_message(self, mac_msg, timestamp_str, radio_id):
        """Write MAC message information"""
        self.file_handle.write(f"[{timestamp_str}] Radio {radio_id} - MAC MESSAGE\n")
        self.file_handle.write(f"  Message Type: {mac_msg.get('type', 'Unknown')}\n")
        if 'data' in mac_msg:
            self.file_handle.write(f"  Data: {mac_msg['data']}\n")
        self.file_handle.write("\n")

    def _write_event(self, event, timestamp_str, radio_id):
        """Write event information"""
        self.file_handle.write(f"[{timestamp_str}] Radio {radio_id} - EVENT: {event.get('type', 'Unknown').upper()}\n")
        
        if event.get('type') == 'rrc_state_change':
            self.file_handle.write(f"  State: {event.get('state', 'Unknown')}\n")
        
        if 'details' in event:
            self.file_handle.write(f"  Details: {event['details']}\n")
            
        self.file_handle.write("\n")

    def _write_security_info(self, security, timestamp_str, radio_id):
        """Write security information"""
        self.file_handle.write(f"[{timestamp_str}] Radio {radio_id} - SECURITY INFORMATION\n")
        self.file_handle.write("+" + "-" * 78 + "+\n")
        
        if 'cipher_key' in security:
            self.file_handle.write(f"| Cipher Key: {security['cipher_key']:<62} |\n")
            
        if 'algorithm' in security:
            self.file_handle.write(f"| Algorithm: {security['algorithm']:<63} |\n")
            
        self.file_handle.write("+" + "-" * 78 + "+\n\n")

    def _write_ca_combo(self, ca_combo, timestamp_str, radio_id):
        """Write CA combo information"""
        self.file_handle.write(f"[{timestamp_str}] Radio {radio_id} - CARRIER AGGREGATION\n")
        if 'raw_line' in ca_combo:
            self.file_handle.write(f"  {ca_combo['raw_line']}\n")
        self.file_handle.write("\n")

    def _categorize_line(self, line):
        """Categorize a log line"""
        line_upper = line.upper()
        
        if 'CELL' in line_upper and ('INFO' in line_upper or 'ID' in line_upper):
            return 'cell'
        elif any(x in line_upper for x in ['RSRP', 'RSRQ', 'RSSI', 'RSCP', 'SINR', 'MEAS']):
            return 'measurement'
        elif 'RRC' in line_upper:
            return 'rrc'
        elif 'NAS' in line_upper:
            return 'nas'
        elif 'MAC' in line_upper:
            return 'mac'
        elif any(x in line_upper for x in ['EVENT', 'STATE', 'TIMER']):
            return 'event'
        elif any(x in line_upper for x in ['CIPHER', 'SECURITY', 'KEY']):
            return 'security'
        elif 'CA' in line_upper or 'COMBO' in line_upper:
            return 'ca'
        else:
            return 'other'

    def _enhance_line(self, line, category):
        """Enhance a line with additional formatting"""
        if category == 'cell':
            return f"📡 {line}"
        elif category == 'measurement':
            return f"📊 {line}"
        elif category == 'rrc':
            return f"📻 {line}"
        elif category == 'nas':
            return f"🌐 {line}"
        elif category == 'mac':
            return f"🔗 {line}"
        elif category == 'event':
            return f"⚡ {line}"
        elif category == 'security':
            return f"🔒 {line}"
        elif category == 'ca':
            return f"📶 {line}"
        else:
            return f"ℹ️  {line}"

    def _update_stats_from_line(self, line):
        """Update statistics based on line content"""
        line_upper = line.upper()
        
        # Detect technologies
        if 'LTE' in line_upper:
            self.stats['technologies'].add('LTE')
        elif 'WCDMA' in line_upper or 'UMTS' in line_upper:
            self.stats['technologies'].add('WCDMA/UMTS')
        elif 'GSM' in line_upper:
            self.stats['technologies'].add('GSM')
        elif 'NR' in line_upper or '5G' in line_upper:
            self.stats['technologies'].add('5G NR')

    def write_summary(self):
        """Write summary section"""
        self.file_handle.write("\n" + "="*80 + "\n")
        self.file_handle.write("ANALYSIS SUMMARY\n")
        self.file_handle.write("="*80 + "\n\n")
        
        self.file_handle.write(f"Total Messages Processed: {self.stats['total_messages']:,}\n")
        self.file_handle.write(f"Cellular Messages: {self.stats['cellular_messages']:,}\n")
        
        if self.stats['total_messages'] > 0:
            percentage = (self.stats['cellular_messages'] / self.stats['total_messages']) * 100
            self.file_handle.write(f"Cellular Message Percentage: {percentage:.2f}%\n")
        
        self.file_handle.write(f"\nUnique Cells Detected: {len(self.stats['cells_seen'])}\n")
        if self.stats['cells_seen']:
            self.file_handle.write(f"Cell IDs: {', '.join(map(str, sorted(self.stats['cells_seen'])))}\n")
            
        self.file_handle.write(f"\nBands Detected: {len(self.stats['bands_seen'])}\n")
        if self.stats['bands_seen']:
            self.file_handle.write(f"Band Numbers: {', '.join(map(str, sorted(self.stats['bands_seen'])))}\n")
            
        self.file_handle.write(f"\nTechnologies Detected: {len(self.stats['technologies'])}\n")
        if self.stats['technologies']:
            self.file_handle.write(f"Technologies: {', '.join(sorted(self.stats['technologies']))}\n")
            
        self.file_handle.write("\n" + "="*80 + "\n")

    def finalize(self):
        """Finalize the report"""
        self.write_summary()
        self.file_handle.write(f"Report completed at: {datetime.datetime.now().isoformat()}\n")
        self.file_handle.write("="*80 + "\n")

    def close(self):
        """Close the writer"""
        self.finalize()
        self.file_handle.close()
