# Live Capture Guide

Complete guide for capturing cellular logs in real-time from Qualcomm devices using USB or Serial connections.

---

## Prerequisites

### Hardware
- Qualcomm-based device with diagnostic mode enabled
- USB cable or Serial adapter
- Computer with USB port

### Software
- Python 3.8+
- libusb (Linux/macOS) or libusb-1.0.dll (Windows)
- Virtual environment activated

---

## Quick Start

### Ubuntu/Linux

#### USB Capture
```bash
# 1. Activate virtual environment
cd /path/to/Extender-Cellular-Analyzer
source venv/bin/activate

# 2. Check USB device is detected
lsusb | grep -i qualcomm

# 3. Add user to dialout group (one-time setup)
sudo usermod -a -G dialout $USER
# Logout and login for group change to take effect

# 4. Start live capture
cd qmdl-offline-parser/src
python3 -m scat.main -t qc -u \
    --events --msgs \
    --txt-file live_capture.txt \
    --json-file live_capture.json \
    -F live_capture.pcap
```

#### Serial Capture
```bash
# 1. Find serial port
ls /dev/ttyUSB* /dev/ttyACM*

# 2. Start capture
python3 -m scat.main -t qc -s /dev/ttyUSB0 -b 115200 \
    --events --msgs \
    --txt-file serial_capture.txt
```

### Windows

#### USB Capture
```powershell
# 1. Activate virtual environment
cd C:\path\to\Extender-Cellular-Analyzer
venv\Scripts\activate

# 2. Install libusb (one-time setup)
# Download from https://libusb.info/
# Copy libusb-1.0.dll to C:\Windows\System32

# 3. Start live capture (Run as Administrator)
cd qmdl-offline-parser\src
python -m scat.main -t qc -u ^
    --events --msgs ^
    --txt-file live_capture.txt ^
    --json-file live_capture.json ^
    -F live_capture.pcap
```

#### Serial Capture
```powershell
# 1. Find COM port in Device Manager
# Look under "Ports (COM & LPT)"

# 2. Start capture
python -m scat.main -t qc -s COM3 -b 115200 ^
    --events --msgs ^
    --txt-file serial_capture.txt
```

### macOS

#### USB Capture
```bash
# 1. Install libusb (one-time setup)
brew install libusb

# 2. Activate virtual environment
cd /path/to/Extender-Cellular-Analyzer
source venv/bin/activate

# 3. Start live capture
cd qmdl-offline-parser/src
python3 -m scat.main -t qc -u \
    --events --msgs \
    --txt-file live_capture.txt \
    --json-file live_capture.json \
    -F live_capture.pcap
```

#### Serial Capture
```bash
# 1. Find serial port
ls /dev/cu.* /dev/tty.*

# 2. Start capture
python3 -m scat.main -t qc -s /dev/cu.usbserial-1234 -b 115200 \
    --events --msgs \
    --txt-file serial_capture.txt
```

---

## Device Setup

### Enabling Diagnostic Mode

#### Qualcomm Devices (General)
```bash
# Via ADB (if device supports)
adb shell setprop sys.usb.config diag,adb

# Or dial code on device
*#*#3424#*#*  # Samsung
*#*#7378423#*#*  # Sony
##3424#  # LG
```

#### Checking Diagnostic Mode
```bash
# Linux
lsusb | grep -i qualcomm
# Should show: Qualcomm, Inc. Gobi Wireless Modem

# Windows
# Check Device Manager > Ports (COM & LPT)
# Should show: Qualcomm HS-USB Diagnostics

# macOS
system_profiler SPUSBDataType | grep -i qualcomm
```

---

## Command Reference

### Basic USB Capture
```bash
python3 -m scat.main -t qc -u --events --txt-file output.txt
```

### Basic Serial Capture
```bash
python3 -m scat.main -t qc -s /dev/ttyUSB0 --events --txt-file output.txt
```

### All Output Formats
```bash
python3 -m scat.main -t qc -u \
    --events --msgs \
    --txt-file live.txt \
    --json-file live.json \
    -F live.pcap
```

### Specific Protocol Layers
```bash
# Only RRC and NAS
python3 -m scat.main -t qc -u --events -L rrc -L nas -F live.pcap

# Only MAC layer
python3 -m scat.main -t qc -u -L mac -F live.pcap
```

### Custom Serial Settings
```bash
# Custom baudrate
python3 -m scat.main -t qc -s /dev/ttyUSB0 -b 921600 --events --txt-file output.txt

# Disable flow control
python3 -m scat.main -t qc -s /dev/ttyUSB0 --no-rts --no-dsr --events --txt-file output.txt
```

### Specific USB Device
```bash
# By vendor and product ID
python3 -m scat.main -t qc -u -v 0x05c6 -p 0x9091 --events --txt-file output.txt
```

---

## Real-World Examples

### Example 1: Quick USB Capture
```bash
# Capture events to TXT file
cd qmdl-offline-parser/src
python3 -m scat.main -t qc -u --events --txt-file quick_capture.txt

# Press Ctrl+C to stop
# Output: quick_capture.txt with decoded events
```

### Example 2: Comprehensive Capture
```bash
# Capture everything with all formats
python3 -m scat.main -t qc -u \
    --events --msgs \
    --txt-file comprehensive.txt \
    --json-file comprehensive.json \
    -F comprehensive.pcap

# Outputs:
# - comprehensive.txt (human-readable)
# - comprehensive.json (structured data)
# - comprehensive.pcap (Wireshark analysis)
```

### Example 3: Serial Modem Capture
```bash
# Capture from USB modem on serial port
python3 -m scat.main -t qc -s /dev/ttyUSB0 -b 115200 \
    --events --msgs \
    --txt-file modem_capture.txt \
    -F modem_capture.pcap
```

### Example 4: Long-Term Monitoring
```bash
# Capture to rotating files (manual rotation)
# Session 1
python3 -m scat.main -t qc -u --events --txt-file session1.txt

# Stop with Ctrl+C, then start Session 2
python3 -m scat.main -t qc -u --events --txt-file session2.txt
```

---

## Troubleshooting

### USB Device Not Found

**Linux:**
```bash
# Check if device is detected
lsusb | grep -i qualcomm

# Check permissions
ls -l /dev/bus/usb/*/*

# Add user to dialout group
sudo usermod -a -G dialout $USER
# Logout and login

# Or create udev rule
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="05c6", MODE="0666"' | \
    sudo tee /etc/udev/rules.d/51-qualcomm.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Windows:**
```powershell
# Check Device Manager
devmgmt.msc

# Install Qualcomm USB driver if needed
# Download from device manufacturer

# Run as Administrator
# Right-click PowerShell > Run as Administrator
```

**macOS:**
```bash
# Check USB devices
system_profiler SPUSBDataType | grep -i qualcomm

# Install libusb if not installed
brew install libusb
```

### Permission Denied

**Linux:**
```bash
# Temporary fix (until reboot)
sudo chmod 666 /dev/ttyUSB0

# Permanent fix
sudo usermod -a -G dialout $USER
# Logout and login
```

**Windows:**
```powershell
# Run PowerShell as Administrator
# Right-click > Run as Administrator
```

### No Data Captured

**Check diagnostic mode:**
```bash
# Linux
lsusb -v | grep -A 5 "Qualcomm"

# Verify device is in diagnostic mode, not just charging
```

**Check baudrate (Serial):**
```bash
# Try different baudrates
python3 -m scat.main -t qc -s /dev/ttyUSB0 -b 115200 --events --txt-file test.txt
python3 -m scat.main -t qc -s /dev/ttyUSB0 -b 921600 --events --txt-file test.txt
```

**Enable debug output:**
```bash
# Add -D flag for debug information
python3 -m scat.main -t qc -u -D --events --txt-file debug.txt
```

### libusb Error

**Linux:**
```bash
# Install libusb
sudo apt install libusb-1.0-0 libusb-1.0-0-dev

# Check if installed
ldconfig -p | grep libusb
```

**Windows:**
```powershell
# Download libusb from https://libusb.info/
# Extract and copy libusb-1.0.dll to:
# - C:\Windows\System32 (64-bit)
# - C:\Windows\SysWOW64 (32-bit on 64-bit Windows)
```

**macOS:**
```bash
# Install via Homebrew
brew install libusb

# Verify installation
brew list libusb
```

### Serial Port Access Denied

**Linux:**
```bash
# Check current groups
groups

# Add to dialout group
sudo usermod -a -G dialout $USER

# Or use sudo (not recommended for long-term)
sudo python3 -m scat.main -t qc -s /dev/ttyUSB0 --events --txt-file output.txt
```

**Windows:**
```powershell
# Check COM port in Device Manager
# Ensure no other application is using the port
# Close PuTTY, HyperTerminal, etc.
```

---

## Advanced Usage

### TCP Server Mode
```bash
# Start TCP server on port 5000
python3 -m scat.main -t qc --live-tcp 5000 --live-host 0.0.0.0 \
    --events --txt-file tcp_capture.txt

# From another machine, forward data:
# socat /dev/ttyUSB0,b115200 TCP:server-ip:5000
```

### Stdin Pipe Mode
```bash
# Pipe from another tool
other-diag-tool | python3 -m scat.main -t qc --live-stdin \
    --events --txt-file piped_capture.txt
```

### Filtering Specific Messages
```bash
# Only capture RRC and NAS layers
python3 -m scat.main -t qc -u -L rrc -L nas \
    --events -F filtered.pcap
```

---

## Output Files

### During Live Capture

**TXT File:**
- Real-time human-readable output
- Events, QMI, RUIM, CM messages
- QCAT-style formatting

**JSON File:**
- Structured data
- Complete message information
- Suitable for automation

**PCAP File:**
- Wireshark-compatible
- GSMTAP encapsulation
- Protocol analysis

### Stopping Capture

Press **Ctrl+C** to stop capture gracefully. Files will be properly closed and saved.

---

## Performance Tips

### For Long Captures
```bash
# Use only necessary output formats
python3 -m scat.main -t qc -u --events --txt-file output.txt

# Or only PCAP for Wireshark analysis
python3 -m scat.main -t qc -u -F output.pcap
```

### For High-Speed Devices
```bash
# Increase serial baudrate
python3 -m scat.main -t qc -s /dev/ttyUSB0 -b 921600 --events --txt-file output.txt
```

### For Minimal Overhead
```bash
# Capture only specific layers
python3 -m scat.main -t qc -u -L rrc -F output.pcap
```

---

## Verification

### Check Capture is Working
```bash
# In another terminal, monitor output file
tail -f live_capture.txt

# Should see messages appearing in real-time
```

### Verify USB Connection
```bash
# Linux
lsusb -t

# Check dmesg for USB events
dmesg | tail -20
```

### Test Serial Connection
```bash
# Linux - check serial port
ls -l /dev/ttyUSB*

# Test with screen (Ctrl+A then K to exit)
screen /dev/ttyUSB0 115200
```

---

## Summary

### Quick Commands

**USB Capture (Linux/macOS):**
```bash
python3 -m scat.main -t qc -u --events --txt-file output.txt
```

**USB Capture (Windows):**
```powershell
python -m scat.main -t qc -u --events --txt-file output.txt
```

**Serial Capture:**
```bash
python3 -m scat.main -t qc -s /dev/ttyUSB0 -b 115200 --events --txt-file output.txt
```

**All Formats:**
```bash
python3 -m scat.main -t qc -u --events --msgs --txt-file out.txt --json-file out.json -F out.pcap
```

---

## Support

For issues:
1. Check device is in diagnostic mode
2. Verify USB/Serial connection
3. Check permissions (Linux)
4. Run as Administrator (Windows)
5. Enable debug output with -D flag
6. Check docs/ for more information
