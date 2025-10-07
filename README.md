# Extender-Cellular-Analyzer

## Overview
Extender-Cellular-Analyzer is a comprehensive tool for parsing, analyzing, and reporting cellular log data from QMDL2 files. It supports advanced feature extraction, robust output generation (JSON, TXT, PCAP), and is designed for both machine and human analysis workflows.

## Features
- **File Information Extraction**: Metadata about the input QMDL2 file (filename, size, timestamp, parser version).
- **Summary Statistics**: Total messages, cellular messages, RRC/NAS/MAC breakdown, events, measurements, cellular percentage.
- **Cell Information Extraction**: Detailed LTE cell info (EARFCN, PCI, bandwidth, MCC/MNC, TAC, Cell ID, timestamps).
- **Measurement Extraction**: LTE measurement data (EARFCN, PCI, SFN/SubFN, timestamps, radio ID).
- **Control Plane Message Extraction**: Raw control plane messages (length, hex data).
- **Error and Warning Handling**: Graceful handling and reporting of unknown message versions.
- **Output Writer Robustness**: Writers handle all data structures (lists, dicts) for parsed fields.
- **PCAP Output Generation**: Generates a PCAP file for packet analysis in Wireshark.
- **Timestamp and Radio ID Tracking**: Precise tracking for all parsed events.
- **Human-Readable Reporting**: TXT report with clear formatting and parsed values.

## Quick Start
### Prerequisites
- Python >= 3.7
- QMDL2 log file (e.g., `2.qmdl2`)

### Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/BOUTCHOUANG1/Extender-Cellular-Analyzer.git
cd Extender-Cellular-Analyzer
pip install -r requirements.txt
```

### Running the Parser
Run the parser with all output options:
```bash
python3 -m scat.main -t qc -d 2.qmdl2 --json-file 2_output.json --txt-file 2_output.txt --pcap-file 2_output.pcap --preserve-intermediate
```

#### Output Files
- `2_output.json`: Machine-readable parsed data
- `2_output.txt`: Human-readable report
- `2_output.pcap`: Packet capture for Wireshark

## Output Validation
- All outputs are generated and validated for completeness and correctness.
- PCAP file can be opened in Wireshark for advanced analysis.
- TXT and JSON files contain all extracted features and statistics.

## Documentation
- [SCAT Feature Test Documentation](./SCAT_Feature_Test_Documentation.md): Detailed feature explanations, testing logic, and workflow.
- [Feature Testing Guide](./FEATURE_TESTING.md): (Add this file for step-by-step feature testing instructions.)

## Advanced Usage
- Supports robust error handling and reporting for unknown message types.
- Output writers are patched to handle variable data structures.
- All features are exercised and documented in the provided sample outputs.

## Example Workflow
1. Prepare your QMDL2 log file.
2. Run the parser with the command above.
3. Review the generated outputs (`2_output.json`, `2_output.txt`, `2_output.pcap`).
4. Open the PCAP file in Wireshark for packet-level analysis.
5. Consult the documentation for feature details and troubleshooting.

## Links
- [SCAT Feature Test Documentation](./SCAT_Feature_Test_Documentation.md)
- [Feature Testing Guide](./FEATURE_TESTING.md)

## Support
For further details, specific field explanations, or troubleshooting, refer to the documentation or open an issue in the repository.

---
*Last updated: October 7, 2025*