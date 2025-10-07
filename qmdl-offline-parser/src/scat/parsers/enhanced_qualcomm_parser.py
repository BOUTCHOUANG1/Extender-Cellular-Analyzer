#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Enhanced Qualcomm Parser that extracts structured data for JSON/TXT output
"""

import datetime
import logging
import re
import binascii
from collections import namedtuple
import struct

class EnhancedQualcommParser:
    """Enhanced parser that extracts structured data from stdout messages"""
    
    def __init__(self, base_parser):
        self.base_parser = base_parser
        self.logger = logging.getLogger('scat.enhanced_qualcomm_parser')
        
    def enhance_parse_result(self, parse_result):
        """Enhance parse result with structured data extraction"""
        if not parse_result:
            return parse_result
            
        enhanced_result = parse_result.copy()
        
        # Extract structured data from stdout
        if 'stdout' in parse_result and parse_result['stdout']:
            structured_data = self._extract_structured_data(parse_result['stdout'])
            enhanced_result.update(structured_data)
            
        return enhanced_result
    
    def _extract_structured_data(self, stdout_text):
        """Extract structured data from stdout text"""
        structured = {}
        lines = stdout_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # LTE RRC SCell Info
            if line.startswith('LTE RRC SCell Info:'):
                structured['cell_info'] = self._parse_lte_rrc_scell_info(line)
                
            # LTE measurements
            elif 'LTE ML1' in line and any(x in line for x in ['Meas', 'RSRP', 'RSRQ', 'SINR']):
                if 'measurement' not in structured:
                    structured['measurement'] = []
                meas = self._parse_lte_measurement(line)
                if meas:
                    structured['measurement'].append(meas)
                    
            # WCDMA measurements
            elif line.startswith('WCDMA Search Cell:'):
                if 'measurement' not in structured:
                    structured['measurement'] = []
                meas = self._parse_wcdma_measurement(line)
                if meas:
                    structured['measurement'].append(meas)
                    
            # GSM measurements
            elif 'GSM' in line and any(x in line for x in ['ARFCN', 'RSSI']):
                if 'measurement' not in structured:
                    structured['measurement'] = []
                meas = self._parse_gsm_measurement(line)
                if meas:
                    structured['measurement'].append(meas)
                    
            # RRC messages
            elif 'RRC' in line and any(x in line for x in ['DL', 'UL', 'MSG']):
                structured['rrc_message'] = self._parse_rrc_message(line)
                
            # NAS messages
            elif 'NAS' in line or 'EMM' in line or 'ESM' in line:
                structured['nas_message'] = self._parse_nas_message(line)
                
            # MAC messages
            elif 'MAC' in line:
                structured['mac_message'] = self._parse_mac_message(line)
                
            # Security/cipher information
            elif any(x in line for x in ['Cipher', 'Integrity', 'Algorithm']):
                structured['security'] = self._parse_security_info(line)
                
            # CA combos
            elif any(x in line for x in ['CA Combo', 'Component Carrier']):
                structured['ca_combo'] = self._parse_ca_combo(line)
                
            # Events
            elif any(x in line for x in ['Timer', 'State', 'Event']):
                structured['event'] = self._parse_event(line)
                
        return structured
    
    def _parse_lte_rrc_scell_info(self, line):
        """Parse LTE RRC SCell Info line into structured data"""
        cell_info = {
            'type': 'lte_rrc_scell',
            'technology': 'LTE'
        }
        
        # Extract EARFCN
        earfcn_match = re.search(r'EARFCN: (\d+)/(\d+)', line)
        if earfcn_match:
            cell_info['earfcn_dl'] = int(earfcn_match.group(1))
            cell_info['earfcn_ul'] = int(earfcn_match.group(2))
            
        # Extract Band
        band_match = re.search(r'Band: (\d+)', line)
        if band_match:
            cell_info['band'] = int(band_match.group(1))
            
        # Extract Bandwidth  
        bw_match = re.search(r'Bandwidth: ([\d.]+)/([\d.]+) MHz', line)
        if bw_match:
            cell_info['bandwidth_dl_mhz'] = float(bw_match.group(1))
            cell_info['bandwidth_ul_mhz'] = float(bw_match.group(2))
        else:
            # Try PRB format
            bw_prb_match = re.search(r'Bandwidth: (\d+)/(\d+) PRBs', line)
            if bw_prb_match:
                cell_info['bandwidth_dl_prb'] = int(bw_prb_match.group(1))
                cell_info['bandwidth_ul_prb'] = int(bw_prb_match.group(2))
                
        # Extract PCI
        pci_match = re.search(r'PCI: (\d+)', line)
        if pci_match:
            cell_info['pci'] = int(pci_match.group(1))
            
        # Extract MCC/MNC
        mcc_match = re.search(r'MCC: (\d+)', line)
        if mcc_match:
            cell_info['mcc'] = int(mcc_match.group(1))
            
        mnc_match = re.search(r'MNC: (\d+)', line)
        if mnc_match:
            cell_info['mnc'] = int(mnc_match.group(1))
            
        # Extract TAC/CID (decimal)
        tac_cid_match = re.search(r'TAC/CID: (\d+)/(\d+)', line)
        if tac_cid_match:
            cell_info['tac'] = int(tac_cid_match.group(1))
            cell_info['cell_id'] = int(tac_cid_match.group(2))
        else:
            # Try hex format
            tac_cid_hex_match = re.search(r'xTAC/xCID: ([0-9a-fA-F]+)/([0-9a-fA-F]+)', line)
            if tac_cid_hex_match:
                cell_info['tac'] = int(tac_cid_hex_match.group(1), 16)
                cell_info['cell_id'] = int(tac_cid_hex_match.group(2), 16)
                cell_info['tac_hex'] = tac_cid_hex_match.group(1)
                cell_info['cell_id_hex'] = tac_cid_hex_match.group(2)
                
        return cell_info
    
    def _parse_lte_measurement(self, line):
        """Parse LTE measurement line"""
        measurement = {
            'type': 'lte_measurement',
            'technology': 'LTE'
        }
        
        # Extract PCI
        pci_match = re.search(r'PCI: (\d+)', line)
        if pci_match:
            measurement['pci'] = int(pci_match.group(1))
            
        # Extract EARFCN
        earfcn_match = re.search(r'EARFCN: (\d+)', line)
        if earfcn_match:
            measurement['earfcn'] = int(earfcn_match.group(1))
            
        # Extract RSRP
        rsrp_match = re.search(r'RSRP: ([-\d.]+)', line)
        if rsrp_match:
            measurement['rsrp_dbm'] = float(rsrp_match.group(1))
            
        # Extract RSRQ
        rsrq_match = re.search(r'RSRQ: ([-\d.]+)', line)
        if rsrq_match:
            measurement['rsrq_db'] = float(rsrq_match.group(1))
            
        # Extract SINR/SNR
        sinr_match = re.search(r'SINR: ([-\d.]+)', line)
        if sinr_match:
            measurement['sinr_db'] = float(sinr_match.group(1))
        else:
            snr_match = re.search(r'SNR: ([-\d.]+)', line)
            if snr_match:
                measurement['snr_db'] = float(snr_match.group(1))
                
        # Extract SFN/SubFN
        sfn_match = re.search(r'SFN/SubFN: (\d+)/(\d+)', line)
        if sfn_match:
            measurement['sfn'] = int(sfn_match.group(1))
            measurement['subfn'] = int(sfn_match.group(2))
            
        return measurement if len(measurement) > 2 else None
    
    def _parse_wcdma_measurement(self, line):
        """Parse WCDMA measurement line"""
        measurement = {
            'type': 'wcdma_measurement',
            'technology': 'WCDMA'
        }
        
        # Extract UARFCN
        uarfcn_match = re.search(r'UARFCN: (\d+)', line)
        if uarfcn_match:
            measurement['uarfcn'] = int(uarfcn_match.group(1))
            
        # Extract PSC
        psc_match = re.search(r'PSC: (\d+)', line)
        if psc_match:
            measurement['psc'] = int(psc_match.group(1))
            
        # Extract RSCP
        rscp_match = re.search(r'RSCP: ([-\d.]+)', line)
        if rscp_match:
            measurement['rscp_dbm'] = float(rscp_match.group(1))
            
        # Extract Ec/Io
        ecio_match = re.search(r'Ec/Io: ([-\d.]+)', line)
        if ecio_match:
            measurement['ecio_db'] = float(ecio_match.group(1))
            
        # Extract cell count info
        cell_count_match = re.search(r'(\d+) 3G cells, (\d+) 2G cells', line)
        if cell_count_match:
            measurement['cells_3g'] = int(cell_count_match.group(1))
            measurement['cells_2g'] = int(cell_count_match.group(2))
            
        return measurement if len(measurement) > 2 else None
    
    def _parse_gsm_measurement(self, line):
        """Parse GSM measurement line"""
        measurement = {
            'type': 'gsm_measurement',
            'technology': 'GSM'
        }
        
        # Extract ARFCN
        arfcn_match = re.search(r'ARFCN: (\d+)', line)
        if arfcn_match:
            measurement['arfcn'] = int(arfcn_match.group(1))
            
        # Extract RSSI
        rssi_match = re.search(r'RSSI: ([-\d.]+)', line)
        if rssi_match:
            measurement['rssi_dbm'] = float(rssi_match.group(1))
            
        # Extract rank
        rank_match = re.search(r'Rank: (\d+)', line)
        if rank_match:
            measurement['rank'] = int(rank_match.group(1))
            
        return measurement if len(measurement) > 2 else None
    
    def _parse_rrc_message(self, line):
        """Parse RRC message line"""
        rrc_msg = {
            'type': 'rrc_message',
            'protocol': 'RRC'
        }
        
        # Determine direction
        if 'DL' in line or 'Downlink' in line or 'Incoming' in line:
            rrc_msg['direction'] = 'downlink'
        elif 'UL' in line or 'Uplink' in line or 'Outgoing' in line:
            rrc_msg['direction'] = 'uplink'
            
        # Extract message type
        if 'SystemInformation' in line:
            rrc_msg['message_type'] = 'SystemInformation'
        elif 'MIB' in line:
            rrc_msg['message_type'] = 'MIB'
        elif 'RRCConnectionRequest' in line:
            rrc_msg['message_type'] = 'RRCConnectionRequest'
        elif 'RRCConnectionSetup' in line:
            rrc_msg['message_type'] = 'RRCConnectionSetup'
        elif 'RRCConnectionReconfiguration' in line:
            rrc_msg['message_type'] = 'RRCConnectionReconfiguration'
            
        rrc_msg['raw_line'] = line
        return rrc_msg
    
    def _parse_nas_message(self, line):
        """Parse NAS message line"""
        nas_msg = {
            'type': 'nas_message',
            'protocol': 'NAS'
        }
        
        # Determine direction
        if 'Incoming' in line or 'DL' in line:
            nas_msg['direction'] = 'downlink'
        elif 'Outgoing' in line or 'UL' in line:
            nas_msg['direction'] = 'uplink'
            
        # Determine NAS protocol
        if 'EMM' in line:
            nas_msg['nas_protocol'] = 'EMM'
        elif 'ESM' in line:
            nas_msg['nas_protocol'] = 'ESM'
            
        # Extract message type
        if 'Attach' in line:
            nas_msg['message_type'] = 'Attach'
        elif 'TAU' in line:
            nas_msg['message_type'] = 'TrackingAreaUpdate'
        elif 'Service' in line:
            nas_msg['message_type'] = 'Service'
        elif 'Detach' in line:
            nas_msg['message_type'] = 'Detach'
            
        nas_msg['raw_line'] = line
        return nas_msg
    
    def _parse_mac_message(self, line):
        """Parse MAC message line"""
        mac_msg = {
            'type': 'mac_message',
            'protocol': 'MAC'
        }
        
        # Extract MAC message type
        if 'RACH' in line:
            mac_msg['message_type'] = 'RACH'
            if 'Trigger' in line:
                mac_msg['rach_type'] = 'trigger'
            elif 'Response' in line:
                mac_msg['rach_type'] = 'response'
        elif 'Transport Block' in line:
            mac_msg['message_type'] = 'TransportBlock'
            if 'DL' in line:
                mac_msg['direction'] = 'downlink'
            elif 'UL' in line:
                mac_msg['direction'] = 'uplink'
                
        mac_msg['raw_line'] = line
        return mac_msg
    
    def _parse_security_info(self, line):
        """Parse security/cipher information"""
        security = {
            'type': 'security_info'
        }
        
        # Extract cipher key
        ck_match = re.search(r'CK: ([0-9a-fA-Fx]+)', line)
        if ck_match:
            security['cipher_key'] = ck_match.group(1)
            
        # Extract integrity key
        ik_match = re.search(r'IK: ([0-9a-fA-Fx]+)', line)
        if ik_match:
            security['integrity_key'] = ik_match.group(1)
            
        # Extract algorithm
        uea_match = re.search(r'Algorithm: UEA(\d+)', line)
        if uea_match:
            security['cipher_algorithm'] = f"UEA{uea_match.group(1)}"
            
        uia_match = re.search(r'Algorithm: UIA(\d+)', line)
        if uia_match:
            security['integrity_algorithm'] = f"UIA{uia_match.group(1)}"
            
        # Extract count
        count_match = re.search(r'Count C: 0x([0-9a-fA-F]+)', line)
        if count_match:
            security['count'] = count_match.group(1)
            
        security['raw_line'] = line
        return security
    
    def _parse_ca_combo(self, line):
        """Parse CA combo information"""
        ca_combo = {
            'type': 'ca_combo'
        }
        
        # Extract component carriers
        cc_matches = re.findall(r'Band (\d+)', line)
        if cc_matches:
            ca_combo['bands'] = [int(x) for x in cc_matches]
            ca_combo['num_carriers'] = len(cc_matches)
            
        ca_combo['raw_line'] = line
        return ca_combo
    
    def _parse_event(self, line):
        """Parse event information"""
        event = {
            'type': 'event'
        }
        
        # Timer events
        if 'Timer' in line:
            event['event_type'] = 'timer'
            if 'Start' in line:
                event['timer_action'] = 'start'
            elif 'Expiry' in line or 'Expired' in line:
                event['timer_action'] = 'expiry'
                
        # State changes
        elif 'State' in line:
            event['event_type'] = 'state_change'
            if 'RRC_IDLE' in line:
                event['state'] = 'IDLE'
            elif 'RRC_CONNECTED' in line:
                event['state'] = 'CONNECTED'
            elif 'RRC_CONNECTING' in line:
                event['state'] = 'CONNECTING'
                
        # RACH events
        elif 'RACH' in line:
            event['event_type'] = 'rach'
            
        event['raw_line'] = line
        return event
