#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

"""
WCDMA Signaling Parser for Qualcomm QMDL files
Handles WCDMA signaling messages with ASN.1 decoding
"""

from collections import namedtuple
import struct
import logging
import binascii
import scat.util as util
import scat.parsers.qualcomm.diagcmd as diagcmd

class DiagWcdmaSignalingParser:
    def __init__(self, parent):
        self.parent = parent
        
        # WCDMA signaling message IDs
        self.process = {
            0x412F: lambda x, y, z: self.parse_wcdma_signaling_messages(x, y, z),
            0x4135: lambda x, y, z: self.parse_wcdma_cell_id(x, y, z),
            0x4342: lambda x, y, z: self.parse_wcdma_search_cell_reselection(x, y, z),
            0x423F: lambda x, y, z: self.parse_wcdma_agc(x, y, z),
            0x421C: lambda x, y, z: self.parse_wcdma_finger_info(x, y, z),
            0x41D3: lambda x, y, z: self.parse_wcdma_tx_agc_adj(x, y, z),
            0x4345: lambda x, y, z: self.parse_wcdma_rrc_states(x, y, z),
            0x4176: lambda x, y, z: self.parse_wcdma_rx_diversity(x, y, z),
            0x41B2: lambda x, y, z: self.parse_wcdma_compressed_mode(x, y, z),
            0x19B5: lambda x, y, z: self.parse_wcdma_rrc_ota_message(x, y, z),
        }
        
        self.no_process = {}

    def update_parameters(self, display_format, gsmtapv3):
        pass

    def parse_wcdma_signaling_messages(self, pkt_header, pkt_body, args):
        """Parse WCDMA Signaling Messages (0x412F)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 16:
            return None
            
        try:
            sub_id = pkt_body[0]
            channel_type = pkt_body[1] if len(pkt_body) > 1 else 0
            rb_id = pkt_body[2] if len(pkt_body) > 2 else 0
            uarfcn = struct.unpack('<H', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
            psc = struct.unpack('<H', pkt_body[6:8])[0] if len(pkt_body) >= 8 else 0
            msg_len = struct.unpack('<H', pkt_body[8:10])[0] if len(pkt_body) >= 10 else 0
            
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            # Channel type mapping
            channel_map = {
                0: "DL_BCCH_BCH", 1: "DL_BCCH_FACH", 2: "DL_PCCH", 3: "DL_CCCH",
                4: "DL_DCCH", 5: "UL_CCCH", 6: "UL_DCCH", 7: "DL_SHCCH"
            }
            channel_str = channel_map.get(channel_type, f"UNKNOWN_{channel_type}")
            
            # Determine message type from payload
            payload_type = "Complete SIB List"
            if len(pkt_body) > 16:
                payload_indicator = pkt_body[16] if len(pkt_body) > 16 else 0
                if payload_indicator == 0x01:
                    payload_type = "First Segment"
                elif payload_indicator == 0x02:
                    payload_type = "Subsequent Segment"
                elif payload_indicator == 0x03:
                    payload_type = "Last Segment Short"
                elif payload_indicator == 0x04:
                    payload_type = "Last Segment Long"
            
            stdout = f"{ts_str}  [99]  0x412F  WCDMA Signaling Messages  --  {channel_str} {payload_type}\\n"
            stdout += f"Subscription ID = {sub_id}\\n"
            stdout += f"\\tChannel Type = {channel_str}, Radio Bearer ID = {rb_id}, Uarfcn = {uarfcn}, Psc = {psc}, Message Length = {msg_len}\\n"
            
            # ASN.1 interpretation
            stdout += f"Interpreted PDU:\\n"
            stdout += f"value BCCH-BCH-Message ::= \\n"
            stdout += f"{{\\n"
            stdout += f"  message \\n"
            stdout += f"  {{\\n"
            
            # Parse SFN from payload
            if len(pkt_body) >= 20:
                sfn_prime = struct.unpack('<H', pkt_body[18:20])[0] if len(pkt_body) >= 20 else 0
                stdout += f"    sfn-Prime {sfn_prime},\\n"
                
                if payload_type == "Complete SIB List":
                    stdout += f"    payload completeSIB-List : \\n"
                    stdout += f"      {{\\n"
                    # Parse SIB list
                    if len(pkt_body) >= 24:
                        num_sibs = pkt_body[22] if len(pkt_body) > 22 else 0
                        stdout += f"        segCount {num_sibs},\\n"
                        stdout += f"        sib-Data-variable\\n"
                        stdout += f"        {{\\n"
                        
                        pos = 24
                        for i in range(min(num_sibs, 8)):
                            if pos + 4 > len(pkt_body):
                                break
                            sib_type = pkt_body[pos] if pos < len(pkt_body) else 0
                            sib_len = pkt_body[pos + 1] if pos + 1 < len(pkt_body) else 0
                            stdout += f"          sib{sib_type} : length {sib_len}\\n"
                            pos += 4 + sib_len
                            
                        stdout += f"        }}\\n"
                    stdout += f"      }}\\n"
                elif payload_type == "First Segment":
                    stdout += f"    payload firstSegment : \\n"
                    stdout += f"      {{\\n"
                    stdout += f"        sib-Type sib1,\\n"
                    stdout += f"        seg-Count 4,\\n"
                    stdout += f"        sib-Data-fixed\\n"
                    stdout += f"      }}\\n"
                elif payload_type == "Subsequent Segment":
                    stdout += f"    payload subsequentSegment : \\n"
                    stdout += f"      {{\\n"
                    stdout += f"        sib-Type sib1,\\n"
                    stdout += f"        segmentIndex 2,\\n"
                    stdout += f"        sib-Data-fixed\\n"
                    stdout += f"      }}\\n"
                elif "Last Segment" in payload_type:
                    stdout += f"    payload lastSegmentShort : \\n"
                    stdout += f"      {{\\n"
                    stdout += f"        sib-Type sib1,\\n"
                    stdout += f"        segmentIndex 3,\\n"
                    stdout += f"        sib-Data-variable\\n"
                    stdout += f"      }}\\n"
                    
            stdout += f"  }}\\n"
            stdout += f"}}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing WCDMA Signaling Messages: {e}')
            return None

    def parse_wcdma_cell_id(self, pkt_header, pkt_body, args):
        """Parse WCDMA Cell ID (0x4135)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4135  WCDMA Cell ID\\n"
            stdout += f"Version = {version}\\n"
            
            if len(pkt_body) >= 12:
                cell_id = struct.unpack('<L', pkt_body[4:8])[0] if len(pkt_body) >= 8 else 0
                psc = struct.unpack('<H', pkt_body[8:10])[0] if len(pkt_body) >= 10 else 0
                
                stdout += f"Cell ID = {cell_id}\\n"
                stdout += f"Primary Scrambling Code = {psc}\\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_search_cell_reselection(self, pkt_header, pkt_body, args):
        """Parse WCDMA Search Cell Reselection (0x4342)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4342  WCDMA Search Cell Reselection\\n"
            stdout += f"Version = {version}\\n"
            
            if len(pkt_body) >= 16:
                search_type = pkt_body[1] if len(pkt_body) > 1 else 0
                num_cells = pkt_body[2] if len(pkt_body) > 2 else 0
                
                search_type_map = {0: "INITIAL_SEARCH", 1: "RESELECTION", 2: "HANDOVER"}
                search_type_str = search_type_map.get(search_type, f"UNKNOWN_{search_type}")
                
                stdout += f"Search Type = {search_type_str}\\n"
                stdout += f"Number of Cells = {num_cells}\\n"
                
                # Parse cell information
                pos = 8
                for i in range(min(num_cells, 8)):
                    if pos + 12 > len(pkt_body):
                        break
                        
                    psc = struct.unpack('<H', pkt_body[pos:pos+2])[0] if pos + 2 <= len(pkt_body) else 0
                    rscp = struct.unpack('<h', pkt_body[pos+2:pos+4])[0] if pos + 4 <= len(pkt_body) else 0
                    ecio = struct.unpack('<h', pkt_body[pos+4:pos+6])[0] if pos + 6 <= len(pkt_body) else 0
                    
                    stdout += f"Cell[{i}]: PSC = {psc}, RSCP = {rscp/16.0:.1f} dBm, Ec/Io = {ecio/16.0:.1f} dB\\n"
                    pos += 12
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_agc(self, pkt_header, pkt_body, args):
        """Parse WCDMA AGC (0x423F)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x423F  WCDMA AGC\\n"
            stdout += f"Version = {version}\\n"
            
            if len(pkt_body) >= 16:
                agc_value = struct.unpack('<h', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                lna_state = pkt_body[6] if len(pkt_body) > 6 else 0
                
                stdout += f"AGC Value = {agc_value}\\n"
                stdout += f"LNA State = {lna_state}\\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_finger_info(self, pkt_header, pkt_body, args):
        """Parse WCDMA Finger Info (0x421C)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x421C  WCDMA Finger Info\\n"
            stdout += f"Version = {version}\\n"
            
            if len(pkt_body) >= 12:
                num_fingers = pkt_body[1] if len(pkt_body) > 1 else 0
                stdout += f"Number of Fingers = {num_fingers}\\n"
                
                pos = 4
                for i in range(min(num_fingers, 6)):
                    if pos + 8 > len(pkt_body):
                        break
                        
                    finger_id = pkt_body[pos] if pos < len(pkt_body) else 0
                    pn_pos = struct.unpack('<H', pkt_body[pos+2:pos+4])[0] if pos + 4 <= len(pkt_body) else 0
                    energy = struct.unpack('<H', pkt_body[pos+4:pos+6])[0] if pos + 6 <= len(pkt_body) else 0
                    
                    stdout += f"Finger[{i}]: ID = {finger_id}, PN Position = {pn_pos}, Energy = {energy}\\n"
                    pos += 8
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_tx_agc_adj(self, pkt_header, pkt_body, args):
        """Parse WCDMA TX AGC Adj (0x41D3)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x41D3  WCDMA TX AGC Adj\\n"
            stdout += f"Version = {version}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_rrc_states(self, pkt_header, pkt_body, args):
        """Parse WCDMA RRC States (0x4345)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4345  WCDMA RRC States\\n"
            stdout += f"Version = {version}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_rx_diversity(self, pkt_header, pkt_body, args):
        """Parse WCDMA RX Diversity (0x4176)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4176  WCDMA RX Diversity\\n"
            stdout += f"Version = {version}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_compressed_mode(self, pkt_header, pkt_body, args):
        """Parse WCDMA Compressed Mode (0x41B2)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x41B2  WCDMA Compressed Mode\\n"
            stdout += f"Version = {version}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_wcdma_rrc_ota_message(self, pkt_header, pkt_body, args):
        """Parse WCDMA RRC OTA Message (0x19B5)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x19B5  WCDMA RRC OTA Message\\n"
            stdout += f"Version = {version}\\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None