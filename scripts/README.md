normalize_txt_to_example.py

Purpose
-------
This script post-processes an already-generated TXT output from the parser and rewrites event blocks to match the layout and whitespace conventions found in `example.txt`.

When to use
-----------
- You have a generated TXT (for example `/tmp/Groupe1_output_analysis.txt`) but do not have the original QMDL used to create `example.txt`.
- You want to visually/byte-match event block layout (tabs, trailing spaces, payload wrapping) for reporting or diffing against `example.txt`.

Usage
-----
```bash
python3 scripts/normalize_txt_to_example.py <in.txt> <out.txt>
```

Notes
-----
- The script is a deterministic post-processor and does not change the decoded payload bytes. It reorganizes the event block layout.
- For full byte-for-byte parity with `example.txt` across the whole file you still need the exact raw QMDL used to generate `example.txt`.

*** End of file
