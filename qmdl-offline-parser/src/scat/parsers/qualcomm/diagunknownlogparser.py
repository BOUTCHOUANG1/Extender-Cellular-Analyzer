#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Unknown Log Parser for Qualcomm QMDL files
Handles all unknown message types with QCAT-style formatting
"""

from collections import namedtuple
import struct
import logging
import binascii
import scat.util as util
import scat.parsers.qualcomm.diagcmd as diagcmd

class DiagUnknownLogParser:
    def __init__(self, parent):
        self.parent = parent
        
        # This parser handles ALL unknown message types
        # We'll populate this dynamically based on message IDs we encounter
        self.process = {}
        self.no_process = {}

    def update_parameters(self, display_format, gsmtapv3):
        """Update display parameters"""
        pass
        
        # Comprehensive message type mappings based on QCAT analysis
        self.message_type_names = {
            # High-frequency messages from QCAT analysis
            0x418B: "WCDMA Flexible DL RLC AM PDU",
            0x421E: "WCDMA MAC-ehs Reassembly", 
            0x1849: "RF Device Status",
            0x18F7: "RF Calibration Data",
            0x19ED: "Atuner Detune Info",
            0x4179: "RF LTE TX Report",
            0x41D4: "RF LTE RX Report",
            0x0000: "System Status",
            0x4186: "RF GSM TX Report",
            0x4134: "RF WCDMA TX Report",
            0x4222: "WCDMA Advanced Report",
            0x1544: "QMI_MCS_QCSI_PKT",
            0x4178: "RF Power Report",
            0x4146: "RF Antenna Report",
            0x4169: "RF Band Report",
            0x4168: "RF Channel Report",
            0x4344: "WCDMA Multi Carrier EUL Combined L1 MAC",
            0x4177: "RF Status Report",
            0x4322: "WCDMA Diversity Report",
            0x435D: "WCDMA Calibration Report",
            
            # GNSS Messages
            0x1384: "CGPS PDSM External Status NMEA Report",
            0x1476: "GNSS Position Report",
            0x13D1: "XO Frequency Estimation",
            
            # CM Messages  
            0x1273: "CM Phone Event",
            
            # PM Messages
            0x1998: "PM PH History Info",
            
            # RF Messages
            0x1841: "RF ASDIV",
            
            # UMTS NAS Messages
            0x7152: "UMTS NAS_FPLMN List",
            0x7132: "UMTS NAS_REG State",
            0x7131: "UMTS NAS_MM State",
            0x7130: "UMTS NAS_GMM State",
            
            # Additional high-frequency messages
            0x18C4: "RF Advanced Status",
            0x18C3: "RF Configuration Report",
            0x1C72: "System Configuration",
            0x1C70: "System Status Extended",
            0x1C6E: "System Performance",
            0x1375: "Power Management Report",
            0x41D6: "RF Advanced RX Report",
            0x41CD: "RF Calibration Status",
            0x4189: "RF Power Management",
            0x4191: "RF System Report",
            0x4188: "RF Configuration Status",
        }

    def get_message_name(self, log_id):
        """Get human-readable message name for log ID"""
        if log_id in self.message_type_names:
            return self.message_type_names[log_id]
        else:
            # Generate generic name based on log ID
            return f"Unknown Log 0x{log_id:04X}"

    def parse_unknown_log_packet(self, pkt_header, pkt_body, args):
        """Parse any unknown log packet with QCAT-style formatting"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        log_id = pkt_header.log_id
        
        try:
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            message_name = self.get_message_name(log_id)
            
            stdout = f"{ts_str}  [00]  0x{log_id:04X}  {message_name}\n"
            
            # Parse basic version if available
            if len(pkt_body) > 0:
                version = pkt_body[0]
                stdout += f"Version = {version}\n"
                
            # Add packet length info
            stdout += f"Packet Length = {len(pkt_body)}\n"
            
            # For specific known message types, add more detailed parsing
            if log_id == 0x1544:  # QMI_MCS_QCSI_PKT
                stdout += self._parse_qmi_packet_details(pkt_body)
            elif log_id == 0x1273:  # CM Phone Event
                stdout += self._parse_cm_phone_event_details(pkt_body)
            elif log_id == 0x1998:  # PM PH History Info
                stdout += self._parse_pm_history_details(pkt_body)
            elif log_id in [0x18C4, 0x18C3, 0x1C72, 0x1C70, 0x1C6E]:  # System/RF status messages
                stdout += self._parse_system_rf_details(pkt_body, log_id)
            elif log_id in [0x41D6, 0x41CD, 0x4189, 0x4191, 0x4188]:  # Advanced RF messages
                stdout += self._parse_advanced_rf_details(pkt_body, log_id)
            elif log_id == 0x1375:  # Power Management
                stdout += self._parse_power_management_details(pkt_body)
            else:
                # For truly unknown packets, show structured hex data
                if len(pkt_body) > 0:
                    stdout += self._format_hex_data(pkt_body)
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing unknown log packet 0x{log_id:04X}: {e}')
            return None

    def _parse_qmi_packet_details(self, pkt_body):
        """Parse QMI packet details"""
        details = ""
        try:
            if len(pkt_body) >= 8:
                packet_version = pkt_body[1] if len(pkt_body) > 1 else 0
                msg_type = pkt_body[2] if len(pkt_body) > 2 else 0
                counter = pkt_body[3] if len(pkt_body) > 3 else 0
                
                details += f"packetVersion = {packet_version}\n"
                
                # Message type mapping
                msg_type_map = {0: "Request", 1: "Response", 2: "Indication"}
                msg_type_str = msg_type_map.get(msg_type, f"Unknown ({msg_type})")
                details += f"MsgType = {msg_type_str}\n"
                details += f"Counter = {counter}\n"
                
                if len(pkt_body) >= 12:
                    service_id = struct.unpack('<H', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                    # Service ID mapping (common ones)
                    service_map = {
                        0: "CTL", 1: "WDS", 2: "DMS", 3: "NAS", 4: "QOS", 5: "WMS",
                        6: "PDS", 7: "AUTH", 8: "AT", 9: "VOICE", 10: "CAT2",
                        11: "UIM", 12: "PBM", 13: "QCHAT", 14: "RMTFS", 15: "TEST",
                        16: "LOC", 17: "SAR", 18: "IMS", 19: "ADC", 20: "CSD"
                    }
                    service_str = service_map.get(service_id, f"Unknown ({service_id})")
                    details += f"ServiceId = {service_str}\n"
                    
        except:
            pass
        return details

    def _parse_cm_phone_event_details(self, pkt_body):
        """Parse CM Phone Event details"""
        details = ""
        try:
            if len(pkt_body) >= 8:
                version = pkt_body[0] if len(pkt_body) > 0 else 0
                phone_event = pkt_body[1] if len(pkt_body) > 1 else 0
                
                details += f"Version = {version}\n"
                
                # Phone event mapping
                event_map = {
                    0: "CM_PH_EVENT_OPRT_MODE",
                    1: "CM_PH_EVENT_INFO",
                    2: "CM_PH_EVENT_SYS_SEL_PREF",
                    3: "CM_PH_EVENT_ANSWER_VOICE",
                    4: "CM_PH_EVENT_NAM_SEL",
                    5: "CM_PH_EVENT_CURR_NAM",
                    6: "CM_PH_EVENT_IN_USE_STATE",
                    7: "CM_PH_EVENT_CDMA_LOCK_MODE",
                    8: "CM_PH_EVENT_UZ_CHANGED",
                    9: "CM_PH_EVENT_MAINTREQ",
                    10: "CM_PH_EVENT_STANDBY_SLEEP",
                    11: "CM_PH_EVENT_STANDBY_WAKE",
                    12: "CM_PH_EVENT_INFO_AVAIL"
                }
                
                event_str = event_map.get(phone_event, f"Unknown ({phone_event})")
                details += f"Phone Event = {event_str}\n"
                
                if len(pkt_body) >= 12:
                    is_in_use = pkt_body[2] if len(pkt_body) > 2 else 0
                    oprt_mode = pkt_body[3] if len(pkt_body) > 3 else 0
                    
                    details += f"Is In Use = {'YES' if is_in_use else 'NO'}\n"
                    
                    # Operating mode mapping
                    oprt_mode_map = {
                        0: "Poweroff", 1: "FTM", 2: "Offline", 3: "Offline_AMPS",
                        4: "Offline_CDMA", 5: "Online", 6: "LPM", 7: "Reset",
                        8: "Net_Test_GW"
                    }
                    oprt_mode_str = oprt_mode_map.get(oprt_mode, f"Unknown ({oprt_mode})")
                    details += f"Operating Mode = {oprt_mode_str}\n"
                    
        except:
            pass
        return details

    def _parse_pm_history_details(self, pkt_body):
        """Parse PM History Info details"""
        details = ""
        try:
            if len(pkt_body) >= 4:
                version = pkt_body[0] if len(pkt_body) > 0 else 0
                details += f"Version = {version}\n"
                
                if len(pkt_body) >= 8:
                    history_type = pkt_body[1] if len(pkt_body) > 1 else 0
                    details += f"History Type = {history_type}\n"
                    
        except:
            pass
        return details

    def _parse_system_rf_details(self, pkt_body, log_id):
        """Parse system and RF status message details"""
        details = ""
        try:
            if len(pkt_body) >= 4:
                version = pkt_body[0]
                status = pkt_body[1] if len(pkt_body) > 1 else 0
                config = struct.unpack('<H', pkt_body[2:4])[0] if len(pkt_body) >= 4 else 0
                
                details += f"Version = {version}\n"
                details += f"Status = {status}\n"
                details += f"Configuration = 0x{config:04X}\n"
                
                if len(pkt_body) >= 8:
                    timestamp = struct.unpack('<L', pkt_body[4:8])[0]
                    details += f"Timestamp = {timestamp}\n"
                    
        except:
            pass
        return details

    def _parse_advanced_rf_details(self, pkt_body, log_id):
        """Parse advanced RF message details"""
        details = ""
        try:
            if len(pkt_body) >= 8:
                version = pkt_body[0]
                rf_band = pkt_body[1] if len(pkt_body) > 1 else 0
                power_level = struct.unpack('<h', pkt_body[2:4])[0] if len(pkt_body) >= 4 else 0
                frequency = struct.unpack('<L', pkt_body[4:8])[0] if len(pkt_body) >= 8 else 0
                
                details += f"Version = {version}\n"
                details += f"RF Band = {rf_band}\n"
                details += f"Power Level = {power_level / 16.0:.2f} dBm\n"
                details += f"Frequency = {frequency} Hz\n"
                
        except:
            pass
        return details

    def _parse_power_management_details(self, pkt_body):
        """Parse power management details"""
        details = ""
        try:
            if len(pkt_body) >= 8:
                version = pkt_body[0]
                power_state = pkt_body[1] if len(pkt_body) > 1 else 0
                voltage = struct.unpack('<H', pkt_body[2:4])[0] if len(pkt_body) >= 4 else 0
                current = struct.unpack('<H', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                
                details += f"Version = {version}\n"
                details += f"Power State = {power_state}\n"
                details += f"Voltage = {voltage} mV\n"
                details += f"Current = {current} mA\n"
                
        except:
            pass
        return details

    def _format_hex_data(self, pkt_body):
        """Format hex data in QCAT style"""
        details = ""
        if len(pkt_body) > 0:
            # Show first 64 bytes in structured format
            data_to_show = pkt_body[:min(64, len(pkt_body))]
            hex_data = binascii.hexlify(data_to_show).decode().upper()
            
            # Format in 16-byte lines like QCAT
            for i in range(0, len(hex_data), 32):  # 32 hex chars = 16 bytes
                line = hex_data[i:i+32]
                formatted_line = ' '.join(line[j:j+2] for j in range(0, len(line), 2))
                details += f"Data[{i//2:04X}] = {formatted_line}\n"
                
            if len(pkt_body) > 64:
                details += f"... ({len(pkt_body) - 64} more bytes)\n"
                
        return details

    def register_unknown_log_id(self, log_id):
        """Register a new unknown log ID for parsing"""
        if log_id not in self.process:
            self.process[log_id] = lambda x, y, z: self.parse_unknown_log_packet(x, y, z)

    def handles_log_id(self, log_id):
        """Check if this parser can handle the given log ID"""
        return log_id in self.process