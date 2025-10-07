#!/usr/bin/env python3
"""
Enhanced QMDL Parser Script
Parses QMDL files and extracts maximum information to JSON and TXT formats
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path so we can import scat modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def main():
    parser = argparse.ArgumentParser(description='Enhanced QMDL Parser - Extract maximum information from QMDL files')
    parser.add_argument('qmdl_file', help='Path to the QMDL file to parse')
    parser.add_argument('--output-prefix', help='Output file prefix (default: same as input file)', type=str)
    parser.add_argument('--json-only', action='store_true', help='Only create JSON output')
    parser.add_argument('--txt-only', action='store_true', help='Only create TXT output') 
    parser.add_argument('--pcap', action='store_true', help='Also create PCAP file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.qmdl_file):
        print(f"Error: QMDL file {args.qmdl_file} not found")
        sys.exit(1)
        
    # Determine output prefix
    if args.output_prefix:
        output_prefix = args.output_prefix
    else:
        output_prefix = Path(args.qmdl_file).stem
        
    print("="*60)
    print("QMDL Offline Parser")
    print("="*60)
    print(f"Input file: {args.qmdl_file}")
    print(f"Output prefix: {output_prefix}")
    print()
    
    # Import and run parser directly
    try:
        import scat.iodevices
        import scat.parsers.qualcomm.qualcommparser
        import scat.writers.jsonwriter
        import scat.writers.txtwriter
        if args.pcap:
            import scat.writers.pcapwriter
            
        print("✅ Modules imported successfully")
        
        # Create writers based on options
        writers = []
        
        if not args.txt_only:
            json_file = f"{output_prefix}_parsed.json"
            json_writer = scat.writers.jsonwriter.JsonWriter(json_file)
            json_writer.set_input_filename(args.qmdl_file)
            writers.append(json_writer)
            print(f"Will create: {json_file}")
            
        if not args.json_only:
            txt_file = f"{output_prefix}_analysis.txt"
            txt_writer = scat.writers.txtwriter.TxtWriter(txt_file)
            txt_writer.set_input_filename(args.qmdl_file)
            writers.append(txt_writer)
            print(f"Will create: {txt_file}")
            
        if args.pcap:
            pcap_file = f"{output_prefix}.pcap"
            pcap_writer = scat.writers.pcapwriter.PcapWriter()
            pcap_writer.set_writer_pcap(pcap_file)
            writers.append(pcap_writer)
            print(f"Will create: {pcap_file}")
            
        if not writers:
            print("Error: No output format specified")
            sys.exit(1)
            
        print()
        print("🚀 Starting QMDL analysis...")
        
        # Create composite writer if multiple outputs
        if len(writers) == 1:
            writer = writers[0]
        else:
            # Create composite writer
            class CompositeWriter:
                def __init__(self, writers):
                    self.writers = writers
                    
                def write_cp(self, sock_content, radio_id, ts):
                    for w in self.writers:
                        if hasattr(w, 'write_cp'):
                            w.write_cp(sock_content, radio_id, ts)
                        elif hasattr(w, 'write_cp_start'):
                            w.write_cp_start(sock_content, radio_id, ts)
                            
                def write_up(self, sock_content, radio_id, ts):
                    for w in self.writers:
                        if hasattr(w, 'write_up'):
                            w.write_up(sock_content, radio_id, ts)
                        elif hasattr(w, 'write_up_start'):
                            w.write_up_start(sock_content, radio_id, ts)
                            
                def write_parsed_data(self, parsed_result, radio_id, ts):
                    for w in self.writers:
                        if hasattr(w, 'write_parsed_data'):
                            w.write_parsed_data(parsed_result, radio_id, ts)
                            
                def write_stdout_data(self, stdout_text, radio_id, ts):
                    for w in self.writers:
                        if hasattr(w, 'write_stdout_data'):
                            w.write_stdout_data(stdout_text, radio_id, ts)
                            
                def close(self):
                    for w in self.writers:
                        if hasattr(w, 'close'):
                            w.close()
                        elif hasattr(w, 'writeln_final'):
                            w.writeln_final()
                            
            writer = CompositeWriter(writers)
            
            writer = CompositeWriter(writers)
        
        # Create file IO and parser
        io_device = scat.iodevices.FileIO([args.qmdl_file])
        qualcomm_parser = scat.parsers.qualcomm.qualcommparser.QualcommParser()
        
        # Configure parser
        qualcomm_parser.set_io_device(io_device)
        qualcomm_parser.set_writer(writer)
        qualcomm_parser.set_parameter({
            'log_level': 10 if args.debug else 20,  # DEBUG or INFO level
            'events': True,
            'msgs': True,
            'cacombos': True,
            'layer': ['ip', 'nas', 'rrc', 'pdcp', 'rlc', 'mac', 'qmi'],
            'format': 'x',
            'gsmtapv3': False
        })
        
        # Parse the file
        qualcomm_parser.read_dump()
        
        # Close writers
        writer.close()
        
        print("✅ Parsing completed successfully!")
        print()
        
        # Show output file statistics
        for writer_obj in (writers if len(writers) > 1 else [writer]):
            if hasattr(writer_obj, 'json_filename') and os.path.exists(writer_obj.json_filename):
                size = os.path.getsize(writer_obj.json_filename)
                print(f"📄 JSON output: {writer_obj.json_filename} ({size:,} bytes)")
            elif hasattr(writer_obj, 'txt_filename') and os.path.exists(writer_obj.txt_filename):
                size = os.path.getsize(writer_obj.txt_filename)
                print(f"📄 TXT output: {writer_obj.txt_filename} ({size:,} bytes)")
                
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("Make sure you're running this script from the project directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
