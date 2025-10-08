#!/usr/bin/env python3

from functools import wraps
import calendar, datetime
import logging
import struct
import uuid

from scat.parsers.qualcomm import diagcmd
import scat.util as util

class DiagCommonEventParser:
    def __init__(self, parent):
        self.parent = parent
        self.header = b''

        if self.parent:
            self.display_format = self.parent.display_format
            self.gsmtapv3 = self.parent.gsmtapv3
        else:
            self.display_format = 'x'
            self.gsmtapv3 = False

        # Event IDs are available at:
        # https://source.codeaurora.org/quic/la/platform/vendor/qcom-opensource/wlan/qcacld-2.0/tree/CORE/VOSS/inc/event_defs.h
        # https://android.googlesource.com/kernel/msm/+/android-7.1.0_r0.2/drivers/staging/qcacld-2.0/CORE/VOSS/inc/event_defs.h
        self.process = {
            # Existing events
            1682: (self.parse_event_ipv6_sm_event, 'IPV6_SM_EVENT'),
            1684: (self.parse_event_ipv6_prefix_update, 'IPV6_PREFIX_UPDATE'),
            2865: (self.parse_event_diag_qshrink_id, 'DIAG_QSHRINK_ID'),
            2866: (self.parse_event_diag_process_name_id, 'DIAG_PROCESS_NAME'),
            # LTE, WCDMA, GSM, NR common events (for demonstration)
            1605: (self.parse_event_common, 'LTE_RRC_TIMER_STATUS'),
            1606: (self.parse_event_common, 'LTE_RRC_STATE_CHANGE'),
            1609: (self.parse_event_common, 'LTE_RRC_DL_MSG'),
            1610: (self.parse_event_common, 'LTE_RRC_UL_MSG'),
            1614: (self.parse_event_common, 'LTE_RRC_PAGING_DRX_CYCLE'),
            2100: (self.parse_event_common, 'WCDMA_RRC_STATE_CHANGE'),
            2101: (self.parse_event_common, 'WCDMA_RRC_DL_MSG'),
            2102: (self.parse_event_common, 'WCDMA_RRC_UL_MSG'),
            2103: (self.parse_event_common, 'WCDMA_RRC_PAGING_DRX_CYCLE'),
            1200: (self.parse_event_common, 'GSM_RACH_ATTEMPT'),
            1201: (self.parse_event_common, 'GSM_RACH_SUCCESS'),
            1202: (self.parse_event_common, 'GSM_RACH_FAILURE'),
            1210: (self.parse_event_common, 'GSM_CELL_SELECTION'),
            1211: (self.parse_event_common, 'GSM_CELL_RESELECTION'),
            3000: (self.parse_event_common, 'NR_RRC_STATE_CHANGE'),
            3001: (self.parse_event_common, 'NR_RRC_DL_MSG'),
            3002: (self.parse_event_common, 'NR_RRC_UL_MSG'),
            3010: (self.parse_event_common, 'NR_RRC_PAGING_DRX_CYCLE'),
        }

    def parse_event_common(self, ts, event_id, arg_bin):
        import binascii
        event_name = self.process[event_id][1] if event_id in self.process else f'UNKNOWN_EVENT_{event_id}'
        payload_hex = ' '.join(f'{b:02X}' for b in arg_bin)
        # Try to decode payload as ASCII if possible
        try:
            payload_ascii = arg_bin.decode('ascii') if all(32 <= b < 127 for b in arg_bin) else ''
        except Exception:
            payload_ascii = ''
        return {
            'type': event_name,
            'id': event_id,
            'thread': '00',
            'payload': payload_hex,
            'payload_str': payload_ascii,
            'timestamp': ts
        }

    def update_parameters(self, display_format, gsmtapv3):
        self.display_format = display_format
        self.gsmtapv3 = gsmtapv3

    def build_header(func):
        @wraps(func)
        def wrapped_function(self, *args, **kwargs):
            osmocore_log_hdr = util.create_osmocore_logging_header(
                timestamp = args[0],
                process_name = b'Event',
                pid = args[1],
            )

            gsmtap_hdr = util.create_gsmtap_header(
                version = 2,
                payload_type = util.gsmtap_type.OSMOCORE_LOG)

            log_precontent = "{}: ".format(self.process[args[1]][1]).encode('utf-8')

            self.header = gsmtap_hdr + osmocore_log_hdr + log_precontent
            return func(self, *args, **kwargs)
        return wrapped_function

    @build_header
    def parse_event_ipv6_sm_event(self, ts, event_id, arg_bin):
        # Event 1682: 2023-01-01 15:02:20.275880: Binary(len=0x04) = 04 80 02 03
        log_content = "{}".format(' '.join('{:02x}'.format(x) for x in arg_bin)).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_ipv6_prefix_update(self, ts, event_id, arg_bin):
        # Event 1684: 2018-10-25 18:40:03.870095: Binary(len=0x18) = 04 80 02 03 | 00 00 00 00 | 2a 02 30 3e 28 02 48 9c | 40 00 00 00 | 00 00 00 00
        log_content = "{}".format(' '.join('{:02x}'.format(x) for x in arg_bin)).encode('utf-8')

        return self.header + log_content



    def parse_event_diag_qshrink_id(self, ts, event_id, arg_bin):
        diag_id = arg_bin[0]
        diag_uuid = arg_bin[1:]
        guid_str = ""
        if len(diag_uuid) == 16:
            guid_blocks = [
                int.from_bytes(diag_uuid[0:4], 'big'),
                int.from_bytes(diag_uuid[4:6], 'big'),
                int.from_bytes(diag_uuid[6:8], 'big'),
                int.from_bytes(diag_uuid[8:10], 'big'),
                int.from_bytes(diag_uuid[10:16], 'big')
            ]
            guid_str = "-".join(str(b) for b in guid_blocks)
        else:
            guid_str = ""
        payload_hex = f"0x{diag_id:02X} " + ' '.join(f'{b:02X}' for b in diag_uuid)
        return {
            'type': 'EVENT_DIAG_QSHRINK_ID',
            'id': event_id,
            'thread': '00',
            'payload': payload_hex,
            'payload_str': f"Diag Id = {diag_id}, GUID = {guid_str}",
            'timestamp': ts
        }

    def parse_event_diag_process_name_id(self, ts, event_id, arg_bin):
        diag_id = arg_bin[0]
        try:
            diag_process_name = arg_bin[1:].decode('utf-8', errors='replace')
        except Exception:
            diag_process_name = binascii.hexlify(arg_bin[1:]).decode()
        payload_hex = f"0x{diag_id:02X} " + ' '.join(f'{b:02X}' for b in arg_bin[1:])
        return {
            'type': 'EVENT_DIAG_PROCESS_NAME_ID',
            'id': event_id,
            'thread': '00',
            'payload': payload_hex,
            'payload_str': diag_process_name,
            'timestamp': ts
        }

