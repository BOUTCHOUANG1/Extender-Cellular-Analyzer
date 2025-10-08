#!/usr/bin/env python3

from functools import wraps
import binascii
import calendar, datetime
import logging
import struct

from scat.parsers.qualcomm import diagcmd
import scat.util as util

class DiagLteEventParser:
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
            # LTE Events
            1605: (self.parse_event_lte_rrc_timer_status, 'LTE_RRC_TIMER_STATUS'),
            1606: (self.parse_event_lte_rrc_state_change, 'LTE_RRC_STATE_CHANGE'),
            1609: (self.parse_event_lte_rrc_dl_msg, 'LTE_RRC_DL_MSG'),
            1610: (self.parse_event_lte_rrc_ul_msg, 'LTE_RRC_UL_MSG'),
            1614: (self.parse_event_lte_rrc_paging_drx_cycle, 'LTE_RRC_PAGING_DRX_CYCLE'),
            1627: (self.parse_event_lte_nas_msg, 'LTE_CM_INCOMING_MSG'),
            1628: (self.parse_event_lte_nas_msg, 'LTE_CM_OUTGOING_MSG'),
            1629: (self.parse_event_lte_nas_msg, 'LTE_EMM_INCOMING_MSG'),
            1630: (self.parse_event_lte_nas_msg, 'LTE_EMM_OUTGOING_MSG'),
            1633: (self.parse_event_lte_nas_msg, 'LTE_REG_INCOMING_MSG'),
            1634: (self.parse_event_lte_nas_msg, 'LTE_REG_OUTGOING_MSG'),
            1635: (self.parse_event_lte_nas_msg, 'LTE_ESM_INCOMING_MSG'),
            1636: (self.parse_event_lte_nas_msg, 'LTE_ESM_OUTGOING_MSG'),
            1966: (self.parse_event_lte_nas_ota_msg, 'LTE_EMM_OTA_INCOMING_MSG'),
            1967: (self.parse_event_lte_nas_ota_msg, 'LTE_EMM_OTA_OUTGOING_MSG'),
            1968: (self.parse_event_lte_nas_ota_msg, 'LTE_ESM_OTA_INCOMING_MSG'),
            1969: (self.parse_event_lte_nas_ota_msg, 'LTE_ESM_OTA_OUTGOING_MSG'),
            1631: (self.parse_event_lte_emm_esm_timer, 'LTE_EMM_TIMER_START'),
            1632: (self.parse_event_lte_emm_esm_timer, 'LTE_EMM_TIMER_EXPIRY'),
            1637: (self.parse_event_lte_emm_esm_timer, 'LTE_ESM_TIMER_START'),
            1638: (self.parse_event_lte_emm_esm_timer, 'LTE_ESM_TIMER_EXPIRY'),
            1938: (self.parse_event_lte_ml1_phr_report, 'LTE_ML1_PHR_REPORT'),
            1994: (self.parse_event_lte_rrc_state_change_trigger, 'LTE_RRC_STATE_CHANGE_TRIGGER'),
            # WCDMA/UMTS Events
            2100: (self.parse_event_wcdma_rrc_state_change, 'WCDMA_RRC_STATE_CHANGE'),
            2101: (self.parse_event_wcdma_rrc_dl_msg, 'WCDMA_RRC_DL_MSG'),
            2102: (self.parse_event_wcdma_rrc_ul_msg, 'WCDMA_RRC_UL_MSG'),
            2103: (self.parse_event_wcdma_rrc_paging_drx_cycle, 'WCDMA_RRC_PAGING_DRX_CYCLE'),
            2127: (self.parse_event_wcdma_nas_msg, 'WCDMA_CM_INCOMING_MSG'),
            2128: (self.parse_event_wcdma_nas_msg, 'WCDMA_CM_OUTGOING_MSG'),
            2129: (self.parse_event_wcdma_nas_msg, 'WCDMA_EMM_INCOMING_MSG'),
            2130: (self.parse_event_wcdma_nas_msg, 'WCDMA_EMM_OUTGOING_MSG'),
            2133: (self.parse_event_wcdma_nas_msg, 'WCDMA_REG_INCOMING_MSG'),
            2134: (self.parse_event_wcdma_nas_msg, 'WCDMA_REG_OUTGOING_MSG'),
            2135: (self.parse_event_wcdma_nas_msg, 'WCDMA_ESM_INCOMING_MSG'),
            2136: (self.parse_event_wcdma_nas_msg, 'WCDMA_ESM_OUTGOING_MSG'),
            # GSM Events
            1200: (self.parse_event_gsm_rach_attempt, 'GSM_RACH_ATTEMPT'),
            1201: (self.parse_event_gsm_rach_success, 'GSM_RACH_SUCCESS'),
            1202: (self.parse_event_gsm_rach_failure, 'GSM_RACH_FAILURE'),
            1210: (self.parse_event_gsm_cell_selection, 'GSM_CELL_SELECTION'),
            1211: (self.parse_event_gsm_cell_reselection, 'GSM_CELL_RESELECTION'),
            # 5G NR Events
            3000: (self.parse_event_nr_rrc_state_change, 'NR_RRC_STATE_CHANGE'),
            3001: (self.parse_event_nr_rrc_dl_msg, 'NR_RRC_DL_MSG'),
            3002: (self.parse_event_nr_rrc_ul_msg, 'NR_RRC_UL_MSG'),
            3010: (self.parse_event_nr_rrc_paging_drx_cycle, 'NR_RRC_PAGING_DRX_CYCLE'),
            3027: (self.parse_event_nr_nas_msg, 'NR_CM_INCOMING_MSG'),
            3028: (self.parse_event_nr_nas_msg, 'NR_CM_OUTGOING_MSG'),
            3029: (self.parse_event_nr_nas_msg, 'NR_EMM_INCOMING_MSG'),
            3030: (self.parse_event_nr_nas_msg, 'NR_EMM_OUTGOING_MSG'),
            3033: (self.parse_event_nr_nas_msg, 'NR_REG_INCOMING_MSG'),
            3034: (self.parse_event_nr_nas_msg, 'NR_REG_OUTGOING_MSG'),
            3035: (self.parse_event_nr_nas_msg, 'NR_ESM_INCOMING_MSG'),
            3036: (self.parse_event_nr_nas_msg, 'NR_ESM_OUTGOING_MSG'),
        }

    # WCDMA/UMTS event decoders
    def parse_event_wcdma_rrc_state_change(self, ts, event_id, arg_bin):
        return {'type': 'WCDMA_RRC_STATE_CHANGE', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_wcdma_rrc_dl_msg(self, ts, event_id, arg_bin):
        return {'type': 'WCDMA_RRC_DL_MSG', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_wcdma_rrc_ul_msg(self, ts, event_id, arg_bin):
        return {'type': 'WCDMA_RRC_UL_MSG', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_wcdma_rrc_paging_drx_cycle(self, ts, event_id, arg_bin):
        return {'type': 'WCDMA_RRC_PAGING_DRX_CYCLE', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_wcdma_nas_msg(self, ts, event_id, arg_bin):
        return {'type': 'WCDMA_NAS_MSG', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}

    # GSM event decoders
    def parse_event_gsm_rach_attempt(self, ts, event_id, arg_bin):
        return {'type': 'GSM_RACH_ATTEMPT', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_gsm_rach_success(self, ts, event_id, arg_bin):
        return {'type': 'GSM_RACH_SUCCESS', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_gsm_rach_failure(self, ts, event_id, arg_bin):
        return {'type': 'GSM_RACH_FAILURE', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_gsm_cell_selection(self, ts, event_id, arg_bin):
        return {'type': 'GSM_CELL_SELECTION', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_gsm_cell_reselection(self, ts, event_id, arg_bin):
        return {'type': 'GSM_CELL_RESELECTION', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}

    # 5G NR event decoders
    def parse_event_nr_rrc_state_change(self, ts, event_id, arg_bin):
        return {'type': 'NR_RRC_STATE_CHANGE', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_nr_rrc_dl_msg(self, ts, event_id, arg_bin):
        return {'type': 'NR_RRC_DL_MSG', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_nr_rrc_ul_msg(self, ts, event_id, arg_bin):
        return {'type': 'NR_RRC_UL_MSG', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_nr_rrc_paging_drx_cycle(self, ts, event_id, arg_bin):
        return {'type': 'NR_RRC_PAGING_DRX_CYCLE', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}
    def parse_event_nr_nas_msg(self, ts, event_id, arg_bin):
        return {'type': 'NR_NAS_MSG', 'id': event_id, 'thread': '00', 'payload': binascii.hexlify(arg_bin).decode(), 'payload_str': '', 'timestamp': ts}

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
    def parse_event_lte_rrc_timer_status(self, ts, event_id, arg_bin):
        log_content = "{}".format(' '.join('{:02x}'.format(x) for x in arg_bin)).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_rrc_state_change(self, ts, event_id, arg1):
        rrc_state_map = {
            1: "RRC_IDLE_NOT_CAMPED",
            2: "RRC_IDLE_CAMPED",
            3: "RRC_CONNECTING",
            4: "RRC_CONNECTED",
            7: "RRC_CLOSING",
        }
        if arg1 in rrc_state_map.keys():
            rrc_state = rrc_state_map[arg1]
        else:
            rrc_state = "{:02x}".format(arg1)

        log_content = "rrc_state={}".format(rrc_state).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_rrc_dl_msg(self, ts, event_id, arg1, arg2):
        channel_dl_map = {
            1: "BCCH",
            2: "PCCH",
            3: "CCCH",
            4: "DCCH"
        }

        message_type_map = {
            0x00: "MasterInformationBlock",
            0x01: "SystemInformationBlockType1",
            0x02: "SystemInformationBlockType2",
            0x03: "SystemInformationBlockType3",
            0x04: "SystemInformationBlockType4",
            0x05: "SystemInformationBlockType5",
            0x06: "SystemInformationBlockType6",
            0x07: "SystemInformationBlockType7",
            0x40: "Paging",
            0x4b: "RRCConnectionSetup",
            0x81: "DLInformationTransfer",
            0x85: "RRCConnectionRelease",
        }

        if arg1 in channel_dl_map.keys():
            channel = channel_dl_map[arg1]
        else:
            channel = "Unknown"

        if arg2 in message_type_map.keys():
            message_type = message_type_map[arg2]
        else:
            message_type = "Unknown ({:2x})".format(arg2)

        log_content = "channel={}, message_type={}".format(channel, message_type).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_rrc_ul_msg(self, ts, event_id, arg1, arg2):
        channel_ul_map = {
            5: "CCCH",
            6: "DCCH"
        }

        message_type_map = {
            0x01: "RRCConnectionRequest",
            0x84: "RRCConnectionSetupComplete",
            0x89: "ULInformationTransfer",
        }

        if arg1 in channel_ul_map.keys():
            channel = channel_ul_map[arg1]
        else:
            channel = "Unknown"

        if arg2 in message_type_map.keys():
            message_type = message_type_map[arg2]
        else:
            message_type = "Unknown ({:2x})".format(arg2)

        log_content = "channel={}, message_type={}".format(channel, message_type).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_rrc_paging_drx_cycle(self, ts, event_id, arg1, arg2):
        log_content = "{:02x} {:02x}".format(arg1, arg2).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_nas_msg(self, ts, event_id, arg1):
        message_id = struct.unpack('<L', arg1[:4])[0]
        log_content = "0x{:04x}".format(message_id).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_nas_ota_msg(self, ts, event_id, arg1):
        log_content = "{:02x}".format(arg1).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_emm_esm_timer(self, ts, event_id, arg1):
        log_content = "{:02x}".format(arg1).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_ml1_phr_report(self, ts, event_id, arg1, arg2):
        log_content = "{:02x} {:02x}".format(arg1, arg2).encode('utf-8')

        return self.header + log_content

    @build_header
    def parse_event_lte_rrc_state_change_trigger(self, ts, event_id, arg1):
        log_content = "{:02x}".format(arg1).encode('utf-8')

        return self.header + log_content
