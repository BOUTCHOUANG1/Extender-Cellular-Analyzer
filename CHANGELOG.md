# Changelog

All notable changes to Extender Cellular Analyzer.

---

## [2.0.0] - 2025-10-09

### Added
- **Full QCAT Parity**: Comprehensive TXT output matching QCAT format
  - Events with full formatting (timestamps, thread IDs, payload hex/strings)
  - QMI messages with service name mapping and TLV parsing
  - RUIM/APDU commands with full decoding (10+ command types)
  - CM Phone Events with 20+ event types and detailed fields
  - PM Policy Stats complete parsing

- **Enhanced Message Parsers**:
  - `DiagQCATMsgParser` for RUIM, QMI, CM, and PM messages
  - Full APDU command decoder (STATUS, SELECT, READ, WRITE, etc.)
  - QMI service ID mapping (21 services: DMS, NAS, WDS, QOS, etc.)
  - TLV (Type-Length-Value) automatic extraction
  - CM event type mapping with operating mode decoder

- **Output Format Verification**:
  - TXT: 416 KB human-readable QCAT-style output
  - JSON: 24 MB structured data with 55,433 messages
  - PCAP: 1.8 MB Wireshark-compatible with 18,039 packets

- **Documentation**:
  - Comprehensive README with platform-specific installation
  - Organized docs/ directory with key documentation
  - Troubleshooting guide for common issues

### Changed
- Integrated SCAT v1.4.0 live capture with Extender offline analysis
- Enhanced TXT writer with `_write_qcat_message()` method
- Improved message routing and parser integration

### Removed
- QCSuper directory (not needed)
- Duplicate documentation files
- Test output files

### Fixed
- USB/Serial device initialization
- Event parsing with proper timestamp handling
- PCAP generation with correct GSMTAP encapsulation

---

## [1.0.0] - 2025-05-10

### Added
- Initial integration of SCAT and Extender-Cellular-Analyzer
- Basic offline QMDL parsing
- JSON and PCAP output support
- Event decoding
- RRC/NAS/MAC message parsing

---

## Version History

- **2.0.0** (2025-10-09): Full QCAT parity with comprehensive decoding
- **1.0.0** (2025-05-10): Initial integrated release
