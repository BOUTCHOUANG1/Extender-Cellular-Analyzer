#!/usr/bin/env python3
"""
Direct test of QMDL parsing functionality
"""

import sys
import os
import glob
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def find_qmdl_file():
    """Find a QMDL file in the current directory"""
    qmdl_files = glob.glob('*.qmdl')
    if qmdl_files:
        return qmdl_files[0]  # Return first found
    return None

def main(qmdl_file=None, output_prefix=None):
    print("🔍 QMDL Offline Parser - Direct Test")
    print("=" * 50)
    
    try:
        # Import required modules
        import scat.iodevices
        import scat.parsers.qualcomm.qualcommparser
        import scat.writers.jsonwriter
        import scat.writers.txtwriter
        
        # Determine input file
        if not qmdl_file:
            qmdl_file = find_qmdl_file()
            
        if not qmdl_file or not os.path.exists(qmdl_file):
            print(f"❌ QMDL file not found: {qmdl_file or 'No .qmdl files in directory'}")
            print("   Use --file to specify a QMDL file or place one in the current directory")
            return False
            
        print(f"📁 Input file: {qmdl_file} ({os.path.getsize(qmdl_file):,} bytes)")
        
        # Determine output prefix
        if not output_prefix:
            output_prefix = Path(qmdl_file).stem + "_test"
        
        # Create output writers
        json_file = f"{output_prefix}.json"
        txt_file = f"{output_prefix}.txt"
        
        json_writer = scat.writers.jsonwriter.JsonWriter(json_file)
        txt_writer = scat.writers.txtwriter.TxtWriter(txt_file)
        json_writer.set_input_filename(qmdl_file)
        txt_writer.set_input_filename(qmdl_file)
        
        # Create composite writer
        class CompositeWriter:
            def __init__(self, json_w, txt_w):
                self.json_writer = json_w
                self.txt_writer = txt_w
                
            def write_cp(self, sock_content, radio_id, ts):
                self.json_writer.write_cp(sock_content, radio_id, ts)
                self.txt_writer.write_cp(sock_content, radio_id, ts)
                
            def write_up(self, sock_content, radio_id, ts):
                self.json_writer.write_up(sock_content, radio_id, ts)
                self.txt_writer.write_up(sock_content, radio_id, ts)
                
            def write_parsed_data(self, parsed_result, radio_id, ts):
                self.json_writer.write_parsed_data(parsed_result, radio_id, ts)
                self.txt_writer.write_parsed_data(parsed_result, radio_id, ts)
                
            def write_stdout_data(self, stdout_text, radio_id, ts):
                self.json_writer.write_stdout_data(stdout_text, radio_id, ts)
                self.txt_writer.write_stdout_data(stdout_text, radio_id, ts)
                
            def close(self):
                self.json_writer.close()
                self.txt_writer.close()
        
        writer = CompositeWriter(json_writer, txt_writer)
        
        # Create file IO and parser
        io_device = scat.iodevices.FileIO([qmdl_file])
        parser = scat.parsers.qualcomm.qualcommparser.QualcommParser()
        
        # Configure parser
        parser.set_io_device(io_device)
        parser.set_writer(writer)
        parser.set_parameter({
            'log_level': 20,  # INFO level
            'events': True,
            'msgs': True,
            'cacombos': True,
            'layer': ['ip', 'nas', 'rrc', 'pdcp', 'rlc', 'mac', 'qmi'],
            'format': 'x',
            'gsmtapv3': False
        })
        
        print("🚀 Starting QMDL analysis...")
        
        # Parse the file
        parser.read_dump()
        
        # Close writers
        writer.close()
        
        print("✅ Analysis completed successfully!")
        print(f"📄 JSON output: {json_file}")
        print(f"📄 TXT output: {txt_file}")
        
        # Show some stats
        if os.path.exists(json_file):
            json_size = os.path.getsize(json_file)
            print(f"📊 JSON file size: {json_size:,} bytes")
            
        if os.path.exists(txt_file):
            txt_size = os.path.getsize(txt_file)
            print(f"📊 TXT file size: {txt_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='QMDL Offline Parser - Direct Test')
    parser.add_argument('--file', help='Specific QMDL file to test with')
    parser.add_argument('--output-prefix', help='Output file prefix (default: <filename>_test)')
    args = parser.parse_args()
    
    main(args.file, args.output_prefix)
