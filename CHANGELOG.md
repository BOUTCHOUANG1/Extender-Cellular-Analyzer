# Changelog

All notable changes to this repository should be documented in this file.

## 2025-10-08 - Formatting & decoder improvements
- Updated `qmdl-offline-parser/src/scat/writers/txtwriter.py` to better match `example.txt` layout:
  - Use literal tabs for event summary lines.
  - Timestamp formatting adjusted to match example month/day spacing.
  - Payload bytes wrapped at 16 bytes and padded to a target column to reproduce trailing spaces.
  - `Payload String` always emitted on the next line with two literal tabs.
  - Added `force_example_header` capability to optionally force header hex value (0x1FFB).
- Hardened Qualcomm event parsing and decoders:
  - Added/verified decoders for event IDs 2865 (QSHRINK) and 2866 (PROCESS_NAME) to populate `payload_str`.
  - Defensive parsing fixes in `qualcommparser.py` to avoid struct.unpack errors on truncated inputs.
- Added `scripts/normalize_txt_to_example.py` to post-process generated TXT files to example-style formatting when exact input data is not available.
- Added/updated unit tests for event decoders (see `qmdl-offline-parser/tests/`).

## Notes
- These changes focus on formatting parity with a provided `example.txt` file. Exact byte-for-byte parity for the whole TXT requires the original raw QMDL input that produced `example.txt`.
