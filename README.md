# Extender Cellular Analyzer

**All-in-One Cellular Log Analysis Tool**

Comprehensive tool for parsing and analyzing Qualcomm QMDL diagnostic logs with live USB/Serial capture support and offline analysis capabilities. Combines SCAT v1.4.0 live capture features with enhanced offline parsing.

---

## Features

✅ **Live Capture**
- USB device capture (Qualcomm diagnostic mode)
- Serial port capture with configurable baudrate
- Real-time log streaming

✅ **Offline Analysis**
- QMDL/DLF/HDF file parsing
- Batch processing support
- Multiple file formats

✅ **Comprehensive Output Formats**
- **TXT**: QCAT-style human-readable output with full message decoding
- **JSON**: Structured data for automation and analysis
- **PCAP**: Wireshark-compatible capture for protocol analysis

✅ **Advanced Decoding**
- Events with full QCAT formatting
- QMI messages with TLV parsing and service name mapping
- RUIM/APDU commands with full decoding
- CM Phone Events with detailed field extraction
- RRC/NAS/MAC protocol messages
- LTE/5G NR support

---

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- libusb (for USB capture on Linux/macOS)

### Installation

#### Ubuntu/Debian Linux
```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv libusb-1.0-0

# Clone repository
cd /path/to/your/workspace
git clone <repository-url>
cd Extender-Cellular-Analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r qmdl-offline-parser/requirements.txt
```

#### Windows
```powershell
# Install Python 3.8+ from https://www.python.org/downloads/
# Make sure to check "Add Python to PATH" during installation

# Clone repository
cd C:\path\to\your\workspace
git clone <repository-url>
cd Extender-Cellular-Analyzer

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install Python dependencies
pip install -r qmdl-offline-parser\requirements.txt

# For USB capture, install libusb:
# Download from https://libusb.info/ and place libusb-1.0.dll in System32
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 libusb

# Clone repository
cd /path/to/your/workspace
git clone <repository-url>
cd Extender-Cellular-Analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r qmdl-offline-parser/requirements.txt
```

### Basic Usage

#### Offline Analysis (QMDL File)
```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Parse QMDL file with all output formats
cd qmdl-offline-parser/src
python3 -m scat.main -t qc -d /path/to/logfile.qmdl2 \
    --events --msgs \
    --txt-file output.txt \
    --json-file output.json \
    -F output.pcap
```

#### Live USB Capture
```bash
# Linux/macOS
python3 -m scat.main -t qc -u \
    --events --msgs \
    --txt-file live_capture.txt

# Windows (Run as Administrator)
python -m scat.main -t qc -u ^
    --events --msgs ^
    --txt-file live_capture.txt

# Note: See docs/LIVE_CAPTURE_GUIDE.md for detailed setup
```

#### Live Serial Capture
```bash
# Linux/macOS
python3 -m scat.main -t qc -s /dev/ttyUSB0 -b 115200 \
    --events --msgs \
    --txt-file serial_capture.txt

# Windows
python -m scat.main -t qc -s COM3 -b 115200 ^
    --events --msgs ^
    --txt-file serial_capture.txt
```

---

## Command Line Options

### Required Arguments
- `-t, --type {qc,hisi,sec,sprd}` - Parser type (use `qc` for Qualcomm)

### Input Sources (choose one)
- `-d, --dump [FILE ...]` - Offline QMDL/DLF/HDF files
- `-u, --usb` - Live USB capture
- `-s, --serial PORT` - Live serial capture
- `--live-tcp PORT` - TCP server mode

### Output Options
- `--txt-file FILE` - Human-readable TXT output (QCAT format)
- `--json-file FILE` - Structured JSON output
- `-F, --pcap-file FILE` - PCAP output for Wireshark

### Decoding Options
- `--events` - Decode events
- `--msgs` - Decode extended messages
- `-L, --layer {rrc,nas,mac,pdcp,ip}` - Specific protocol layers

### Serial Options
- `-b, --baudrate RATE` - Baudrate (default: 115200)
- `--no-rts` - Disable RTS flow control
- `--no-dsr` - Disable DSR flow control

### USB Options
- `-v, --vendor ID` - USB vendor ID
- `-p, --product ID` - USB product ID

---

## Output Formats

### TXT Format (QCAT-Style)
Human-readable output with comprehensive message decoding:
- Events with timestamps, thread IDs, and payload strings
- QMI messages with service names and TLV parsing
- RUIM/APDU commands with full decoding
- CM Phone Events with detailed fields

**Best for:** Quick review, debugging, sharing reports

### JSON Format
Structured data with complete information:
```json
{
  "file_info": {...},
  "summary": {
    "total_messages": 55433,
    "cellular_messages": 8729
  },
  "cell_info": [...],
  "measurements": [...],
  "events": [...]
}
```

**Best for:** Automation, data mining, integration with other tools

### PCAP Format
Wireshark-compatible capture with GSMTAP encapsulation:
- RRC/NAS/MAC protocol messages
- Layer 2/3 analysis
- Protocol conformance testing

**Best for:** Deep protocol analysis, Wireshark inspection

---

## Examples

### Example 1: Quick Analysis
```bash
# Parse QMDL and generate TXT output
python3 -m scat.main -t qc -d logfile.qmdl2 --events --txt-file output.txt
```

### Example 2: Comprehensive Analysis
```bash
# Generate all output formats
python3 -m scat.main -t qc -d logfile.qmdl2 \
    --events --msgs \
    --txt-file analysis.txt \
    --json-file analysis.json \
    -F analysis.pcap
```

### Example 3: Live Capture with Filtering
```bash
# Capture only RRC and NAS layers
python3 -m scat.main -t qc -u \
    --events -L rrc -L nas \
    --txt-file live.txt \
    -F live.pcap
```

### Example 4: Batch Processing
```bash
# Process multiple files
python3 -m scat.main -t qc -d *.qmdl2 \
    --events --msgs \
    --json-file batch_output.json
```

---

## Troubleshooting

### USB Permission Issues (Linux)
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or create udev rule
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="05c6", MODE="0666"' | \
    sudo tee /etc/udev/rules.d/51-android.rules
sudo udevadm control --reload-rules
```

### Module Not Found Error
```bash
# Make sure you're in the correct directory
cd qmdl-offline-parser/src

# And virtual environment is activated
source ../../venv/bin/activate  # Linux/macOS
..\..\venv\Scripts\activate     # Windows
```

### libusb Not Found (Windows)
1. Download libusb from https://libusb.info/
2. Extract and copy `libusb-1.0.dll` to `C:\Windows\System32`
3. For 64-bit systems, also copy to `C:\Windows\SysWOW64`

### Serial Port Access Denied
```bash
# Linux: Add user to dialout group
sudo usermod -a -G dialout $USER

# Windows: Run as Administrator or check Device Manager
```

---

## Project Structure

```
Extender-Cellular-Analyzer/
├── qmdl-offline-parser/          # Main parser application
│   ├── src/scat/                 # Source code
│   │   ├── parsers/              # Protocol parsers
│   │   │   └── qualcomm/         # Qualcomm-specific parsers
│   │   ├── writers/              # Output format writers
│   │   ├── iodevices/            # I/O device handlers
│   │   └── main.py               # Entry point
│   ├── requirements.txt          # Python dependencies
│   └── pyproject.toml            # Project configuration
├── docs/                         # Documentation
│   ├── FULL_QCAT_PARITY_COMPLETE.md
│   ├── ALL_FORMATS_VERIFICATION.md
│   └── QUICK_START.md
├── venv/                         # Virtual environment (created during setup)
├── CHANGELOG.md                  # Version history
└── README.md                     # This file
```

---

## Dependencies

### Python Packages
- `bitstring>=3.1.7` - Binary data manipulation
- `libscrc>=1.8.0` - CRC calculations
- `packaging>=19.0` - Version parsing
- `pyusb>=1.0.2` - USB device access
- `pyserial>=3.3` - Serial port communication

### System Libraries
- `libusb-1.0` - USB device access (Linux/macOS)
- `libusb-1.0.dll` - USB device access (Windows)

---

## Documentation

Detailed documentation available in the `docs/` directory:

- **[LIVE_CAPTURE_GUIDE.md](docs/LIVE_CAPTURE_GUIDE.md)** - Complete live capture guide (USB/Serial)
- **[FULL_QCAT_PARITY_COMPLETE.md](docs/FULL_QCAT_PARITY_COMPLETE.md)** - Complete feature documentation
- **[ALL_FORMATS_VERIFICATION.md](docs/ALL_FORMATS_VERIFICATION.md)** - Output format details
- **[QUICK_START.md](docs/QUICK_START.md)** - Quick start guide
- **[PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Project overview

---

## Contributing

Contributions are welcome! Please ensure:
1. Code follows existing style
2. All tests pass
3. Documentation is updated
4. Commit messages are clear

---

## License

GPL-2.0-or-later

---

## Credits

- Based on SCAT v1.4.0 (https://github.com/fgsect/scat)
- Integrates features from Extender-Cellular-Analyzer
- Enhanced with comprehensive QCAT-style decoding

---

## Support

For issues, questions, or contributions:
1. Check the documentation in `docs/`
2. Review existing issues
3. Create a new issue with detailed information

---

## Version

**Current Version:** 2.0.0  
**Last Updated:** October 2025  
**Status:** Production Ready ✅
