# Project Summary

## Extender Cellular Analyzer v2.0.0

**All-in-One Cellular Log Analysis Tool with Full QCAT Parity**

---

## Overview

Comprehensive tool combining SCAT v1.4.0 live capture capabilities with enhanced offline QMDL parsing and full QCAT-style output formatting. Supports live USB/Serial capture and offline analysis with three output formats: TXT, JSON, and PCAP.

---

## Key Features

### 1. Live Capture
- USB device capture (Qualcomm diagnostic mode)
- Serial port capture with configurable settings
- Real-time log streaming
- TCP server mode

### 2. Offline Analysis
- QMDL/DLF/HDF file parsing
- Batch processing support
- 237 MB file processed in ~60 seconds

### 3. Output Formats

**TXT (QCAT-Style)**
- Human-readable comprehensive decoding
- Events, QMI, RUIM, CM messages
- 416 KB output from 237 MB input

**JSON (Structured Data)**
- Complete message information
- 55,433 messages parsed
- 24 MB output with full details

**PCAP (Wireshark)**
- GSMTAP encapsulation
- 18,039 packets captured
- 1.8 MB output for protocol analysis

### 4. Message Decoding

**Events**
- Full QCAT formatting
- Timestamps, thread IDs, payload hex/strings
- 64 unique event types supported

**QMI Messages**
- 21 service types (DMS, NAS, WDS, QOS, etc.)
- TLV parsing
- Request/Response/Indication detection

**RUIM/APDU**
- 10+ command types (STATUS, SELECT, READ, WRITE, etc.)
- Full parameter decoding (CLA, INS, P1, P2, P3)
- Status word library

**CM Phone Events**
- 20+ event types
- Operating mode decoder
- Detailed field extraction

**Protocol Messages**
- RRC/NAS/MAC/PDCP
- LTE and 5G NR support
- GSMTAP encapsulation for Wireshark

---

## Architecture

```
Input Sources
├── Live USB Capture
├── Live Serial Capture
└── Offline QMDL Files
    ↓
QualcommParser
├── DiagGsmLogParser
├── DiagLteLogParser
├── DiagNrLogParser
├── DiagQCATMsgParser (NEW)
└── Event Parsers
    ↓
Output Writers
├── TxtWriter (QCAT format)
├── JsonWriter (Structured data)
└── PcapWriter (GSMTAP)
    ↓
Output Files
├── .txt (Human-readable)
├── .json (Machine-parseable)
└── .pcap (Wireshark-compatible)
```

---

## Technical Specifications

### Supported Platforms
- Linux (Ubuntu, Debian, etc.)
- Windows (7, 10, 11)
- macOS (10.14+)

### Requirements
- Python 3.8+
- libusb-1.0 (for USB capture)
- 4 GB RAM minimum
- 100 MB disk space

### Dependencies
- bitstring>=3.1.7
- libscrc>=1.8.0
- packaging>=19.0
- pyusb>=1.0.2
- pyserial>=3.3

### Performance
- Processing Speed: ~4 MB/s
- Memory Usage: <500 MB
- Output Compression: 0.17% (TXT), 10% (JSON), 0.76% (PCAP)

---

## File Structure

```
Extender-Cellular-Analyzer/
├── qmdl-offline-parser/
│   ├── src/scat/
│   │   ├── parsers/qualcomm/
│   │   │   ├── diagqcatmsgparser.py    (NEW - RUIM/QMI/CM)
│   │   │   ├── diagltelogparser.py
│   │   │   ├── diagnrlogparser.py
│   │   │   └── qualcommparser.py
│   │   ├── writers/
│   │   │   ├── txtwriter.py            (ENHANCED)
│   │   │   ├── jsonwriter.py
│   │   │   └── pcapwriter.py
│   │   ├── iodevices/
│   │   │   ├── usbio.py
│   │   │   ├── serialio.py
│   │   │   └── fileio.py
│   │   └── main.py
│   ├── requirements.txt
│   └── pyproject.toml
├── docs/
│   ├── FULL_QCAT_PARITY_COMPLETE.md
│   ├── ALL_FORMATS_VERIFICATION.md
│   ├── QUICK_START.md
│   └── PROJECT_SUMMARY.md
├── venv/
├── CHANGELOG.md
└── README.md
```

---

## Usage Examples

### Quick Analysis
```bash
python3 -m scat.main -t qc -d logfile.qmdl2 --events --txt-file output.txt
```

### Comprehensive Analysis
```bash
python3 -m scat.main -t qc -d logfile.qmdl2 \
    --events --msgs \
    --txt-file analysis.txt \
    --json-file analysis.json \
    -F analysis.pcap
```

### Live USB Capture
```bash
python3 -m scat.main -t qc -u --events --txt-file live.txt
```

---

## Development Status

### Completed ✅
- Live USB/Serial capture integration
- Offline QMDL parsing
- Full QCAT-style TXT output
- Comprehensive QMI decoding
- RUIM/APDU full decoding
- CM Phone Event parsing
- JSON structured output
- PCAP Wireshark output
- Multi-platform support
- Documentation

### Future Enhancements
- Additional message type parsers
- GUI interface
- Real-time visualization
- Advanced filtering options
- Export to additional formats

---

## Testing Results

### Test File
- **Name**: diag_log_20250510_1511231746886283842.qmdl2
- **Size**: 237.48 MB
- **Processing Time**: ~60 seconds

### Output Generated
- **TXT**: 416 KB (QCAT format)
- **JSON**: 24 MB (55,433 messages)
- **PCAP**: 1.8 MB (18,039 packets)

### Messages Parsed
- Total: 55,433
- Cellular: 8,729
- Events: Multiple types
- Cells: 4 unique

---

## Documentation

### Main Documents
1. **README.md** - Installation and usage guide
2. **CHANGELOG.md** - Version history
3. **docs/FULL_QCAT_PARITY_COMPLETE.md** - Feature documentation
4. **docs/ALL_FORMATS_VERIFICATION.md** - Output format details
5. **docs/QUICK_START.md** - Quick start guide

### Code Documentation
- Inline comments in source files
- Docstrings for all major functions
- Type hints where applicable

---

## Credits

- **SCAT v1.4.0**: https://github.com/fgsect/scat
- **Extender-Cellular-Analyzer**: Base offline parser
- **Contributors**: Development team

---

## License

GPL-2.0-or-later

---

## Version Information

- **Current Version**: 2.0.0
- **Release Date**: October 9, 2025
- **Status**: Production Ready ✅
- **Python**: 3.8+
- **Platforms**: Linux, Windows, macOS
