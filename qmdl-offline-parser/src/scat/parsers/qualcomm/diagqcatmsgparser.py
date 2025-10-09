#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later
"""
DiagQCATMsgParser Module

Provides parsing for RUIM Debug, QMI, and CM messages to match QCAT TXT output format.
Extracts and formats these messages for comprehensive text-based analysis.
"""

import struct
import binascii
import logging
from collections import namedtuple
import scat.util as util
import scat.parsers.qualcomm.diagcmd as diagcmd


class DiagQCATMsgParser:
    """Parser for RUIM, QMI, and CM messages to match QCAT output format"""
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger('scat.diagqcatmsgparser')
        
        # Map log IDs to parsers
        self.process = {
            0x1098: lambda x, y, z: self.parse_ruim_debug(x, y, z),
            0x1544: lambda x, y, z: self.parse_qmi_message(x, y, z),
            0x1273: lambda x, y, z: self.parse_cm_phone_event(x, y, z),
            0x199B: lambda x, y, z: self.parse_pm_policy_stats(x, y, z),
        }
    
    def update_parameters(self, display_format, gsmtapv3):
        """Update parameters (required by parent parser)"""
        pass
    
    def parse_ruim_debug(self, pkt_header, pkt_body, args):
        """Parse RUIM Debug messages (APDU commands)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 2:
            return None
        
        direction = pkt_body[0]
        data = pkt_body[1:]
        
        result = {
            'type': 'ruim_debug',
            'direction': 'TX' if direction == 0 else 'RX',
            'data': binascii.hexlify(data).decode().upper(),
            'timestamp': pkt_ts
        }
        
        # Parse TX APDU command
        if direction == 0 and len(data) >= 5:
            cla, ins, p1, p2, p3 = data[0], data[1], data[2], data[3], data[4]
            result['cla'] = cla
            result['ins'] = ins
            result['p1'] = p1
            result['p2'] = p2
            result['p3'] = p3
            result['command'] = self._get_apdu_command(ins)
            result['slot'] = 1
            result['channel'] = cla & 0x03
            result['sm_used'] = 'No SM used' if (cla & 0x0C) == 0 else 'SM used'
        
        # Parse RX APDU response
        if direction == 1 and len(data) >= 2:
            sw1, sw2 = data[-2], data[-1]
            result['sw1'] = sw1
            result['sw2'] = sw2
            result['status'] = self._parse_status_words(sw1, sw2)
            result['slot'] = 1
            if len(data) > 2:
                result['response_data'] = binascii.hexlify(data[:-2]).decode().upper()
        
        return {'qcat_msg': result, 'ts': pkt_ts}
    
    def parse_qmi_message(self, pkt_header, pkt_body, args):
        """Parse QMI messages with TLV decoding"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 12:
            return None
        
        version = pkt_body[0]
        msg_type = pkt_body[1]
        counter = struct.unpack('<H', pkt_body[2:4])[0]
        service_id = pkt_body[4]
        major_rev = pkt_body[5]
        minor_rev = pkt_body[6]
        con_handle = struct.unpack('<I', pkt_body[7:11])[0] if len(pkt_body) >= 11 else 0
        msg_id = struct.unpack('<H', pkt_body[11:13])[0] if len(pkt_body) >= 13 else 0
        qmi_len = struct.unpack('<H', pkt_body[13:15])[0] if len(pkt_body) >= 15 else 0
        
        service_names = {1: 'CTL', 2: 'WDS', 3: 'DMS', 4: 'NAS', 5: 'QOS', 6: 'WMS', 
                        7: 'PDS', 8: 'AUTH', 9: 'AT', 10: 'VOICE', 11: 'CAT2', 
                        12: 'UIM', 13: 'PBM', 14: 'QCHAT', 15: 'RMTFS', 16: 'TEST',
                        17: 'LOC', 18: 'SAR', 19: 'IMSS', 20: 'ADC', 21: 'MFS'}
        
        result = {
            'type': 'qmi_message',
            'version': version,
            'msg_type': 'Request' if msg_type == 0 else 'Response' if msg_type == 2 else 'Indication',
            'counter': counter,
            'service_id': service_id,
            'service_name': service_names.get(service_id, f'Unknown({service_id})'),
            'major_rev': major_rev,
            'minor_rev': minor_rev,
            'con_handle': con_handle,
            'msg_id': msg_id,
            'qmi_length': qmi_len,
            'timestamp': pkt_ts,
            'tlvs': []
        }
        
        # Parse TLVs
        if len(pkt_body) > 15:
            tlv_data = pkt_body[15:]
            pos = 0
            while pos + 3 <= len(tlv_data):
                tlv_type = tlv_data[pos]
                tlv_len = struct.unpack('<H', tlv_data[pos+1:pos+3])[0]
                if pos + 3 + tlv_len <= len(tlv_data):
                    tlv_value = tlv_data[pos+3:pos+3+tlv_len]
                    result['tlvs'].append({
                        'type': tlv_type,
                        'length': tlv_len,
                        'value': binascii.hexlify(tlv_value).decode().upper()
                    })
                    pos += 3 + tlv_len
                else:
                    break
        
        return {'qcat_msg': result, 'ts': pkt_ts}
    
    def parse_cm_phone_event(self, pkt_header, pkt_body, args):
        """Parse CM Phone Event messages with detailed field extraction"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 4:
            return None
        
        version = pkt_body[0]
        event_type = struct.unpack('<H', pkt_body[1:3])[0]
        
        event_names = {
            0: 'CM_PH_EVENT_OPRT_MODE',
            1: 'CM_PH_EVENT_TEST_CONTROL_TYPE',
            2: 'CM_PH_EVENT_SYS_SEL_PREF',
            3: 'CM_PH_EVENT_ANSWER_VOICE',
            4: 'CM_PH_EVENT_NAM_SEL',
            5: 'CM_PH_EVENT_CURR_NAM',
            6: 'CM_PH_EVENT_IN_USE_STATE',
            7: 'CM_PH_EVENT_CDMA_LOCK_MODE',
            8: 'CM_PH_EVENT_UIM_NOT_AVAILABLE',
            9: 'CM_PH_EVENT_SUBSCRIPTION_AVAILABLE',
            10: 'CM_PH_EVENT_SUBSCRIPTION_NOT_AVAILABLE',
            11: 'CM_PH_EVENT_SUBSCRIPTION_CHANGED',
            12: 'CM_PH_EVENT_AVAILABLE_NETWORKS_CONF',
            13: 'CM_PH_EVENT_PREFERRED_NETWORKS_CONF',
            14: 'CM_PH_EVENT_FUNDS_LOW',
            15: 'CM_PH_EVENT_WAKEUP_FROM_STANDBY',
            16: 'CM_PH_EVENT_NVRUIM_CONFIG_CHANGED',
            17: 'CM_PH_EVENT_PREFERRED_NETWORKS',
            18: 'CM_PH_EVENT_PS_ATTACH_FAILED',
            19: 'CM_PH_EVENT_RESET_ACM_COMPLETED',
            20: 'CM_PH_EVENT_DDTM_STATUS'
        }
        
        result = {
            'type': 'cm_phone_event',
            'version': version,
            'event_type': event_type,
            'event_name': event_names.get(event_type, f'Unknown({event_type})'),
            'timestamp': pkt_ts,
            'fields': {}
        }
        
        # Parse common fields if available
        if len(pkt_body) >= 10:
            result['fields']['is_in_use'] = 'YES' if pkt_body[3] else 'NO'
            oprt_mode = pkt_body[4]
            oprt_modes = {0: 'Poweroff', 1: 'FTM', 2: 'Offline', 3: 'Offline AMPS', 
                         4: 'Offline CDMA', 5: 'Online', 6: 'Low power mode', 7: 'Reset'}
            result['fields']['operating_mode'] = oprt_modes.get(oprt_mode, f'Unknown({oprt_mode})')
        
        return {'qcat_msg': result, 'ts': pkt_ts}
    
    def parse_pm_policy_stats(self, pkt_header, pkt_body, args):
        """Parse PM Policy Stats Info messages"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 20:
            return None
        
        version = pkt_body[0]
        policy_num = struct.unpack('<H', pkt_body[1:3])[0] if len(pkt_body) >= 3 else 0
        policy_type = pkt_body[3] if len(pkt_body) >= 4 else 0
        policy_version = pkt_body[4] if len(pkt_body) >= 5 else 0
        last_exec_time = struct.unpack('<I', pkt_body[5:9])[0] if len(pkt_body) >= 9 else 0
        elapsed_time = struct.unpack('<I', pkt_body[9:13])[0] if len(pkt_body) >= 13 else 0
        num_rules = struct.unpack('<H', pkt_body[13:15])[0] if len(pkt_body) >= 15 else 0
        suspend_count = struct.unpack('<H', pkt_body[15:17])[0] if len(pkt_body) >= 17 else 0
        is_policy_init = pkt_body[17] if len(pkt_body) >= 18 else 0
        
        result = {
            'type': 'pm_policy_stats',
            'version': version,
            'policy_num': policy_num,
            'policy_type': policy_type,
            'policy_version': policy_version,
            'last_exec_time': last_exec_time,
            'elapsed_time': elapsed_time,
            'num_rules': num_rules,
            'suspend_count': suspend_count,
            'is_policy_init': 'true' if is_policy_init else 'false',
            'timestamp': pkt_ts
        }
        
        return {'qcat_msg': result, 'ts': pkt_ts}
    
    def _get_apdu_command(self, ins):
        """Get APDU command name from instruction byte"""
        commands = {
            0xF2: 'STATUS',
            0xA4: 'SELECT',
            0xB0: 'READ BINARY',
            0xB2: 'READ RECORD',
            0xD6: 'UPDATE BINARY',
            0xDC: 'UPDATE RECORD',
            0x88: 'AUTHENTICATE',
            0x20: 'VERIFY',
            0x84: 'GET CHALLENGE',
            0xC0: 'GET RESPONSE',
        }
        return commands.get(ins, f'UNKNOWN (0x{ins:02X})')
    
    def _parse_status_words(self, sw1, sw2):
        """Parse APDU status words"""
        if sw1 == 0x90 and sw2 == 0x00:
            return "Normal ending of the command"
        elif sw1 == 0x91:
            return f"Normal ending with extra info (0x{sw2:02X})"
        elif sw1 == 0x92:
            return f"Command successful with warning (0x{sw2:02X})"
        elif sw1 == 0x93:
            return f"Command successful but after retry (0x{sw2:02X})"
        elif sw1 == 0x94:
            return f"Error, no precise diagnosis (0x{sw2:02X})"
        elif sw1 == 0x98:
            return f"Security error (0x{sw2:02X})"
        elif sw1 == 0x6A:
            return f"Wrong parameter(s) P1-P2 (0x{sw2:02X})"
        elif sw1 == 0x6B:
            return "Wrong parameter(s) P1-P2"
        elif sw1 == 0x6D:
            return "Instruction code not supported"
        elif sw1 == 0x6E:
            return "Class not supported"
        elif sw1 == 0x6F:
            return "Technical problem, no precise diagnosis"
        else:
            return f"Unknown status (0x{sw1:02X} 0x{sw2:02X})"
