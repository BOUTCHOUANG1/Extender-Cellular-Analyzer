#!/usr/bin/env python3
"""
Post-process an existing TXT produced by the parser and reformat event blocks to match example.txt layout.
- Ensures event summary indentation uses a literal tab
- Wraps payload bytes into 16-byte chunks
- Pads payload lines to a fixed column to match trailing-space behavior
- Writes "\t\tPayload String = ..." on the next line (even if empty)

Usage:
  python3 scripts/normalize_txt_to_example.py /tmp/Groupe1_output_analysis.txt /tmp/Groupe1_output_analysis_normalized.txt
"""
import re
import sys

if len(sys.argv) < 3:
    print("Usage: normalize_txt_to_example.py <in.txt> <out.txt>")
    sys.exit(2)

inf = sys.argv[1]
outf = sys.argv[2]

# target column (observed from example.txt)
TARGET_COL = 174

# regexes
header_re = re.compile(r'^(\d{4} \w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\.\d{3}.*Event  --  )(.+)$')
indented_event_re = re.compile(r'^\t(?P<time>\d{2}:\d{2}:\d{2}\.\d{3}) Event\s+0 : (?P<name>.+?) \(ID=(?P<id>\d+)\)\s+Payload = (?P<payload>.*)$')
payload_only_re = re.compile(r'^(0x)?(?P<hex>[-0-9A-Fa-f xX]+)')

blocks = []
with open(inf, 'r', encoding='utf-8', errors='replace') as f:
    data = f.read()

# Split into blank-line separated blocks
parts = re.split(r'\n\s*\n', data)

for part in parts:
    if 'Event  --' in part:
        # try to find the header line and the indented payload line
        lines = part.splitlines()
        header_line = None
        indented_line = None
        payload_string_line = ''
        other_lines = []
        for i,ln in enumerate(lines):
            if 'Event  --' in ln and header_line is None:
                header_line = ln
            if (ln.startswith('\t') or ln.lstrip().startswith('Event')) and 'Payload =' in ln and indented_line is None:
                indented_line = ln
            # capture payload string from anywhere in the block
            if 'Payload String = ' in ln:
                payload_string_line = ln.split('Payload String = ',1)[1].rstrip('\n')
        if header_line and indented_line:
            m = indented_event_re.match(indented_line)
            if m:
                time = m.group('time')
                name = m.group('name')
                idnum = int(m.group('id'))
                raw_payload = m.group('payload').strip()
                # extract hex bytes
                toks = re.findall(r'[0-9A-Fa-f]{2}', raw_payload)
                # build 16-byte chunks
                chunks = []
                for i in range(0, len(toks), 16):
                    chunk = toks[i:i+16]
                    if i == 0:
                        chunks.append('0x' + ' '.join(chunk))
                    else:
                        chunks.append(' '.join(chunk))
                # if no payload bytes, keep empty list
                # normalize payload string
                payload_str = payload_string_line if payload_string_line is not None else ''
                blocks.append((header_line, time, name, idnum, chunks, payload_str))
                continue
    # else, skip or keep for later

# Now produce output file by walking original file but replacing event blocks with formatted ones
out_lines = []
with open(inf, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

i = 0
bidx = 0
while i < len(lines):
    ln = lines[i]
    if 'Event  --' in ln and bidx < len(blocks):
        # write header line from block
        header_line, time, name, idnum, chunks, payload_str = blocks[bidx]
        out_lines.append(header_line.rstrip('\n') + '\n')
        # summary prefix
        summary_prefix = f"\t{time} Event  0 : {name} (ID={idnum})  Payload = "
        if chunks:
            first = chunks[0]
            total_len = len(summary_prefix) + len(first)
            if total_len < TARGET_COL:
                pad = TARGET_COL - total_len
                out_lines.append(f"{summary_prefix}{first}{' ' * pad}\n")
            else:
                out_lines.append(f"{summary_prefix}{first}\n")
            cont_indent = ' ' * len(summary_prefix)
            for pl in chunks[1:]:
                total_len = len(cont_indent) + len(pl)
                if total_len < TARGET_COL:
                    pad = TARGET_COL - total_len
                    out_lines.append(f"{cont_indent}{pl}{' ' * pad}\n")
                else:
                    out_lines.append(f"{cont_indent}{pl}\n")
        else:
            out_lines.append(f"{summary_prefix}\n")
        # Payload String line (two tabs)
        out_lines.append(f"\t\tPayload String = {payload_str}\n")
        out_lines.append('\n')
        # advance i forward until after this event block in original file
        # find next blank line
        while i < len(lines) and lines[i].strip() != '':
            i += 1
        # skip the blank line too
        while i < len(lines) and lines[i].strip() == '':
            i += 1
        bidx += 1
    else:
        out_lines.append(ln)
        i += 1

with open(outf, 'w', encoding='utf-8', errors='replace') as fo:
    fo.writelines(out_lines)

print('Wrote normalized file to', outf)
