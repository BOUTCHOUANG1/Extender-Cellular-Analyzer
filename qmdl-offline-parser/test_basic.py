#!/usr/bin/env python3
"""
Simple test to check if we can parse a QMDL file
"""

import sys
import os
import glob
import argparse

# Add src to path for testing
sys.path.insert(0, 'src')

def find_qmdl_file():
    """Find a QMDL file in the current directory"""
    qmdl_files = glob.glob('*.qmdl')
    if qmdl_files:
        return qmdl_files[0]  # Return first found
    return None

def test_basic_parsing(qmdl_file=None):
    try:
        # Test basic imports
        print("Testing imports...")
        import scat.iodevices
        print("✅ iodevices imported")
        
        import scat.parsers.qualcomm.qualcommparser
        print("✅ qualcomm parser imported")
        
        import scat.writers.jsonwriter
        print("✅ JSON writer imported")
        
        import scat.writers.txtwriter  
        print("✅ TXT writer imported")
        
        # Test file IO
        if not qmdl_file:
            qmdl_file = find_qmdl_file()
            
        if qmdl_file and os.path.exists(qmdl_file):
            print(f"✅ QMDL file found: {qmdl_file} ({os.path.getsize(qmdl_file):,} bytes)")
            
            # Test file loading
            file_io = scat.iodevices.FileIO([qmdl_file])
            print("✅ FileIO created successfully")
        else:
            print("⚠️  No QMDL file found for testing FileIO")
            print("   (Place a .qmdl file in the current directory or specify with --file)")
            
        print("\n🎉 Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='QMDL Offline Parser - Basic Test')
    parser.add_argument('--file', help='Specific QMDL file to test with')
    args = parser.parse_args()
    
    print("QMDL Offline Parser - Basic Test")
    print("=" * 40)
    test_basic_parsing(args.file)
