#!/usr/bin/env python3
# coding: utf8
# SPDX-License-Identifier: GPL-2.0-or-later

"""
GNSS/GPS Log Parser for Qualcomm QMDL files
Handles GNSS Position Reports, NMEA messages, and frequency estimation
"""

from collections import namedtuple
import struct
import logging
import binascii
import scat.util as util
import scat.parsers.qualcomm.diagcmd as diagcmd

class DiagGnssLogParser:
    def __init__(self, parent):
        self.parent = parent
        
        # GNSS message IDs from QCAT output analysis
        self.process = {
            0x1384: lambda x, y, z: self.parse_cgps_pdsm_nmea_report(x, y, z),
            0x1476: lambda x, y, z: self.parse_gnss_position_report(x, y, z),
            0x13D1: lambda x, y, z: self.parse_xo_frequency_estimation(x, y, z),
            0x418B: lambda x, y, z: self.parse_gnss_measurement_report(x, y, z),
        }
        
        self.no_process = {}

    def update_parameters(self, display_format, gsmtapv3):
        """Update display parameters"""
        pass

    def parse_cgps_pdsm_nmea_report(self, pkt_header, pkt_body, args):
        """Parse CGPS PDSM External Status NMEA Report (0x1384)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 8:
            return None
            
        try:
            # Parse header
            version, client_id = struct.unpack('<BL', pkt_body[0:5])
            nmea_sentence_type = struct.unpack('<L', pkt_body[5:9])[0]
            nmea_sentence_length = pkt_body[9]
            
            # Extract NMEA sentence data
            nmea_data = b''
            if len(pkt_body) > 10 and nmea_sentence_length > 0:
                end_pos = min(10 + nmea_sentence_length, len(pkt_body))
                nmea_data = pkt_body[10:end_pos]
                
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [D5]  0x1384  CGPS PDSM External Status NMEA Report\n"
            stdout += f"Version = {version}\n"
            stdout += f"Client ID = {client_id}\n"
            stdout += f"NMEA Sentence Type = {nmea_sentence_type}\n"
            stdout += f"NMEA Sentence Length = {nmea_sentence_length}\n"
            
            if nmea_data:
                try:
                    nmea_str = nmea_data.decode('ascii', errors='ignore').strip()
                    stdout += f"NMEA Sentence Data = {nmea_str}\n"
                except:
                    stdout += f"NMEA Sentence Data = {binascii.hexlify(nmea_data).decode()}\n"
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing CGPS PDSM NMEA Report: {e}')
            return None

    def parse_gnss_position_report(self, pkt_header, pkt_body, args):
        """Parse GNSS Position Report (0x1476) - Full QCAT compatibility"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 20:
            return None
            
        try:
            # Parse exact QCAT structure
            version = pkt_body[0]
            f_count = pkt_body[1]
            pos_source = pkt_body[2] if len(pkt_body) > 2 else 0
            
            # Format output exactly like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [61]  0x1476  GNSS Position Report\n"
            stdout += f"Version = {version}\n"
            stdout += f"F Count = {f_count}\n"
            
            # Position source mapping
            pos_source_map = {0: "Internal Database", 1: "Network", 2: "Sensor"}
            pos_source_str = pos_source_map.get(pos_source, f"Unknown ({pos_source})")
            stdout += f"Position Source = {pos_source_str}\n"
            
            # Parse PosVelFlag_IntDB
            if len(pkt_body) >= 8:
                pos_vel_flag = struct.unpack('<L', pkt_body[4:8])[0]
                stdout += f"PosVelFlag_IntDB {{\n"
                stdout += f"   Pos Vel Flag = {pos_vel_flag & 0xFFFF}\n"
                stdout += f"   Raw Value = 0x{pos_vel_flag:04X}\n"
                stdout += f"}}\n"
                
            # Parse PosVelFlag2_IntDB
            if len(pkt_body) >= 16:
                pos_vel_flag2 = struct.unpack('<Q', pkt_body[8:16])[0]
                stdout += f"PosVelFlag2_IntDB {{\n"
                stdout += f"   Pos Vel Flag = 0x{pos_vel_flag2 & 0xFFFFFFFF:X}\n"
                stdout += f"   Raw Value = 0x{pos_vel_flag2:016X}\n"
                stdout += f"}}\n"
                
            # Parse PosVelFlag3_IntDB
            if len(pkt_body) >= 24:
                pos_vel_flag3 = struct.unpack('<Q', pkt_body[16:24])[0]
                stdout += f"PosVelFlag3_IntDB {{\n"
                stdout += f"   Pos Vel Flag = {pos_vel_flag3 & 0xFFFFFFFF}\n"
                stdout += f"   Raw Value = 0x{pos_vel_flag3:016X}\n"
                stdout += f"}}\n"
                
            # Parse u_FixMode and Failure Code
            if len(pkt_body) >= 26:
                fix_mode = pkt_body[24] if len(pkt_body) > 24 else 0
                failure_code = pkt_body[25] if len(pkt_body) > 25 else 0
                stdout += f"u_FixMode = {fix_mode}\n"
                stdout += f"Failure Code = {failure_code}\n"
                
            # Parse Fix Events
            if len(pkt_body) >= 28:
                fix_events = struct.unpack('<H', pkt_body[26:28])[0]
                stdout += f"Fix Events {{\n"
                stdout += f"   Fix Events = {fix_events}\n"
                stdout += f"   Raw Value = 0x{fix_events:04X}\n"
                stdout += f"}}\n"
                
            # Parse GPS time
            if len(pkt_body) >= 34:
                gps_week = struct.unpack('<H', pkt_body[28:30])[0]
                gps_ms = struct.unpack('<L', pkt_body[30:34])[0]
                stdout += f"GPS Week Number = {gps_week}\n"
                stdout += f"GPS Milliseconds = {gps_ms}\n"
                
            # Parse GLONASS time
            if len(pkt_body) >= 42:
                glonass_cycle = struct.unpack('<H', pkt_body[34:36])[0]
                glonass_days = struct.unpack('<H', pkt_body[36:38])[0]
                glonass_ms = struct.unpack('<L', pkt_body[38:42])[0]
                stdout += f"GLONASS Cycle Number 4 Years = {glonass_cycle}\n"
                stdout += f"GLONASS Number Of Days In 4 Year = {glonass_days}\n"
                stdout += f"GLONASS Milliseconds = {glonass_ms}\n"
                
            # Parse Number of Positions
            if len(pkt_body) >= 44:
                num_positions = struct.unpack('<H', pkt_body[42:44])[0]
                stdout += f"Number Of Positions = {num_positions}\n"
                
            # Parse position data
            if len(pkt_body) >= 60:
                lat = struct.unpack('<d', pkt_body[44:52])[0]
                lon = struct.unpack('<d', pkt_body[52:60])[0]
                stdout += f"Final Position Latitude = {lat:.10f}\n"
                stdout += f"Latitude = {lat * 57.2957795131:.9f} degree\n"
                stdout += f"Final Position Longitude = {lon:.10f}\n"
                stdout += f"Longitude = {lon * 57.2957795131:.8f} degree\n"
                
            if len(pkt_body) >= 64:
                alt = struct.unpack('<f', pkt_body[60:64])[0]
                stdout += f"Final Position Altitude = {alt:.3f}\n"
                
            # Parse heading and velocities
            if len(pkt_body) >= 68:
                heading = struct.unpack('<h', pkt_body[64:66])[0]
                heading_unc = struct.unpack('<f', pkt_body[66:70])[0] if len(pkt_body) >= 70 else 0
                stdout += f"Heading = {heading}\n"
                stdout += f"Heading Uncertainty In Radians = {heading_unc:.4f}\n"
                
            if len(pkt_body) >= 82:
                east_vel = struct.unpack('<f', pkt_body[70:74])[0]
                north_vel = struct.unpack('<f', pkt_body[74:78])[0]
                vert_vel = struct.unpack('<f', pkt_body[78:82])[0]
                stdout += f"East Velocity = {east_vel}\n"
                stdout += f"North Velocity = {north_vel}\n"
                stdout += f"Vertical Velocity = {vert_vel}\n"
                
            if len(pkt_body) >= 94:
                east_vel_unc = struct.unpack('<f', pkt_body[82:86])[0]
                north_vel_unc = struct.unpack('<f', pkt_body[86:90])[0]
                vert_vel_unc = struct.unpack('<f', pkt_body[90:94])[0]
                stdout += f"East Velocity Uncertainty = {east_vel_unc:.4f}\n"
                stdout += f"North Velocity Uncertainty = {north_vel_unc:.4f}\n"
                stdout += f"Vertical Velocity Uncertainty = {vert_vel_unc:.4f}\n"
                
            # Parse clock bias
            if len(pkt_body) >= 102:
                clock_bias = struct.unpack('<d', pkt_body[94:102])[0]
                stdout += f"Clock Bias = {clock_bias}\n"
                
            if len(pkt_body) >= 106:
                clock_bias_unc = struct.unpack('<f', pkt_body[102:106])[0]
                stdout += f"Clock Bias Uncertainty = {clock_bias_unc:.1f}\n"
                
            # Parse Inter GNSS TB
            if len(pkt_body) >= 138:
                stdout += f"Inter GNSS TB {{\n"
                gps_glo_bias = struct.unpack('<d', pkt_body[106:114])[0]
                gps_glo_bias_unc = struct.unpack('<f', pkt_body[114:118])[0]
                filt_gps_glo_bias = struct.unpack('<d', pkt_body[118:126])[0]
                filt_gps_glo_bias_unc = struct.unpack('<f', pkt_body[126:130])[0]
                gps_bds_bias = struct.unpack('<d', pkt_body[130:138])[0]
                stdout += f"   GPS To GLONASS Time Bias = {gps_glo_bias}\n"
                stdout += f"   GPS To GLONASS Time Bias Uncertainty = {gps_glo_bias_unc:.0f}\n"
                stdout += f"   Filtered GPS To GLONASS Time Bias = {filt_gps_glo_bias}\n"
                stdout += f"   Filtered GPS To GLONASS Time Bias Uncertainty = {filt_gps_glo_bias_unc:.0f}\n"
                stdout += f"   GPS To Beidou Time Bias (m) = {gps_bds_bias}\n"
                
            if len(pkt_body) >= 154:
                gps_bds_bias_unc = struct.unpack('<f', pkt_body[138:142])[0]
                filt_gps_bds_bias = struct.unpack('<d', pkt_body[142:150])[0]
                filt_gps_bds_bias_unc = struct.unpack('<f', pkt_body[150:154])[0]
                stdout += f"   GPS To Beidou Time Bias Unc (m) = {gps_bds_bias_unc:.0f}\n"
                stdout += f"   Filtered GPS To Beidou Time Bias (m) = {filt_gps_bds_bias}\n"
                stdout += f"   Filtered GPS To Beidou Time Bias Unc (m) = {filt_gps_bds_bias_unc:.0f}\n"
                stdout += f"}}\n"
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing GNSS Position Report: {e}')
            return None

    def parse_xo_frequency_estimation(self, pkt_header, pkt_body, args):
        """Parse XO Frequency Estimation (0x13D1)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 4:
            return None
            
        try:
            # Parse basic fields
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x13D1  XO Frequency Estimation\n"
            stdout += f"Version = {version}\n"
            
            # Parse frequency data if available
            if len(pkt_body) >= 8:
                freq_est = struct.unpack('<L', pkt_body[4:8])[0]
                stdout += f"Frequency Estimate = {freq_est}\n"
                
            if len(pkt_body) >= 12:
                freq_unc = struct.unpack('<L', pkt_body[8:12])[0]
                stdout += f"Frequency Uncertainty = {freq_unc}\n"
                
            # Add frequency table data if present
            if len(pkt_body) > 12:
                remaining_data = pkt_body[12:]
                if len(remaining_data) > 0:
                    stdout += f"Frequency Table Data = {binascii.hexlify(remaining_data).decode()}\n"
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing XO Frequency Estimation: {e}')
            return None

    def parse_gnss_measurement_report(self, pkt_header, pkt_body, args):
        """Parse GNSS Measurement Report (0x418B)"""
        pkt_ts = util.parse_qxdm_ts(pkt_header.timestamp)
        
        if len(pkt_body) < 4:
            return None
            
        try:
            # Parse basic fields
            version = pkt_body[0] if len(pkt_body) > 0 else 0
            num_measurements = pkt_body[1] if len(pkt_body) > 1 else 0
            
            # Format output like QCAT
            ts_str = pkt_ts.strftime('%Y %b %_d  %H:%M:%S.%f')[:-3]
            
            stdout = f"{ts_str}  [00]  0x418B  GNSS Measurement Report\n"
            stdout += f"Version = {version}\n"
            stdout += f"Number of Measurements = {num_measurements}\n"
            
            # Parse measurement data
            pos = 4
            for i in range(min(num_measurements, 32)):  # Limit to prevent excessive output
                if pos + 16 > len(pkt_body):
                    break
                    
                try:
                    sv_id = pkt_body[pos] if pos < len(pkt_body) else 0
                    constellation = pkt_body[pos + 1] if pos + 1 < len(pkt_body) else 0
                    
                    stdout += f"Measurement {i}:\n"
                    stdout += f"  SV ID = {sv_id}\n"
                    stdout += f"  Constellation = {constellation}\n"
                    
                    if pos + 8 <= len(pkt_body):
                        pseudorange = struct.unpack('<d', pkt_body[pos + 2:pos + 10])[0]
                        stdout += f"  Pseudorange = {pseudorange:.3f}\n"
                        
                    pos += 16  # Assume 16 bytes per measurement
                except:
                    break
                    
            return {'stdout': stdout, 'ts': pkt_ts}
            
        except Exception as e:
            if self.parent:
                self.parent.logger.log(logging.WARNING, f'Error parsing GNSS Measurement Report: {e}')
            return None