#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Enhanced WCDMA Log Parser for Qualcomm QMDL files
Handles high-frequency WCDMA messages with full QCAT compatibility
"""

from collections import namedtuple
import struct
import logging
import binascii
import scat.util as util
import scat.parsers.qualcomm.diagcmd as diagcmd

class DiagWcdmaEnhancedLogParser:
    def __init__(self, parent):
        self.parent = parent
        
        # High-frequency WCDMA message IDs from QCAT analysis
        self.process = {
            0x418B: lambda x, y, z: self.parse_wcdma_flexible_dl_rlc_am_pdu(x, y, z),
            0x421E: lambda x, y, z: self.parse_wcdma_mac_ehs_reassembly(x, y, z),
            0x4134: lambda x, y, z: self.parse_wcdma_tx_report(x, y, z),
            0x4222: lambda x, y, z: self.parse_wcdma_advanced_report(x, y, z),
            0x4344: lambda x, y, z: self.parse_wcdma_multi_carrier_eul(x, y, z),
            0x4322: lambda x, y, z: self.parse_wcdma_diversity_report(x, y, z),
            0x435D: lambda x, y, z: self.parse_wcdma_calibration_report(x, y, z),
        }
        
        self.no_process = {}

    def update_parameters(self, display_format, gsmtapv3):
        """Update display parameters"""
        pass

    def parse_wcdma_flexible_dl_rlc_am_pdu(self, pkt_header, pkt_body, args):
        """Parse WCDMA Flexible DL RLC AM PDU (0x418B)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 8:
            return None
            
        try:
            # Parse header
            sub_id = pkt_body[0] if len(pkt_body) > 0 else 1
            version = pkt_body[1] if len(pkt_body) > 1 else 0
            num_entities = pkt_body[2] if len(pkt_body) > 2 else 0
            
            # Format output exactly like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [F7]  0x418B  WCDMA Flexible DL RLC AM PDU\\n"
            stdout += f"Subscription ID = {sub_id}\\n"
            stdout += f"Version = {version}\\n"
            stdout += f"Number of DL Entities = {num_entities}\\n"
            
            # Parse entities
            pos = 4
            for i in range(min(num_entities, 8)):  # Limit to prevent excessive parsing
                if pos + 8 > len(pkt_body):
                    break
                    
                try:
                    logical_ch_id = pkt_body[pos] if pos < len(pkt_body) else 0
                    num_pdus = pkt_body[pos + 1] if pos + 1 < len(pkt_body) else 0
                    li_length = pkt_body[pos + 2] if pos + 2 < len(pkt_body) else 0
                    rlc_mode = pkt_body[pos + 3] if pos + 3 < len(pkt_body) else 0
                    
                    stdout += f"Entity Info[{i}]\\n"
                    stdout += f"   Data Logical Channel ID = {logical_ch_id}\\n"
                    stdout += f"   Number of PDUs Logged = {num_pdus}\\n"
                    stdout += f"   LI Length = {li_length}\\n"
                    
                    rlc_mode_map = {0: "TM", 1: "UM", 2: "AM"}
                    rlc_mode_str = rlc_mode_map.get(rlc_mode, f"Unknown ({rlc_mode})")
                    stdout += f"   RLC Mode = {rlc_mode_str}\\n"
                    
                    pos += 4
                    
                    # Parse PDU data
                    stdout += f"Entity Data[{i}]\\n"
                    stdout += f"   Entity Index = {i}{{ {logical_ch_id}, {num_pdus}, {li_length}  }}\\n"
                    
                    for j in range(min(num_pdus, 4)):  # Limit PDUs
                        if pos + 8 > len(pkt_body):
                            break
                            
                        pdu_size_bits = struct.unpack('<H', pkt_body[pos:pos+2])[0] if pos + 2 <= len(pkt_body) else 0
                        pdu_size_bytes = (pdu_size_bits + 7) // 8
                        
                        stdout += f"   PDU[{j}]\\n"
                        stdout += f"      PDU Size (in Bits) = {pdu_size_bits}\\n"
                        
                        if pos + 2 + pdu_size_bytes <= len(pkt_body):
                            raw_data = pkt_body[pos + 2:pos + 2 + min(pdu_size_bytes, 16)]
                            hex_data = ', '.join(f'0x{b:02X}' for b in raw_data)
                            stdout += f"      Raw Data = {{ {hex_data} }}\\n"
                            
                            # Basic RLC PDU analysis
                            if len(raw_data) > 0:
                                first_byte = raw_data[0]
                                if rlc_mode == 2:  # AM mode
                                    if first_byte & 0x80:  # Data PDU
                                        stdout += f"      ->, DATA PDU:: {logical_ch_id}\\n"
                                    else:  # Control PDU
                                        stdout += f"      ->, CTL PDU:: {logical_ch_id}, Type = STATUS\\n"
                                        if len(raw_data) >= 4:
                                            ack_sn = (raw_data[2] << 4) | (raw_data[3] >> 4)
                                            stdout += f"      SUFI[0]\\n"
                                            stdout += f"         ACK, LSN = 0x{ack_sn:X}- {ack_sn}\\n"
                        
                        pos += 2 + pdu_size_bytes
                        
                except Exception:
                    break
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing WCDMA Flexible DL RLC AM PDU: {e}')
            return None

    def parse_wcdma_mac_ehs_reassembly(self, pkt_header, pkt_body, args):
        """Parse WCDMA MAC-ehs Reassembly (0x421E)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 8:
            return None
            
        try:
            # Parse header
            sub_id = pkt_body[0] if len(pkt_body) > 0 else 1
            version = pkt_body[1] if len(pkt_body) > 1 else 0
            active_mac = pkt_body[2] if len(pkt_body) > 2 else 0
            num_pdus = pkt_body[3] if len(pkt_body) > 3 else 0
            
            # Format output exactly like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [E8]  0x421E  WCDMA MAC-ehs Reassembly\\n"
            stdout += f"Subscription ID = {sub_id}\\n"
            stdout += f"Version = {version}\\n"
            
            active_mac_map = {0: "MAC-d", 1: "MAC-ehs", 2: "MAC-i/is"}
            active_mac_str = active_mac_map.get(active_mac, f"Unknown ({active_mac})")
            stdout += f"Active MAC = {active_mac_str}\\n"
            stdout += f"Number of PDUs = {num_pdus}\\n"
            
            # Parse E-FACH TM mode
            if len(pkt_body) >= 8:
                efach_tm_mode = pkt_body[4] if len(pkt_body) > 4 else 0
                if efach_tm_mode == 0:
                    stdout += f"E-FACH TM mode = TSN does not contain Enahanced Cell FACH TM mode PDUs\\n"
                else:
                    stdout += f"E-FACH TM mode = Enhanced Cell FACH TM mode enabled\\n"
                    
            # Parse PDU information
            pos = 8
            for i in range(min(num_pdus, 16)):  # Limit to prevent excessive output
                if pos + 12 > len(pkt_body):
                    break
                    
                try:
                    pdu_info = struct.unpack('<LHHH', pkt_body[pos:pos+10]) if pos + 10 <= len(pkt_body) else (0, 0, 0, 0)
                    stdout += f"PDU[{i}]\\n"
                    stdout += f"   TSN = {pdu_info[0]}\\n"
                    stdout += f"   Size = {pdu_info[1]} bytes\\n"
                    stdout += f"   Queue ID = {pdu_info[2]}\\n"
                    stdout += f"   Status = {pdu_info[3]}\\n"
                    pos += 10
                except:
                    break
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing WCDMA MAC-ehs Reassembly: {e}')
            return None

    def parse_wcdma_tx_report(self, pkt_header, pkt_body, args):
        """Parse WCDMA TX Report (0x4134)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4134  WCDMA TX Report\\n"
            stdout += f"Version = {version}\\n"
            
            if len(pkt_body) >= 12:
                tx_power = struct.unpack('<h', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                pa_state = pkt_body[6] if len(pkt_body) > 6 else 0
                
                stdout += f"TX Power = {tx_power / 16.0:.2f} dBm\\n"
                stdout += f"PA State = {pa_state}\\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_advanced_report(self, pkt_header, pkt_body, args):
        """Parse WCDMA Advanced Report (0x4222)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4222  WCDMA Advanced Report\\n"
            stdout += f"Version = {version}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_multi_carrier_eul(self, pkt_header, pkt_body, args):
        """Parse WCDMA Multi Carrier EUL Combined L1 MAC (0x4344)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            sub_id = pkt_body[0] if len(pkt_body) > 0 else 1
            version = pkt_body[1] if len(pkt_body) > 1 else 0
            
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [EC]  0x4344  WCDMA Multi Carrier EUL Combined L1 MAC \\n"
            stdout += f"Subscription ID = {sub_id}\\n"
            stdout += f" \\n"
            stdout += f"Version = {version}\\n"
            
            if len(pkt_body) >= 8:
                carrier_state = pkt_body[2] if len(pkt_body) > 2 else 0
                carrier_state_map = {0: "SINGLE_CARRIER", 1: "DUAL_CARRIER"}
                carrier_state_str = carrier_state_map.get(carrier_state, f"Unknown ({carrier_state})")
                stdout += f"Carrier State = {carrier_state_str}\\n"
                stdout += f" \\n"
                stdout += f"Primary Carrier:\\n"
                stdout += f" \\n"
                
                if len(pkt_body) >= 16:
                    num_samples = pkt_body[8] if len(pkt_body) > 8 else 0
                    tti = pkt_body[9] if len(pkt_body) > 9 else 0
                    etfci_table = pkt_body[10] if len(pkt_body) > 10 else 0
                    start_cfn = struct.unpack('<H', pkt_body[12:14])[0] if len(pkt_body) >= 14 else 0
                    num_cells = pkt_body[14] if len(pkt_body) > 14 else 0
                    
                    stdout += f"\\tNumber of Samples = {num_samples}\\n"
                    stdout += f"\\tTTI = {tti}ms\\n"
                    stdout += f"\\tETFCI Table = {etfci_table}\\n"
                    stdout += f"\\tStart CFN = {start_cfn}\\n"
                    stdout += f"\\tNumber of Cells = {num_cells}\\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_diversity_report(self, pkt_header, pkt_body, args):
        """Parse WCDMA Diversity Report (0x4322)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4322  WCDMA Diversity Report\\n"
            stdout += f"Version = {version}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_calibration_report(self, pkt_header, pkt_body, args):
        """Parse WCDMA Calibration Report (0x435D)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x435D  WCDMA Calibration Report\\n"
            stdout += f"Version = {version}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None