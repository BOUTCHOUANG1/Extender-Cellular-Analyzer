#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

"""
RF Log Parser for Qualcomm QMDL files
Handles RF ASDIV, Atuner Detune Info, and other RF-related messages
"""

from collections import namedtuple
import struct
import logging
import binascii
import scat.util as util
import scat.parsers.qualcomm.diagcmd as diagcmd

class DiagRfLogParser:
    def __init__(self, parent):
        self.parent = parent
        
        # RF message IDs from QCAT output analysis
        self.process = {
            0x1841: lambda x, y, z: self.parse_rf_asdiv(x, y, z),
            0x19ED: lambda x, y, z: self.parse_atuner_detune_info(x, y, z),
            0x1849: lambda x, y, z: self.parse_rf_device_status(x, y, z),
            0x18F7: lambda x, y, z: self.parse_rf_calibration_data(x, y, z),
            0x4179: lambda x, y, z: self.parse_rf_lte_tx_report(x, y, z),
            0x41D4: lambda x, y, z: self.parse_rf_lte_rx_report(x, y, z),
            0x4186: lambda x, y, z: self.parse_rf_gsm_tx_report(x, y, z),
            0x4134: lambda x, y, z: self.parse_rf_wcdma_tx_report(x, y, z),
            0x4178: lambda x, y, z: self.parse_rf_power_report(x, y, z),
            0x4146: lambda x, y, z: self.parse_rf_antenna_report(x, y, z),
        }
        
        self.no_process = {}

    def update_parameters(self, display_format, gsmtapv3):
        """Update display parameters"""
        pass

    def parse_rf_asdiv(self, pkt_header, pkt_body, args):
        """Parse RF ASDIV (0x1841)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 4:
            return None
            
        try:
            # Parse basic fields
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x1841  RF ASDIV\n"
            stdout += f"Version = {version}\n"
            
            # Parse ASDIV specific data
            if len(pkt_body) >= 8:
                asdiv_state = pkt_body[1] if len(pkt_body) > 1 else 0
                antenna_selection = pkt_body[2] if len(pkt_body) > 2 else 0
                switch_count = pkt_body[3] if len(pkt_body) > 3 else 0
                
                stdout += f"ASDIV State = {asdiv_state}\n"
                stdout += f"Antenna Selection = {antenna_selection}\n"
                stdout += f"Switch Count = {switch_count}\n"
                
            if len(pkt_body) >= 12:
                rssi_ant0 = struct.unpack('<h', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                rssi_ant1 = struct.unpack('<h', pkt_body[6:8])[0] if len(pkt_body) >= 8 else 0
                stdout += f"RSSI Antenna 0 = {rssi_ant0 / 16.0:.2f} dBm\n"
                stdout += f"RSSI Antenna 1 = {rssi_ant1 / 16.0:.2f} dBm\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing RF ASDIV: {e}')
            return None

    def parse_atuner_detune_info(self, pkt_header, pkt_body, args):
        """Parse Atuner Detune Info (0x19ED) - Full QCAT compatibility"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 8:
            return None
            
        try:
            # Parse header
            version = pkt_body[0]
            num_antennas = pkt_body[1] if len(pkt_body) > 1 else 0
            tuner_state = pkt_body[2] if len(pkt_body) > 2 else 0
            
            # Format output exactly like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [FE]  0x19ED  Atuner Detune Info\n"
            stdout += f"Version = {version}\n"
            stdout += f"Num Antennas = {num_antennas}\n"
            
            # Tuner system state mapping
            tuner_state_map = {0: "OFF_STATE", 1: "ON_STATE", 2: "IDLE_STATE"}
            tuner_state_str = tuner_state_map.get(tuner_state, f"UNKNOWN_STATE_{tuner_state}")
            stdout += f"Tuner System State = {tuner_state_str}\n"
            
            # Parse antenna data table
            stdout += f"Antenna Data\n"
            stdout += f"   ------------------------------------------------------------------------------------------------\n"
            stdout += f"   |   |       |        |        |Carrier Info                                                    |\n"
            stdout += f"   |   |Antenna|        |Num     |   |               |        |Device  |               |Channel   |\n"
            stdout += f"   |#  |Number |RFM Mode|Carriers|#  |Carrier Id     |Band    |Type    |RFM Device     |Number    |\n"
            stdout += f"   ------------------------------------------------------------------------------------------------\n"
            
            # Parse antenna entries
            pos = 8
            for i in range(min(num_antennas, 16)):  # Limit to prevent excessive parsing
                if pos + 20 > len(pkt_body):
                    break
                    
                try:
                    antenna_num = pkt_body[pos] if pos < len(pkt_body) else 0
                    rfm_mode = pkt_body[pos + 1] if pos + 1 < len(pkt_body) else 0
                    num_carriers = pkt_body[pos + 2] if pos + 2 < len(pkt_body) else 0
                    
                    if antenna_num == 0xFF:
                        antenna_str = "INVALID"
                    else:
                        antenna_str = f"{antenna_num:7d}"
                        
                    # RFM Mode mapping
                    rfm_mode_map = {
                        0: "LTE", 1: "WCDMA", 2: "GSM", 3: "CDMA", 4: "TDSCDMA",
                        5: "GPS", 6: "WIFI", 7: "BT", 20: "20", 97: "97"
                    }
                    rfm_mode_str = rfm_mode_map.get(rfm_mode, f"{rfm_mode:8d}")
                    
                    if num_carriers > 0 and pos + 16 < len(pkt_body):
                        carrier_id = pkt_body[pos + 4] if pos + 4 < len(pkt_body) else 0
                        band = pkt_body[pos + 5] if pos + 5 < len(pkt_body) else 0
                        device_type = pkt_body[pos + 6] if pos + 6 < len(pkt_body) else 0
                        rfm_device = pkt_body[pos + 7] if pos + 7 < len(pkt_body) else 0
                        channel_num = struct.unpack('<L', pkt_body[pos + 8:pos + 12])[0] if pos + 12 <= len(pkt_body) else 0
                        
                        carrier_id_str = f"CARRIER_ID_{carrier_id}"
                        device_type_map = {0: "PRX", 1: "DRX", 2: "TX"}
                        device_type_str = device_type_map.get(device_type, f"TYPE_{device_type}")
                        rfm_device_str = f"DEVICE_{rfm_device}"
                        
                        stdout += f"   |{i:3d}|{antenna_str}|{rfm_mode_str:8s}|{num_carriers:8d}|{0:3d}|{carrier_id_str:15s}|{band:8d}|{device_type_str:8s}|{rfm_device_str:15s}|{channel_num:10d}|\n"
                    else:
                        stdout += f"   |{i:3d}|{antenna_str}|{rfm_mode_str:8s}|{num_carriers:8d}|   |               |        |        |               |          |\n"
                        
                    pos += 20
                except:
                    break
                    
            # Parse system data table
            stdout += f"\nSystem Data\n"
            stdout += f"   -------------------------------------------------------------------------\n"
            stdout += f"   |   |            |Num     |PCC Band    |        |           |           |\n"
            stdout += f"   |#  |RFM Mode    |Carriers|Index       |Band    |RX Channels|TX Channels|\n"
            stdout += f"   -------------------------------------------------------------------------\n"
            
            # Parse system data entries (simplified)
            if pos + 32 < len(pkt_body):
                try:
                    rfm_mode_sys = pkt_body[pos] if pos < len(pkt_body) else 0
                    num_carriers_sys = pkt_body[pos + 1] if pos + 1 < len(pkt_body) else 0
                    pcc_band_idx = pkt_body[pos + 2] if pos + 2 < len(pkt_body) else 0
                    band_sys = pkt_body[pos + 3] if pos + 3 < len(pkt_body) else 0
                    rx_channels = struct.unpack('<L', pkt_body[pos + 4:pos + 8])[0] if pos + 8 <= len(pkt_body) else 0
                    tx_channels = struct.unpack('<L', pkt_body[pos + 8:pos + 12])[0] if pos + 12 <= len(pkt_body) else 0
                    
                    stdout += f"   |{0:3d}|{rfm_mode_sys:12d}|{num_carriers_sys:8d}|{pcc_band_idx:12d}|{band_sys:8d}|{rx_channels:11d}|{tx_channels:11d}|\n"
                    
                    # Additional band entries
                    for j in range(1, 6):
                        if pos + 12 + j * 4 < len(pkt_body):
                            band_extra = struct.unpack('<L', pkt_body[pos + 12 + j * 4:pos + 16 + j * 4])[0] if pos + 16 + j * 4 <= len(pkt_body) else 0
                            if band_extra != 0:
                                stdout += f"   |   |            |        |            |{band_extra:8d}|{0:11d}|{0:11d}|\n"
                except:
                    pass
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing Atuner Detune Info: {e}')
            return None

    def parse_rf_device_status(self, pkt_header, pkt_body, args):
        """Parse RF Device Status (0x1849)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x1849  RF Device Status\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 8:
                device_id = pkt_body[1] if len(pkt_body) > 1 else 0
                status = pkt_body[2] if len(pkt_body) > 2 else 0
                
                stdout += f"Device ID = {device_id}\n"
                stdout += f"Status = {status}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing RF Device Status: {e}')
            return None

    def parse_rf_calibration_data(self, pkt_header, pkt_body, args):
        """Parse RF Calibration Data (0x18F7)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x18F7  RF Calibration Data\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 8:
                cal_type = pkt_body[1] if len(pkt_body) > 1 else 0
                band = pkt_body[2] if len(pkt_body) > 2 else 0
                
                stdout += f"Calibration Type = {cal_type}\n"
                stdout += f"Band = {band}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing RF Calibration Data: {e}')
            return None

    def parse_rf_lte_tx_report(self, pkt_header, pkt_body, args):
        """Parse RF LTE TX Report (0x4179)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4179  RF LTE TX Report\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 12:
                tx_power = struct.unpack('<h', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                pa_state = pkt_body[6] if len(pkt_body) > 6 else 0
                
                stdout += f"TX Power = {tx_power / 16.0:.2f} dBm\n"
                stdout += f"PA State = {pa_state}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing RF LTE TX Report: {e}')
            return None

    def parse_rf_lte_rx_report(self, pkt_header, pkt_body, args):
        """Parse RF LTE RX Report (0x41D4)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x41D4  RF LTE RX Report\n"
            stdout += f"Version = {version}\n"
            
            if len(pkt_body) >= 12:
                rx_power = struct.unpack('<h', pkt_body[4:6])[0] if len(pkt_body) >= 6 else 0
                lna_state = pkt_body[6] if len(pkt_body) > 6 else 0
                
                stdout += f"RX Power = {rx_power / 16.0:.2f} dBm\n"
                stdout += f"LNA State = {lna_state}\n"
                
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing RF LTE RX Report: {e}')
            return None

    def parse_rf_gsm_tx_report(self, pkt_header, pkt_body, args):
        """Parse RF GSM TX Report (0x4186)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4186  RF GSM TX Report\n"
            stdout += f"Version = {version}\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_wcdma_tx_report(self, pkt_header, pkt_body, args):
        """Parse RF WCDMA TX Report (0x4134)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4134  RF WCDMA TX Report\n"
            stdout += f"Version = {version}\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_power_report(self, pkt_header, pkt_body, args):
        """Parse RF Power Report (0x4178)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4178  RF Power Report\n"
            stdout += f"Version = {version}\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None

    def parse_rf_antenna_report(self, pkt_header, pkt_body, args):
        """Parse RF Antenna Report (0x4146)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        try:
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x4146  RF Antenna Report\n"
            stdout += f"Version = {version}\n"
            
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            return None