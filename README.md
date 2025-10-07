# Extender-Cellular-Analyzer

## Project Overview & Developer Guide

### What is this project?
Extender-Cellular-Analyzer is a Python-based tool for offline analysis of cellular diagnostic logs (QMDL2 format, typically from Qualcomm devices). It parses these logs and extracts detailed information about network events, measurements, and control messages, outputting results in JSON, TXT, and PCAP formats for further analysis (including in Wireshark).

### How does it work?
- **Input:** You provide a QMDL2 log file (e.g., `2.qmdl2`).
- **Processing:** The tool parses the file, extracts cellular events, measurements, and metadata.
- **Output:** Results are written to:
	- `2_output.json` (structured data for automation/scripts)
	- `2_output.txt` (human-readable report)
	- `2_output.pcap` (packet capture for Wireshark)

---

## Main Components & Script Connections

### 1. `main.py` (Entry Point)
- Located at: `qmdl-offline-parser/src/scat/main.py`
- Handles command-line arguments, sets up the parser, and manages output writers.
- Connects to:
	- **Parsers** (e.g., Qualcomm, Samsung, HiSilicon)
	- **Writers** (JSON, TXT, PCAP, Socket)
	- **IODevice** (for reading files)

### 2. Writers
- **`jsonwriter.py`**: Writes structured output to JSON. Tracks file info, summary stats, cell info, measurements, etc.
- **`txtwriter.py`**: Writes a readable report to TXT. Includes headers, stats, and parsed events.
- **`pcapwriter.py`**: Writes packet data to PCAP for Wireshark analysis.
- All writers are managed by `main.py` and can be combined using a `CompositeWriter` class for multi-format output.

### 3. Parsers
- **Qualcomm, Samsung, HiSilicon Parsers**: Each vendor has a dedicated parser module (e.g., `qualcommparser.py`). These extract vendor-specific log details.
- Parsers are selected in `main.py` based on the `--type` argument.

### 4. Enhanced QMDL Parser (`enhanced_qmdl_parser.py`)
- A wrapper script for maximum information extraction.
- Handles output file naming, writer setup, and parser configuration.
- Useful for batch or automated analysis.

### 5. IO Devices
- **`FileIO`**: Reads log files for offline analysis.

---

## How to Patch or Upgrade
- **Add a new output format:** Create a new writer class (e.g., `csvwriter.py`) and update `main.py` to support it.
- **Support a new log type/vendor:** Add a new parser module and register it in `main.py`.
- **Change output structure:** Edit the relevant writer (e.g., `jsonwriter.py`) to adjust fields or formatting.
- **Improve error handling:** Update exception blocks in `main.py` and writers to provide clearer messages or fallback logic.

---

## Example Workflow
1. Place your QMDL2 file in the project directory.
2. Run:
	 ```bash
	 python3 -m scat.main -t qc -d 2.qmdl2 --json-file 2_output.json --txt-file 2_output.txt --pcap-file 2_output.pcap
	 ```
3. Review the outputs. Open the PCAP file in Wireshark for packet-level analysis.

---


## Code Documentation & Readability
- All major source files now include comprehensive docstrings and inline comments explaining their logic, classes, and functions.
- This makes the codebase much easier to read, understand, and maintain for both Python and non-Python developers.

## Where to Find More Details
- **Feature explanations and testing:** See [`SCAT_Feature_Test_Documentation.md`](./SCAT_Feature_Test_Documentation.md)
- **Quick start and commands:** See the top of this README

---

## For Java Developers & Non-Python Users
- The architecture is modular: each parser and writer is a class, and the main script wires them together.
- If you want to patch or extend, look for class definitions and method calls in the relevant `.py` files.
- Python’s class and method structure is similar to Java, but indentation and imports differ.
- You can add new features by creating new classes or editing existing ones, then updating the main entry point to use them.

---

## Support & Contribution
For further details, specific field explanations, or troubleshooting, refer to the documentation or open an issue in the repository.
Contributions are welcome! If you want to add features or fix bugs, fork the repo, make your changes, and submit a pull request.

---

*Last updated: October 7, 2025*

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