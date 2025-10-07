# SCAT QMDL2 Feature Test Documentation

## Overview
This document provides a detailed explanation of each feature tested using the SCAT Enhanced QMDL Offline Parser on the sample file `2.qmdl2`. It covers the testing process, logic, and output validation for each feature, with explicit details on how the parser and its output writers handle cellular log data.

---

## 1. File Information Extraction
### **Feature**
Extracts metadata about the input QMDL2 file, including filename, size, parse timestamp, and parser version.

### **How It Was Tested**
- Ran the parser with the command:
  ```bash
  python3 -m scat.main -t qc -d 2.qmdl2 --json-file 2_output.json --txt-file 2_output.txt --pcap-file 2_output.pcap
  ```
- Verified the `file_info` section in `2_output.json` and the header in `2_output.txt`.

### **Process & Logic**
- The parser reads the file and records its metadata before parsing begins.
- Metadata is written to both JSON and TXT outputs for traceability.

---

## 2. Summary Statistics
### **Feature**
Calculates and reports summary statistics: total messages, cellular messages, RRC/NAS/MAC messages, events, measurements, and cellular percentage.

### **How It Was Tested**
- Checked the `summary` section in `2_output.json` for all expected fields.
- Confirmed summary lines in TXT output.

### **Process & Logic**
- As the parser processes each log entry, counters for each message type are incremented.
- At the end, these counters are aggregated and output in summary form.

---

## 3. Cell Information Extraction
### **Feature**
Extracts detailed information about detected LTE cells, including EARFCN, PCI, bandwidth, MCC/MNC, TAC, Cell ID, and timestamps.

### **How It Was Tested**
- Located the `cell_info` array in `2_output.json`.
- Verified corresponding cell info blocks in TXT output.

### **Process & Logic**
- The parser identifies RRC SCell Info messages and extracts all relevant fields.
- Each cell is represented as a dictionary in JSON and a formatted block in TXT.
- Handles both single and multiple cell scenarios.

---

## 4. Measurement Extraction
### **Feature**
Extracts LTE measurement data, including EARFCN, PCI, SFN/SubFN, timestamps, and radio ID.

### **How It Was Tested**
- Inspected the `measurements` array in `2_output.json` for completeness and structure.
- Verified measurement sections in TXT output, including parsed values and timestamps.

### **Process & Logic**
- The parser processes ML1 SCell Meas Response messages, extracting measurement fields.
- Each measurement is output as a dictionary (JSON) and a formatted block (TXT).
- The writers were patched to robustly handle both lists and dicts, ensuring all measurements are captured regardless of data structure.

---

## 5. Control Plane Message Extraction
### **Feature**
Extracts and displays raw control plane messages, including length and hex data.

### **How It Was Tested**
- Located control plane message blocks in TXT output, showing length and hex data.
- Confirmed presence of these messages in the parsed output.

### **Process & Logic**
- The parser identifies control plane messages and extracts their raw binary data.
- Data is formatted as hex and output in TXT for human analysis.
- Ensures advanced message types are not skipped.

---

## 6. Error and Warning Handling
### **Feature**
Handles unexpected or unknown message versions gracefully, reporting them in the output.

### **How It Was Tested**
- Observed lines such as `Unexpected PDCP Cipher Data Subpacket version 40` and `Unknown LTE MAC DL transport block packet version 0x31` in the terminal and TXT output.

### **Process & Logic**
- The parser checks message versions against known types.
- Unknown or unexpected versions are logged as warnings, not errors, allowing parsing to continue.
- This ensures robustness and completeness of analysis.

---

## 7. Output Writer Robustness
### **Feature**
Ensures both JSON and TXT writers can handle all data structures (lists, dicts) for parsed fields.

### **How It Was Tested**
- Patched both writers to use helper functions for dict/list handling.
- Ran the parser and confirmed no runtime errors, with all expected data present in outputs.

### **Process & Logic**
- Writers use a `process_item` helper to recursively handle dicts and lists.
- This logic prevents crashes when the parser outputs variable data structures.
- All fields are output regardless of their structure, ensuring comprehensive documentation.

---

## 8. PCAP Output Generation
### **Feature**
Generates a PCAP file for packet analysis in Wireshark.

### **How It Was Tested**
- Confirmed creation of `2_output.pcap` after parser run.
- Validated that the file is non-empty and can be opened in Wireshark.

### **Process & Logic**
- The parser converts supported log messages into PCAP format.
- PCAP output enables advanced analysis and visualization in external tools.

---

## 9. Timestamp and Radio ID Tracking
### **Feature**
Tracks and outputs precise timestamps and radio IDs for all parsed events.

### **How It Was Tested**
- Verified presence of timestamps and radio IDs in both JSON and TXT outputs for all events.

### **Process & Logic**
- The parser records the timestamp and radio ID for each message as it is processed.
- This enables correlation and time-based analysis of cellular events.

---

## 10. Human-Readable Reporting
### **Feature**
Generates a comprehensive, human-readable TXT report with clear formatting, section headers, and parsed values.

### **How It Was Tested**
- Inspected `2_output.txt` for readability, structure, and completeness.

### **Process & Logic**
- TXT writer formats each parsed event with headers, separators, and explicit field values.
- Ensures analysts can quickly interpret results without needing to parse raw JSON.

---

## Conclusion
All features were tested using a real QMDL2 file and validated for correctness, robustness, and completeness. The parser and output writers now reliably handle all expected and unexpected data structures, providing both machine-readable and human-readable outputs for advanced cellular log analysis.

---

*For further details or specific field explanations, refer to the full output files or request additional breakdowns.*
