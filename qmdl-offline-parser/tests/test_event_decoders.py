import datetime
from scat.parsers.qualcomm.diagcommoneventparser import DiagCommonEventParser


def test_parse_qshrink_guid_format():
    parser = DiagCommonEventParser(None)
    # diag_id = 7, guid = 16 bytes
    diag_id = 7
    guid_bytes = bytes([0xDD, 0xFE, 0xB3, 0x16, 0x0A, 0xE3, 0xA2, 0xC2, 0xD2, 0x4F, 0x3E, 0xE7, 0xF2, 0xCF, 0x5A, 0xA3])
    arg_bin = bytes([diag_id]) + guid_bytes
    res = parser.parse_event_diag_qshrink_id(datetime.datetime.now(), 2865, arg_bin)
    assert res['type'] == 'EVENT_DIAG_QSHRINK_ID'
    assert res['id'] == 2865
    assert res['payload'].startswith('0x07 ')
    assert 'GUID =' in res['payload_str']
    # Check GUID pattern: decimal blocks separated by '-'
    guid_part = res['payload_str'].split('GUID =')[-1].strip()
    assert '-' in guid_part


def test_parse_process_name_payload():
    parser = DiagCommonEventParser(None)
    diag_id = 7
    name = b'msm/modem/wlan_pd\x00'
    arg_bin = bytes([diag_id]) + name
    res = parser.parse_event_diag_process_name_id(datetime.datetime.now(), 2866, arg_bin)
    assert res['type'] == 'EVENT_DIAG_PROCESS_NAME_ID'
    assert res['id'] == 2866
    assert res['payload'].startswith('0x07 ')
    assert 'msm/modem' in res['payload_str']
