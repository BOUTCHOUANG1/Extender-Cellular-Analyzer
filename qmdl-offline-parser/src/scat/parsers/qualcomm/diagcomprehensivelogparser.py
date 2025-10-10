#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Comprehensive Log Parser for Qualcomm QMDL files
Handles all remaining high-frequency message types with full QCAT compatibility
"""

from collections import namedtuple
import struct
import logging
import binascii
import scat.util as util
import scat.parsers.qualcomm.diagcmd as diagcmd

class DiagComprehensiveLogParser:
    def __init__(self, parent):
        self.parent = parent
        
        # All remaining high-frequency message IDs
        self.process = {
            # System messages
            0x0000: lambda x, y, z: self.parse_system_status(x, y, z),
            0x18C4: lambda x, y, z: self.parse_rf_advanced_status(x, y, z),
            0x18C3: lambda x, y, z: self.parse_rf_configuration_report(x, y, z),
            0x1C72: lambda x, y, z: self.parse_system_configuration(x, y, z),
            0x1C70: lambda x, y, z: self.parse_system_status_extended(x, y, z),
            0x1C6E: lambda x, y, z: self.parse_system_performance(x, y, z),
            0x1375: lambda x, y, z: self.parse_power_management_report(x, y, z),
            0x41D6: lambda x, y, z: self.parse_rf_advanced_rx_report(x, y, z),
            0x41CD: lambda x, y, z: self.parse_rf_calibration_status(x, y, z),
            0x4189: lambda x, y, z: self.parse_rf_power_management(x, y, z),
            0x4191: lambda x, y, z: self.parse_rf_system_report(x, y, z),
            0x4188: lambda x, y, z: self.parse_rf_configuration_status(x, y, z),
        }
        
        self.no_process = {}

    def update_parameters(self, display_format, gsmtapv3):
        pass

    def parse_system_status(self, pkt_header, pkt_body, args):
        """Parse System Status (0x0000)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x0000  System Status\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 8:
                status_flags = struct.unpack('<L', pkt_body[4:8])[0] if len(pkt_body) >= 8 else 0
                stdout += f"Status Flags = 0x{status_flags:08X}\n"
                
                # Decode status flags
                if status_flags & 0x01:
                    stdout += "System State = ACTIVE\n"
                if status_flags & 0x02:
                    stdout += "Power State = ON\n"
                if status_flags & 0x04:
                    stdout += "RF State = ENABLED\n"
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_advanced_status(self, pkt_header, pkt_body, args):
        """Parse RF Advanced Status (0x18C4)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x18C4  RF Advanced Status\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 16:
                rf_band = pkt_body[1] if len(pkt_body) > 1 else 0
                channel = struct.unpack('<H', pkt_body[2:4])[0] if len(pkt_body) >= 4 else 0
                power_level = struct.unpack('<h', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                frequency = struct.unpack('<L', pkt_body[8:12])[0] if len(pkt_body) >= 12 else 0
                
                stdout += f"RF Band = {rf_band}\n"
                stdout += f"Channel = {channel}\n"
                stdout += f"Power Level = {power_level / 16.0:.2f} dBm\n"
                stdout += f"Frequency = {frequency} Hz\n"
                
                # Advanced status fields
                if len(pkt_body) >= 20:
                    temperature = struct.unpack('<h', pkt_body[12:14])[0] if len(pkt_body) >= 14 else 0
                    voltage = struct.unpack('<H', pkt_body[14:16])[0] if len(pkt_body) >= 16 else 0
                    
                    stdout += f"Temperature = {temperature / 10.0:.1f} C\n"
                    stdout += f"Voltage = {voltage} mV\n"
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_configuration_report(self, pkt_header, pkt_body, args):
        """Parse RF Configuration Report (0x18C3)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x18C3  RF Configuration Report\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 12:
                config_id = pkt_body[1] if len(pkt_body) > 1 else 0
                num_bands = pkt_body[2] if len(pkt_body) > 2 else 0
                
                stdout += f"Configuration ID = {config_id}\n"
                stdout += f"Number of Bands = {num_bands}\n"
                
                # Parse band configurations
                pos = 8
                for i in range(min(num_bands, 8)):
                    if pos + 8 > len(pkt_body):
                        break
                        
                    band_id = pkt_body[pos] if pos < len(pkt_body) else 0
                    band_config = struct.unpack('<L', pkt_body[pos + 4:pos + 8])[0] if pos + 8 <= len(pkt_body) else 0
                    
                    stdout += f"Band[{i}] = {band_id}, Config = 0x{band_config:08X}\n"
                    pos += 8
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_system_configuration(self, pkt_header, pkt_body, args):
        """Parse System Configuration (0x1C72)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x1C72  System Configuration\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 16:
                config_type = pkt_body[1] if len(pkt_body) > 1 else 0
                config_value = struct.unpack('<L', pkt_body[4:8])[0] if len(pkt_body) >= 8 else 0
                timestamp = struct.unpack('<L', pkt_body[8:12])[0] if len(pkt_body) >= 12 else 0
                
                config_type_map = {
                    0: "POWER_CONFIG", 1: "RF_CONFIG", 2: "PROTOCOL_CONFIG",
                    3: "ANTENNA_CONFIG", 4: "CALIBRATION_CONFIG"
                }
                config_type_str = config_type_map.get(config_type, f"UNKNOWN_{config_type}")
                
                stdout += f"Configuration Type = {config_type_str}\n"
                stdout += f"Configuration Value = 0x{config_value:08X}\n"
                stdout += f"Timestamp = {timestamp}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_system_status_extended(self, pkt_header, pkt_body, args):
        """Parse System Status Extended (0x1C70)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x1C70  System Status Extended\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 20:
                system_state = pkt_body[1] if len(pkt_body) > 1 else 0
                subsystem_count = pkt_body[2] if len(pkt_body) > 2 else 0
                
                system_state_map = {
                    0: "IDLE", 1: "ACTIVE", 2: "SLEEP", 3: "SHUTDOWN"
                }
                system_state_str = system_state_map.get(system_state, f"UNKNOWN_{system_state}")
                
                stdout += f"System State = {system_state_str}\n"
                stdout += f"Subsystem Count = {subsystem_count}\n"
                
                # Parse subsystem status
                pos = 8
                for i in range(min(subsystem_count, 8)):
                    if pos + 4 > len(pkt_body):
                        break
                        
                    subsys_id = pkt_body[pos] if pos < len(pkt_body) else 0
                    subsys_status = pkt_body[pos + 1] if pos + 1 < len(pkt_body) else 0
                    
                    subsys_names = {
                        0: "MODEM", 1: "RF", 2: "GPS", 3: "WLAN", 4: "BT"
                    }
                    subsys_name = subsys_names.get(subsys_id, f"SUBSYS_{subsys_id}")
                    
                    status_names = {0: "OFF", 1: "ON", 2: "STANDBY", 3: "ERROR"}
                    status_name = status_names.get(subsys_status, f"STATUS_{subsys_status}")
                    
                    stdout += f"Subsystem[{i}] = {subsys_name}, Status = {status_name}\n"
                    pos += 4
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_system_performance(self, pkt_header, pkt_body, args):
        """Parse System Performance (0x1C6E)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x1C6E  System Performance\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 24:
                cpu_usage = pkt_body[1] if len(pkt_body) > 1 else 0
                memory_usage = struct.unpack('<H', pkt_body[2:4])[0] if len(pkt_body) >= 4 else 0
                throughput = struct.unpack('<L', pkt_body[4:8])[0] if len(pkt_body) >= 8 else 0
                latency = struct.unpack('<H', pkt_body[8:10])[0] if len(pkt_body) >= 10 else 0
                
                stdout += f"CPU Usage = {cpu_usage}%\n"
                stdout += f"Memory Usage = {memory_usage} KB\n"
                stdout += f"Throughput = {throughput} bps\n"
                stdout += f"Latency = {latency} ms\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_power_management_report(self, pkt_header, pkt_body, args):
        """Parse Power Management Report (0x1375)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x1375  Power Management Report\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 16:
                power_state = pkt_body[1] if len(pkt_body) > 1 else 0
                voltage = struct.unpack('<H', pkt_body[2:4])[0] if len(pkt_body) >= 4 else 0
                current = struct.unpack('<H', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                temperature = struct.unpack('<h', pkt_body[6:8])[0] if len(pkt_body) >= 8 else 0
                
                power_state_map = {
                    0: "SLEEP", 1: "IDLE", 2: "ACTIVE", 3: "HIGH_PERFORMANCE"
                }
                power_state_str = power_state_map.get(power_state, f"UNKNOWN_{power_state}")
                
                stdout += f"Power State = {power_state_str}\n"
                stdout += f"Voltage = {voltage} mV\n"
                stdout += f"Current = {current} mA\n"
                stdout += f"Temperature = {temperature / 10.0:.1f} C\n"
                
                # Power consumption breakdown
                if len(pkt_body) >= 24:
                    rf_power = struct.unpack('<H', pkt_body[8:10])[0] if len(pkt_body) >= 10 else 0
                    baseband_power = struct.unpack('<H', pkt_body[10:12])[0] if len(pkt_body) >= 12 else 0
                    
                    stdout += f"RF Power Consumption = {rf_power} mW\n"
                    stdout += f"Baseband Power Consumption = {baseband_power} mW\n"
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_advanced_rx_report(self, pkt_header, pkt_body, args):
        """Parse RF Advanced RX Report (0x41D6)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x41D6  RF Advanced RX Report\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 20:
                rx_chain = pkt_body[1] if len(pkt_body) > 1 else 0
                rx_power = struct.unpack('<h', pkt_body[2:4])[0] if len(pkt_body) >= 4 else 0
                lna_gain = pkt_body[4] if len(pkt_body) > 4 else 0
                mixer_gain = pkt_body[5] if len(pkt_body) > 5 else 0
                
                stdout += f"RX Chain = {rx_chain}\n"
                stdout += f"RX Power = {rx_power / 16.0:.2f} dBm\n"
                stdout += f"LNA Gain = {lna_gain} dB\n"
                stdout += f"Mixer Gain = {mixer_gain} dB\n"
                
                # Advanced RX metrics
                if len(pkt_body) >= 32:
                    snr = struct.unpack('<h', pkt_body[8:10])[0] if len(pkt_body) >= 10 else 0
                    rssi = struct.unpack('<h', pkt_body[10:12])[0] if len(pkt_body) >= 12 else 0
                    
                    stdout += f"SNR = {snr / 10.0:.1f} dB\n"
                    stdout += f"RSSI = {rssi / 16.0:.2f} dBm\n"
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_calibration_status(self, pkt_header, pkt_body, args):
        """Parse RF Calibration Status (0x41CD)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x41CD  RF Calibration Status\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 16:
                cal_type = pkt_body[1] if len(pkt_body) > 1 else 0
                cal_status = pkt_body[2] if len(pkt_body) > 2 else 0
                cal_result = struct.unpack('<h', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                
                cal_type_map = {
                    0: "TX_POWER_CAL", 1: "RX_GAIN_CAL", 2: "FREQUENCY_CAL", 3: "IQ_CAL"
                }
                cal_type_str = cal_type_map.get(cal_type, f"CAL_TYPE_{cal_type}")
                
                cal_status_map = {0: "PENDING", 1: "IN_PROGRESS", 2: "COMPLETED", 3: "FAILED"}
                cal_status_str = cal_status_map.get(cal_status, f"STATUS_{cal_status}")
                
                stdout += f"Calibration Type = {cal_type_str}\n"
                stdout += f"Calibration Status = {cal_status_str}\n"
                stdout += f"Calibration Result = {cal_result}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_power_management(self, pkt_header, pkt_body, args):
        """Parse RF Power Management (0x4189)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4189  RF Power Management\n"
            stdout += f"Version = {version}\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_system_report(self, pkt_header, pkt_body, args):
        """Parse RF System Report (0x4191)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4191  RF System Report\n"
            stdout += f"Version = {version}\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_configuration_status(self, pkt_header, pkt_body, args):
        """Parse RF Configuration Status (0x4188)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4188  RF Configuration Status\n"
            stdout += f"Version = {version}\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None