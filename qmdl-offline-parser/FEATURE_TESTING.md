# QMDL Offline Parser (SCAT Fork) - Feature Testing & Documentation

## Project Goals
- Evaluate and document all features of the `qmdl-offline-parser` (SCAT fork), including advanced options.
- Provide clear, step-by-step instructions and explanations for each feature tested.
- Enable new contributors to quickly understand and use the tool.

## Steps Completed So Far

### 1. Repository Cloning
- Cloned the SCAT fork repository for offline QMDL analysis:
  ```bash
  git clone https://github.com/drinkingc0ffee/qmdl-offline-parser.git
  ```

### 2. Installation & Setup
- Fixed an installation issue due to an invalid version string in `pyproject.toml`.
- Updated the version string to comply with Python packaging standards (`1.4.0.post1`).
- Installed the package with fast CRC support for optimal performance:
  ```bash
  pip install -e ./qmdl-offline-parser[fastcrc]
  ```

## Next Steps
- Test and document each feature, including:
  - Output formats (JSON, TXT, PCAP)
  - Data extraction (cell info, signal measurements, protocol messages, network events, security data, carrier aggregation)
  - Supported technologies (5G NR, LTE/4G, WCDMA/3G, GSM/2G)
  - Device support and connection methods (USB, serial, file-based)
  - Advanced features (GSMTAPv3, Wireshark plugin)
- For each feature:
  - Run relevant commands
  - Record results and observations
  - Document the process, commands, and findings

---

## Documentation Structure
Each feature will be documented with:
- **Feature Name & Description**
- **Purpose & Use Case**
- **Step-by-Step Instructions**
- **Commands Used**
- **Results & Output Examples**
- **Troubleshooting & Tips**

---

*This document will be updated as testing progresses.*
