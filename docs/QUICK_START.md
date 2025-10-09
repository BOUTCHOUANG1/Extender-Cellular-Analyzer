# Quick Start Guide

## Extender-Cellular-Analyzer - All-in-One Tool

One tool for everything: Live capture + Offline analysis + Enhanced outputs

---

## Installation (One Time)

```bash
cd Extender-Cellular-Analyzer
python3 -m venv venv
./venv/bin/pip install -e qmdl-offline-parser/.[fastcrc]
```

---

## Common Commands

### 1. List Connected USB Devices
```bash
./run_parser.sh -t qc -l
```

### 2. Live USB Capture
```bash
# Basic
./run_parser.sh -t qc -u -a 001:010 --json-file out.json --txt-file out.txt

# With all features
./run_parser.sh -t qc -u -a 001:010 \
  --events --msgs --cacombos \
  --qmdl raw.qmdl \
  --json-file data.json \
  --txt-file report.txt \
  --pcap-file wireshark.pcap
```

### 3. Serial Port Capture
```bash
# Basic
./run_parser.sh -t qc -s /dev/ttyUSB0 --json-file out.json --txt-file out.txt

# High-speed
./run_parser.sh -t qc -s /dev/ttyUSB0 -b 921600 --json-file out.json
```

### 4. Offline File Analysis
```bash
# Single file
./run_parser.sh -t qc -d file.qmdl2 --json-file out.json --txt-file out.txt

# Multiple files
./run_parser.sh -t qc -d file1.qmdl2 file2.qmdl2 --json-file out.json

# Samsung
./run_parser.sh -t sec -d file.sdm --json-file out.json
```

### 5. Get Help
```bash
./run_parser.sh --help
```

---

## Output Files

- **JSON** (`--json-file`): Machine-readable structured data
- **TXT** (`--txt-file`): Human-readable report with statistics
- **PCAP** (`--pcap-file`): Wireshark-compatible packet capture

---

## Baseband Types

- `-t qc` - Qualcomm
- `-t sec` - Samsung
- `-t hisi` - HiSilicon
- `-t sprd` - Unisoc/Spreadtrum

---

## Common Options

- `--events` - Decode events (Qualcomm)
- `--msgs` - Decode extended messages (Qualcomm)
- `--cacombos` - Show CA combos (Qualcomm)
- `-L ip,nas,rrc` - Select protocol layers
- `-D` - Debug mode (verbose)
- `-3` - Enable GSMTAPv3 for 2G/3G/4G

---

## Troubleshooting

### USB Permission Denied
```bash
sudo usermod -a -G plugdev $USER
# Logout and login
```

### Serial Port Access Denied
```bash
sudo usermod -a -G dialout $USER
# Logout and login
```

### ModemManager Conflicts
```bash
sudo systemctl stop ModemManager
sudo systemctl disable ModemManager
```

---

## Documentation

- **`ALL_IN_ONE_GUIDE.md`** - Complete guide
- **`MIGRATION_GUIDE.md`** - For SCAT users
- **`FINAL_SUMMARY.md`** - Quick reference
- **`README.md`** - Project overview

---

## Examples

### Field Testing
```bash
./run_parser.sh -t qc -u -a 001:010 \
  --events --msgs \
  --qmdl field_$(date +%Y%m%d).qmdl \
  --json-file field_data.json \
  --txt-file field_report.txt
```

### Lab Analysis
```bash
./run_parser.sh -t qc -d lab_capture.qmdl2 \
  --json-file analysis.json \
  --txt-file report.txt \
  --pcap-file wireshark.pcap
```

### Batch Processing
```bash
for file in *.qmdl2; do
  ./run_parser.sh -t qc -d "$file" --json-file "${file%.qmdl2}.json"
done
```

---

**That's it! You're ready to go.**

For detailed information, see `ALL_IN_ONE_GUIDE.md`
