#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

"""
UMTS NAS Log Parser for Qualcomm QMDL files
Handles UMTS NAS messages for network attachment states
"""

from collections import namedtuple
import struct
import logging
import binascii
import scat.util as util
import scat.parsers.qualcomm.diagcmd as diagcmd

class DiagUmtsNasLogParser:
    def __init__(self, parent):
        self.parent = parent
        
        # UMTS NAS message IDs from QCAT output analysis
        self.process = {
            0x7152: lambda x, y, z: self.parse_umts_nas_fplmn_list(x, y, z),
            0x7132: lambda x, y, z: self.parse_umts_nas_reg_state(x, y, z),
            0x7131: lambda x, y, z: self.parse_umts_nas_mm_state(x, y, z),
            0x7130: lambda x, y, z: self.parse_umts_nas_gmm_state(x, y, z),
        }
        
        self.no_process = {}

    def update_parameters(self, display_format, gsmtapv3):
        """Update display parameters"""
        pass

    def parse_umts_nas_fplmn_list(self, pkt_header, pkt_body, args):
        """Parse UMTS NAS_FPLMN List (0x7152)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 4:
            return None
            
        try:
            # Parse basic fields
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x7152  UMTS NAS_FPLMN List\n"
            stdout += f"Version = {version}\n"
            
            # Parse FPLMN list data
            if len(pkt_body) >= 8:
                num_fplmns = pkt_body[1] if len(pkt_body) > 1 else 0
                stdout += f"Number of FPLMNs = {num_fplmns}\n"
                
                # Parse individual FPLMN entries
                pos = 4
                for i in range(min(num_fplmns, 16)):  # Limit to prevent excessive output
                    if pos + 3 > len(pkt_body):
                        break
                        
                    # PLMN is encoded in 3 bytes
                    plmn_bytes = pkt_body[pos:pos+3]
                    if len(plmn_bytes) >= 3:
                        # Decode MCC/MNC from PLMN
                        mcc_digit1 = plmn_bytes[0] & 0x0F
                        mcc_digit2 = (plmn_bytes[0] & 0xF0) >> 4
                        mcc_digit3 = plmn_bytes[1] & 0x0F
                        mnc_digit3 = (plmn_bytes[1] & 0xF0) >> 4
                        mnc_digit1 = plmn_bytes[2] & 0x0F
                        mnc_digit2 = (plmn_bytes[2] & 0xF0) >> 4
                        
                        mcc = mcc_digit1 * 100 + mcc_digit2 * 10 + mcc_digit3
                        if mnc_digit3 == 0xF:
                            mnc = mnc_digit1 * 10 + mnc_digit2
                        else:
                            mnc = mnc_digit3 * 100 + mnc_digit1 * 10 + mnc_digit2
                            
                        stdout += f"FPLMN {i}: MCC={mcc:03d}, MNC={mnc:02d}\n"
                        
                    pos += 3
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing UMTS NAS FPLMN List: {e}')
            return None

    def parse_umts_nas_reg_state(self, pkt_header, pkt_body, args):
        """Parse UMTS NAS_REG State (0x7132)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 4:
            return None
            
        try:
            # Parse basic fields
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x7132  UMTS NAS_REG State\n"
            stdout += f"Version = {version}\n"
            
            # Parse registration state data
            if len(pkt_body) >= 8:
                reg_state = pkt_body[1] if len(pkt_body) > 1 else 0
                reg_domain = pkt_body[2] if len(pkt_body) > 2 else 0
                
                # Registration state mapping
                reg_state_map = {
                    0: "Not Registered",
                    1: "Registered (Home Network)",
                    2: "Not Registered (Searching)",
                    3: "Registration Denied",
                    4: "Unknown",
                    5: "Registered (Roaming)"
                }
                
                reg_state_str = reg_state_map.get(reg_state, f"Unknown ({reg_state})")
                stdout += f"Registration State = {reg_state_str}\n"
                stdout += f"Registration Domain = {reg_domain}\n"
                
            if len(pkt_body) >= 12:
                lac = struct.unpack('<H', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                cell_id = struct.unpack('<H', pkt_body[6:8])[0] if len(pkt_body) >= 8 else 0
                
                stdout += f"Location Area Code = 0x{lac:04X}\n"
                stdout += f"Cell ID = 0x{cell_id:04X}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing UMTS NAS REG State: {e}')
            return None

    def parse_umts_nas_mm_state(self, pkt_header, pkt_body, args):
        """Parse UMTS NAS_MM State (0x7131)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 4:
            return None
            
        try:
            # Parse basic fields
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x7131  UMTS NAS_MM State\n"
            stdout += f"Version = {version}\n"
            
            # Parse MM state data
            if len(pkt_body) >= 8:
                mm_state = pkt_body[1] if len(pkt_body) > 1 else 0
                mm_substate = pkt_body[2] if len(pkt_body) > 2 else 0
                
                # MM state mapping
                mm_state_map = {
                    0: "MM_IDLE",
                    1: "MM_WAIT_FOR_OUTGOING_MM_CONNECTION",
                    2: "MM_CONNECTION_ACTIVE",
                    3: "MM_IMSI_DETACH_INITIATED",
                    4: "MM_PROCESS_CM_SERVICE_PROMPT",
                    5: "MM_WAIT_FOR_ADDITIONAL_OUTGOING_MM_CONNECTION",
                    6: "MM_WAIT_FOR_RR_CONNECTION_MM",
                    7: "MM_WAIT_FOR_NETWORK_COMMAND",
                    8: "MM_WAIT_FOR_RR_ACTIVE",
                    9: "MM_LOCATION_UPDATE_INITIATED",
                    10: "MM_LOCATION_UPDATE_REJECTED",
                    11: "MM_WAIT_FOR_RR_CONNECTION_LU",
                    12: "MM_WAIT_FOR_RR_CONNECTION_IMSI_DETACH"
                }
                
                mm_state_str = mm_state_map.get(mm_state, f"Unknown ({mm_state})")
                stdout += f"MM State = {mm_state_str}\n"
                stdout += f"MM Substate = {mm_substate}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing UMTS NAS MM State: {e}')
            return None

    def parse_umts_nas_gmm_state(self, pkt_header, pkt_body, args):
        """Parse UMTS NAS_GMM State (0x7130)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 4:
            return None
            
        try:
            # Parse basic fields
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x7130  UMTS NAS_GMM State\n"
            stdout += f"Version = {version}\n"
            
            # Parse GMM state data
            if len(pkt_body) >= 8:
                gmm_state = pkt_body[1] if len(pkt_body) > 1 else 0
                gmm_substate = pkt_body[2] if len(pkt_body) > 2 else 0
                
                # GMM state mapping
                gmm_state_map = {
                    0: "GMM_DEREGISTERED",
                    1: "GMM_REGISTERED_INITIATED",
                    2: "GMM_REGISTERED",
                    3: "GMM_DEREGISTERED_INITIATED",
                    4: "GMM_ROUTING_AREA_UPDATING_INITIATED",
                    5: "GMM_SERVICE_REQUEST_INITIATED",
                    6: "GMM_REGISTERED_NORMAL_SERVICE",
                    7: "GMM_REGISTERED_LIMITED_SERVICE",
                    8: "GMM_REGISTERED_UPDATE_NEEDED",
                    9: "GMM_REGISTERED_ATTEMPTING_TO_UPDATE",
                    10: "GMM_REGISTERED_IMSI_DETACH_INITIATED",
                    11: "GMM_REGISTERED_ATTEMPTING_TO_UPDATE_MM",
                    12: "GMM_REGISTERED_NO_CELL_AVAILABLE"
                }
                
                gmm_state_str = gmm_state_map.get(gmm_state, f"Unknown ({gmm_state})")
                stdout += f"GMM State = {gmm_state_str}\n"
                stdout += f"GMM Substate = {gmm_substate}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing UMTS NAS GMM State: {e}')
            return None