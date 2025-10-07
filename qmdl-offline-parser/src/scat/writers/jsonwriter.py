#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

import json
import datetime
import os
from pathlib import Path
import binascii

class JsonWriter:
    def write_stdout_data(self, stdout_text, radio_id=0, ts=None):
        """Stub method to prevent AttributeError during parsing."""
        pass
    def __init__(self, json_filename):
        self.json_filename = json_filename
        self.data = {
            "file_info": {
                "filename": None,
                "size_bytes": 0,
                "parsed_timestamp": datetime.datetime.now().isoformat(),
                "parser_version": "scat_enhanced"
            },
            "summary": {
                "total_messages": 0,
                "cellular_messages": 0,
                "rrc_messages": 0,
                "nas_messages": 0,
                "mac_messages": 0,
                "events": 0,
                "measurements": 0
            },
            "cell_info": [],
            "measurements": [],
            "rrc_messages": [],
            "nas_messages": [],
            "mac_messages": [],
            "events": [],
            "security_info": [],
            "ca_combos": [],
            "raw_messages": []
        }
        
        # Track unique cells and their information
        self.cells_seen = {}
        
    def set_input_filename(self, filename):
        """Set the input filename for metadata"""
        self.data["file_info"]["filename"] = filename
        if os.path.exists(filename):
            self.data["file_info"]["size_bytes"] = os.path.getsize(filename)

    def write_cp(self, sock_content, radio_id, ts):
        """Write control plane data"""
        self._increment_counter('total_messages')
        
        # Store raw message for debugging/completeness
        raw_msg = {
            "timestamp": ts.isoformat() if isinstance(ts, datetime.datetime) else str(ts),
            "radio_id": radio_id,
            "type": "control_plane",
            "data": binascii.hexlify(sock_content).decode('ascii'),
            "length": len(sock_content)
        }
        self.data["raw_messages"].append(raw_msg)

    def write_up(self, sock_content, radio_id, ts):
        """Write user plane data"""
        self._increment_counter('total_messages')
        
        # Store raw message for debugging/completeness
        raw_msg = {
            "timestamp": ts.isoformat() if isinstance(ts, datetime.datetime) else str(ts),
            "radio_id": radio_id,
            "type": "user_plane", 
            "data": binascii.hexlify(sock_content).decode('ascii'),
            "length": len(sock_content)
        }
        self.data["raw_messages"].append(raw_msg)

    def write_parsed_data(self, parsed_result, radio_id=0, ts=None):
        """Write structured parsed data"""
        if ts is None:
            ts = datetime.datetime.now()
            
        timestamp = ts.isoformat() if isinstance(ts, datetime.datetime) else str(ts)
        
        # Extract cell information
        if 'cell_info' in parsed_result:
            cell_data = parsed_result['cell_info'].copy()
            cell_data.update({
                "timestamp": timestamp,
                "radio_id": radio_id
            })
            
            # Track unique cells
            cell_key = f"{cell_data.get('pci', 0)}_{cell_data.get('earfcn_dl', 0)}_{radio_id}"
            if cell_key not in self.cells_seen:
                self.data["cell_info"].append(cell_data)
                self.cells_seen[cell_key] = True
        
        # Helper to process dict or list
        def process_item(item, target_list, extra_update=None, unique_key=None):
            if isinstance(item, list):
                for entry in item:
                    entry_copy = entry.copy()
                    if extra_update:
                        entry_copy.update(extra_update)
                    if unique_key:
                        key = unique_key(entry_copy)
                        if key not in self.cells_seen:
                            target_list.append(entry_copy)
                            self.cells_seen[key] = True
                    else:
                        target_list.append(entry_copy)
            elif isinstance(item, dict):
                entry_copy = item.copy()
                if extra_update:
                    entry_copy.update(extra_update)
                if unique_key:
                    key = unique_key(entry_copy)
                    if key not in self.cells_seen:
                        target_list.append(entry_copy)
                        self.cells_seen[key] = True
                else:
                    target_list.append(entry_copy)

        # Extract cell information
        if 'cell_info' in parsed_result:
            process_item(
                parsed_result['cell_info'],
                self.data["cell_info"],
                {"timestamp": timestamp, "radio_id": radio_id},
                lambda cell: f"{cell.get('pci', 0)}_{cell.get('earfcn_dl', 0)}_{radio_id}"
            )
        # Extract measurement data
        if 'measurement' in parsed_result:
            process_item(
                parsed_result['measurement'],
                self.data["measurements"],
                {"timestamp": timestamp, "radio_id": radio_id}
            )
            self._increment_counter('measurements')
        # Extract RRC messages
        if 'rrc_message' in parsed_result:
            process_item(
                parsed_result['rrc_message'],
                self.data["rrc_messages"],
                {"timestamp": timestamp, "radio_id": radio_id}
            )
            self._increment_counter('rrc_messages')
        # Extract NAS messages
        if 'nas_message' in parsed_result:
            process_item(
                parsed_result['nas_message'],
                self.data["nas_messages"],
                {"timestamp": timestamp, "radio_id": radio_id}
            )
            self._increment_counter('nas_messages')
        # Extract MAC messages
        if 'mac_message' in parsed_result:
            process_item(
                parsed_result['mac_message'],
                self.data["mac_messages"],
                {"timestamp": timestamp, "radio_id": radio_id}
            )
            self._increment_counter('mac_messages')
        # Extract events
        if 'event' in parsed_result:
            process_item(
                parsed_result['event'],
                self.data["events"],
                {"timestamp": timestamp, "radio_id": radio_id}
            )
            self._increment_counter('events')
        # Extract security information
        if 'security' in parsed_result:
            process_item(
                parsed_result['security'],
                self.data["security_info"],
                {"timestamp": timestamp, "radio_id": radio_id}
            )
        # Extract CA combos
        if 'ca_combo' in parsed_result:
            process_item(
                parsed_result['ca_combo'],
                self.data["ca_combos"],
                {"timestamp": timestamp, "radio_id": radio_id}
            )
        self._increment_counter('cellular_messages')
            
        # ...existing code...
    
    def _parse_stdout_line(self, line, timestamp, radio_id):
        """Parse individual stdout lines into structured data"""
        parsed = {}
        
        # LTE RRC SCell Info parsing
        if line.startswith('LTE RRC SCell Info:'):
            parsed['cell_info'] = self._parse_lte_rrc_scell_info(line, timestamp, radio_id)
            
        # LTE ML1 measurements
        elif 'LTE ML1' in line and ('Meas' in line or 'RSRP' in line or 'RSRQ' in line):
            parsed['measurement'] = self._parse_lte_measurement(line, timestamp, radio_id)
            
        # WCDMA measurements  
        elif line.startswith('WCDMA Search Cell:'):
            parsed['measurement'] = self._parse_wcdma_measurement(line, timestamp, radio_id)
            
        # GSM measurements
        elif 'GSM' in line and ('ARFCN' in line or 'RSSI' in line):
            parsed['measurement'] = self._parse_gsm_measurement(line, timestamp, radio_id)
            
        # RRC state changes
        elif 'RRC_STATE_CHANGE' in line:
            parsed['event'] = self._parse_rrc_state_change(line, timestamp, radio_id)
            
        # Security/cipher information
        elif 'Cipher' in line or 'Integrity' in line:
            parsed['security'] = self._parse_security_info(line, timestamp, radio_id)
            
        # CA combos
        elif 'CA Combo' in line or 'Component Carrier' in line:
            parsed['ca_combo'] = self._parse_ca_combo(line, timestamp, radio_id)
            
        return parsed if parsed else None
    
    def _parse_lte_rrc_scell_info(self, line, timestamp, radio_id):
        """Parse LTE RRC SCell Info line"""
        # Example: LTE RRC SCell Info: EARFCN: 1300/19300, Band: 3, Bandwidth: 20/20 MHz, PCI: 123, MCC: 310, MNC: 260, TAC/CID: 1234/5678
        cell_info = {
            "type": "lte_rrc_scell",
            "timestamp": timestamp,
            "radio_id": radio_id
        }
        
        import re
        
        # Extract EARFCN
        earfcn_match = re.search(r'EARFCN: (\d+)/(\d+)', line)
        if earfcn_match:
            cell_info["earfcn_dl"] = int(earfcn_match.group(1))
            cell_info["earfcn_ul"] = int(earfcn_match.group(2))
            
        # Extract Band
        band_match = re.search(r'Band: (\d+)', line)
        if band_match:
            cell_info["band"] = int(band_match.group(1))
            
        # Extract Bandwidth
        bw_match = re.search(r'Bandwidth: ([\d.]+)/([\d.]+) MHz', line)
        if bw_match:
            cell_info["bandwidth_dl_mhz"] = float(bw_match.group(1))
            cell_info["bandwidth_ul_mhz"] = float(bw_match.group(2))
            
        # Extract PCI
        pci_match = re.search(r'PCI: (\d+)', line)
        if pci_match:
            cell_info["pci"] = int(pci_match.group(1))
            
        # Extract MCC/MNC
        mcc_match = re.search(r'MCC: (\d+)', line)
        if mcc_match:
            cell_info["mcc"] = int(mcc_match.group(1))
            
        mnc_match = re.search(r'MNC: (\d+)', line)
        if mnc_match:
            cell_info["mnc"] = int(mnc_match.group(1))
            
        # Extract TAC/CID
        tac_cid_match = re.search(r'TAC/CID: (\d+)/(\d+)', line)
        if tac_cid_match:
            cell_info["tac"] = int(tac_cid_match.group(1))
            cell_info["cell_id"] = int(tac_cid_match.group(2))
        else:
            # Try hex format
            tac_cid_hex_match = re.search(r'xTAC/xCID: ([0-9a-fA-F]+)/([0-9a-fA-F]+)', line)
            if tac_cid_hex_match:
                cell_info["tac"] = int(tac_cid_hex_match.group(1), 16)
                cell_info["cell_id"] = int(tac_cid_hex_match.group(2), 16)
                
        return cell_info
    
    def _parse_lte_measurement(self, line, timestamp, radio_id):
        """Parse LTE measurement line"""
        measurement = {
            "type": "lte_measurement",
            "timestamp": timestamp,
            "radio_id": radio_id
        }
        
        import re
        
        # Extract RSRP
        rsrp_match = re.search(r'RSRP: ([-\d.]+)', line)
        if rsrp_match:
            measurement["rsrp_dbm"] = float(rsrp_match.group(1))
            
        # Extract RSRQ  
        rsrq_match = re.search(r'RSRQ: ([-\d.]+)', line)
        if rsrq_match:
            measurement["rsrq_db"] = float(rsrq_match.group(1))
            
        # Extract SINR/SNR
        sinr_match = re.search(r'SINR: ([-\d.]+)', line)
        if sinr_match:
            measurement["sinr_db"] = float(sinr_match.group(1))
            
        # Extract PCI if present
        pci_match = re.search(r'PCI: (\d+)', line)
        if pci_match:
            measurement["pci"] = int(pci_match.group(1))
            
        return measurement
    
    def _parse_wcdma_measurement(self, line, timestamp, radio_id):
        """Parse WCDMA measurement line"""
        measurement = {
            "type": "wcdma_measurement", 
            "timestamp": timestamp,
            "radio_id": radio_id
        }
        
        import re
        
        # Extract UARFCN
        uarfcn_match = re.search(r'UARFCN: (\d+)', line)
        if uarfcn_match:
            measurement["uarfcn"] = int(uarfcn_match.group(1))
            
        # Extract PSC
        psc_match = re.search(r'PSC: (\d+)', line)
        if psc_match:
            measurement["psc"] = int(psc_match.group(1))
            
        # Extract RSCP
        rscp_match = re.search(r'RSCP: ([-\d.]+)', line)
        if rscp_match:
            measurement["rscp_dbm"] = float(rscp_match.group(1))
            
        # Extract Ec/Io
        ecio_match = re.search(r'Ec/Io: ([-\d.]+)', line)
        if ecio_match:
            measurement["ecio_db"] = float(ecio_match.group(1))
            
        return measurement
    
    def _parse_gsm_measurement(self, line, timestamp, radio_id):
        """Parse GSM measurement line"""
        measurement = {
            "type": "gsm_measurement",
            "timestamp": timestamp, 
            "radio_id": radio_id
        }
        
        import re
        
        # Extract ARFCN
        arfcn_match = re.search(r'ARFCN: (\d+)', line)
        if arfcn_match:
            measurement["arfcn"] = int(arfcn_match.group(1))
            
        # Extract RSSI
        rssi_match = re.search(r'RSSI: ([-\d.]+)', line)
        if rssi_match:
            measurement["rssi_dbm"] = float(rssi_match.group(1))
            
        return measurement
    
    def _parse_rrc_state_change(self, line, timestamp, radio_id):
        """Parse RRC state change event"""
        event = {
            "type": "rrc_state_change",
            "timestamp": timestamp,
            "radio_id": radio_id
        }
        
        # Extract state information from the line
        if "RRC_IDLE" in line:
            event["state"] = "IDLE"
        elif "RRC_CONNECTED" in line:
            event["state"] = "CONNECTED"
        elif "RRC_CONNECTING" in line:
            event["state"] = "CONNECTING"
            
        return event
    
    def _parse_security_info(self, line, timestamp, radio_id):
        """Parse security/cipher information"""
        security = {
            "type": "security_info",
            "timestamp": timestamp,
            "radio_id": radio_id
        }
        
        import re
        
        # Extract cipher key
        ck_match = re.search(r'CK: ([0-9a-fA-Fx]+)', line)
        if ck_match:
            security["cipher_key"] = ck_match.group(1)
            
        # Extract algorithm
        alg_match = re.search(r'Algorithm: UEA(\d+)', line)
        if alg_match:
            security["algorithm"] = f"UEA{alg_match.group(1)}"
            
        return security
    
    def _parse_ca_combo(self, line, timestamp, radio_id):
        """Parse CA combo information"""
        ca_combo = {
            "type": "ca_combo",
            "timestamp": timestamp,
            "radio_id": radio_id,
            "raw_line": line
        }
        
        return ca_combo
    
    def _increment_counter(self, counter_name):
        """Increment a summary counter"""
        if counter_name in self.data["summary"]:
            self.data["summary"][counter_name] += 1
    
    def finalize(self):
        """Finalize and write the JSON file"""
        # Calculate percentages
        total = self.data["summary"]["total_messages"]
        if total > 0:
            cellular = self.data["summary"]["cellular_messages"]
            self.data["summary"]["cellular_percentage"] = round((cellular / total) * 100, 2)
            
        # Write JSON file
        with open(self.json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
            
    def close(self):
        """Close the writer and finalize output"""
        self.finalize()
