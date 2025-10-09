
#!/usr/bin/env python3
# coding: utf8
"""
QMDL Offline Parser Main Entry Point

This script provides the command-line interface for offline analysis of Qualcomm diagnostic dumps.
It loads available parser modules, sets up argument parsing, and manages output writers.

Key functions:
- Loads all available parser modules
- Handles command-line arguments for selecting baseband type, output format, and debug options
- Manages signal handling for graceful termination
- Entry point for offline file analysis
"""

import scat.iodevices
import scat.writers
import scat.parsers

import argparse
import faulthandler
import importlib.metadata
import logging
import os, sys
import signal

current_parser = None
logger = logging.getLogger('qmdl-offline-parser')
__version__ = "1.4.0-offline"

if os.name != 'nt':
    faulthandler.register(signal.SIGUSR1)

def sigint_handler(signal, frame):
    global current_parser
    current_parser.stop_diag()
    sys.exit(0)

def hexint(string):
    if string[0:2] == '0x' or string[0:2] == '0X':
        return int(string[2:], 16)
    else:
        return int(string)

class ListUSBAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        scat.iodevices.USBIO().list_usb_devices()
        parser.exit()

def scat_main():
    global current_parser
    # Load parser modules
    parser_dict = {}
    for parser_module in dir(scat.parsers):
        if parser_module.startswith('__'):
            continue
        if type(getattr(scat.parsers, parser_module)) == type:
            c = getattr(scat.parsers, parser_module)()
            parser_dict[c.shortname] = c

    valid_layers = ['ip', 'nas', 'rrc', 'pdcp', 'rlc', 'mac', 'qmi']

    parser = argparse.ArgumentParser(description='Extender-Cellular-Analyzer - All-in-one tool for live capture and offline analysis of cellular diagnostic data')
    parser.register('action', 'listusb', ListUSBAction)

    parser.add_argument('-D', '--debug', help='Print debug information, mostly hexdumps.', action='store_true')
    parser.add_argument('-t', '--type', help='Baseband type to be parsed.\nAvailable types: {}'.format(', '.join(parser_dict.keys())), required=True, choices=list(parser_dict.keys()))
    parser.add_argument('-l', '--list-devices', help='List USB devices and exit', nargs=0, action='listusb')
    parser.add_argument('-V', '--version', action='version', version='Extender-Cellular-Analyzer v1.4.0+ (SCAT v1.4.0 + Enhanced Features)')
    parser.add_argument('-L', '--layer', help='Specify the layers to see as GSMTAP packets (comma separated).\nAvailable layers: {}, Default: "ip,nas,rrc"'.format(', '.join(valid_layers)), type=str, default='ip,nas,rrc')
    parser.add_argument('-f', '--format', help='Select display format for LAC/RAC/TAC/CID: [d]ecimal, he[x]adecimal (default), [b]oth.', type=str, default='x', choices=['d', 'x', 'b'])
    parser.add_argument('-3', '--gsmtapv3', help='Enable GSMTAPv3 for 2G/3G/4G. Default: enabled only for 5G NR', action='store_true')

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-s', '--serial', help='Use serial diagnostic port')
    input_group.add_argument('-u', '--usb', action='store_true', help='Use USB diagnostic port')
    input_group.add_argument('-d', '--dump', help='Read from baseband dump (QMDL, SDM, LPD)', nargs='*')
    input_group.add_argument('--live-stdin', help='Read raw DIAG HDLC stream from stdin for live parsing (experimental)', action='store_true')
    parser.add_argument('--live-tcp', help='Listen on TCP port and accept a single client for live parsing (e.g. --live-tcp 5000)', type=int)
    parser.add_argument('--live-host', help='Host/interface for --live-tcp to bind to (default: 127.0.0.1)', type=str, default='127.0.0.1')

    serial_group = parser.add_argument_group('Serial device settings')
    serial_group.add_argument('-b', '--baudrate', help='Set the serial baud rate', type=int, default=115200)
    serial_group.add_argument('--no-rts', action='store_true', help='Do not enable the RTS/CTS')
    serial_group.add_argument('--no-dsr', action='store_true', help='Do not enable the DSR/DTR')

    usb_group = parser.add_argument_group('USB device settings')
    usb_group.add_argument('-v', '--vendor', help='Specify USB vendor ID', type=hexint)
    usb_group.add_argument('-p', '--product', help='Specify USB product ID', type=hexint)
    usb_group.add_argument('-a', '--address', help='Specify USB device address(bus:address)', type=str)
    usb_group.add_argument('-c', '--config', help='Specify USB configuration number for DM port', type=int, default=-1)
    usb_group.add_argument('-i', '--interface', help='Specify USB interface number for DM port', type=int, default=2)

    if 'qc' in parser_dict.keys():
        qc_group = parser.add_argument_group('Qualcomm specific settings')
        qc_group.add_argument('--qmdl', help='Store log as QMDL file (Qualcomm only)')
        qc_group.add_argument('--qsr-hash', help='Specify QSR message hash file (usually QSRMessageHash.db), implies --msgs', type=str)
        qc_group.add_argument('--qsr4-hash', help='Specify QSR4 message hash file (need to obtain from the device firmware), implies --msgs', type=str)
        qc_group.add_argument('--events', action='store_true', help='Decode Events as GSMTAP logging')
        qc_group.add_argument('--msgs', action='store_true', help='Decode Extended Message Reports and QSR Message Reports as GSMTAP logging')
        qc_group.add_argument('--cacombos', action='store_true', help='Display raw values of UE CA combo information on 4G/5G (0xB0CD/0xB826)')
        qc_group.add_argument('--disable-crc-check', action='store_true', help='Disable CRC mismatch checks. Improves performance by avoiding CRC calculations.')

    if 'sec' in parser_dict.keys():
        sec_group = parser.add_argument_group('Samsung specific settings')
        sec_group.add_argument('-m', '--model', help='Override autodetected device model for analyzing diagnostic messages', type=str)
        sec_group.add_argument('--start-magic', help='Magic value provided for starting DM session. Default: 0x41414141', type=str, default='0x41414141')
        sec_group.add_argument('--sdmraw', help='Store log as raw SDM file (Samsung only)')
        sec_group.add_argument('--trace', action='store_true', help='Decode trace')
        sec_group.add_argument('--ilm', action='store_true', help='Decode ILM')
        sec_group.add_argument('--all-items', action='store_true', help='Enable all SDM items')


    if 'hisi' in parser_dict.keys():
        hisi_group = parser.add_argument_group('HiSilicon specific settings')
        try:
            hisi_group.add_argument('--msgs', action='store_true', help='Decode debug messages GSMTAP logging')
            hisi_group.add_argument('--disable-crc-check', action='store_true', help='Disable CRC mismatch checks. Improves performance by avoiding CRC calculations.')
        except argparse.ArgumentError:
            pass

    ip_group = parser.add_argument_group('GSMTAP IP settings')
    ip_group.add_argument('-P', '--port', help='Change UDP port to emit GSMTAP packets', type=int, default=4729)
    ip_group.add_argument('--port-up', help='Change UDP port to emit user plane packets', type=int, default=47290)
    ip_group.add_argument('-H', '--hostname', help='Change base host name/IP to emit GSMTAP packets. For dual SIM devices the subsequent IP address will be used.', type=str, default='127.0.0.1')

    ip_group.add_argument('-F', '--pcap-file', help='Write GSMTAP packets directly to specified PCAP file')
    ip_group.add_argument('-C', '--combine-stdout', action='store_true', help='Write standard output messages as osmocore log file, along with other GSMTAP packets.')
    
    # Enhanced output formats
    output_group = parser.add_argument_group('Enhanced output formats')
    output_group.add_argument('--json-file', help='Write structured data to JSON file', type=str)
    output_group.add_argument('--txt-file', help='Write human-readable analysis to TXT file', type=str)
    output_group.add_argument('--preserve-intermediate', action='store_true', help='Keep intermediate PCAP files when using JSON/TXT output')

    args = parser.parse_args()

    GSMTAP_IP = args.hostname
    GSMTAP_PORT = args.port
    IP_OVER_UDP_PORT = args.port_up

    if not args.type in parser_dict.keys():
        print('Error: invalid baseband type {} specified. Available modules: {}'.format(args.type, ', '.join(parser_dict.keys())))
        sys.exit(1)

    layers = args.layer.split(',')
    for l in layers:
        if not l in valid_layers:
            print('Error: invalid layer {} specified. Available layers: {}'.format(l, ', '.join(valid_layers)))
            sys.exit(1)

    # Device preparation
    io_device = None
    if args.serial:
        io_device = scat.iodevices.SerialIO(args.serial, args.baudrate, not args.no_rts, not args.no_dsr)
    elif args.usb:
        io_device = scat.iodevices.USBIO()
        if args.address:
            usb_bus, usb_device = args.address.split(':')
            usb_bus = int(usb_bus, base=10)
            usb_device = int(usb_device, base=10)
            io_device.probe_device_by_bus_dev(usb_bus, usb_device)
        elif args.vendor == None:
            io_device.guess_device()
        else:
            io_device.probe_device_by_vid_pid(args.vendor, args.product)

        if args.config > 0:
            io_device.set_configuration(args.config)
        io_device.claim_interface(args.interface)
    elif args.dump:
        io_device = scat.iodevices.FileIO(args.dump)
    elif args.live_stdin:
        # Use live stdin reader (blocks until stdin closes)
        io_device = scat.iodevices.LiveStdinIO()
    elif args.live_tcp is not None:
        # Create a LiveTcpIO listening on the requested interface/port
        io_device = scat.iodevices.LiveTcp(listen_addr=args.live_host, listen_port=args.live_tcp)
    else:
        print('Error: No input file specified.')
        print('QMDL Offline Parser only supports file input.')
        print('Usage: qmdl-parser -t qc -d your_file.qmdl --json-file output.json')
        sys.exit(1)

    # Writer preparation - Enhanced for multiple output formats
    writer = None
    pcap_writer = None
    # Determine output format priority: JSON/TXT > PCAP > Network
    if args.json_file or args.txt_file:
        # Enhanced output mode - use JSON/TXT writers
        if args.json_file and args.txt_file:
            # Both JSON and TXT - create composite writer
            from scat.writers.jsonwriter import JsonWriter
            from scat.writers.txtwriter import TxtWriter
            json_writer = JsonWriter(args.json_file)
            txt_writer = TxtWriter(args.txt_file)
            # Set input filename for metadata
            if args.dump and len(args.dump) > 0:
                json_writer.set_input_filename(args.dump[0])
                txt_writer.set_input_filename(args.dump[0])
            # If PCAP requested, create PcapWriter
            if args.preserve_intermediate and args.pcap_file:
                from scat.writers.pcapwriter import PcapWriter
                pcap_writer = PcapWriter(args.pcap_file, GSMTAP_PORT, IP_OVER_UDP_PORT)
                print("Note: Intermediate PCAP file will be created at:", args.pcap_file)
            # Create composite writer
            class CompositeWriter:
                def __init__(self, json_w, txt_w, pcap_w=None):
                    self.json_writer = json_w
                    self.txt_writer = txt_w
                    self.pcap_writer = pcap_w
                def write_cp(self, sock_content, radio_id, ts):
                    self.json_writer.write_cp(sock_content, radio_id, ts)
                    self.txt_writer.write_cp(sock_content, radio_id, ts)
                    if self.pcap_writer:
                        self.pcap_writer.write_cp(sock_content, radio_id, ts)
                def write_up(self, sock_content, radio_id, ts):
                    self.json_writer.write_up(sock_content, radio_id, ts)
                    self.txt_writer.write_up(sock_content, radio_id, ts)
                    if self.pcap_writer:
                        self.pcap_writer.write_up(sock_content, radio_id, ts)
                def write_parsed_data(self, parsed_result, radio_id, ts):
                    self.json_writer.write_parsed_data(parsed_result, radio_id, ts)
                    self.txt_writer.write_parsed_data(parsed_result, radio_id, ts)
                def write_stdout_data(self, stdout_text, radio_id, ts):
                    self.json_writer.write_stdout_data(stdout_text, radio_id, ts)
                    self.txt_writer.write_stdout_data(stdout_text, radio_id, ts)
                def close(self):
                    self.json_writer.close()
                    self.txt_writer.close()
                    if self.pcap_writer:
                        self.pcap_writer.pcap_file.close()
            writer = CompositeWriter(json_writer, txt_writer, pcap_writer)
        elif args.json_file:
            # JSON only
            from scat.writers.jsonwriter import JsonWriter
            writer = JsonWriter(args.json_file)
            if args.dump and len(args.dump) > 0:
                writer.set_input_filename(args.dump[0])
        elif args.txt_file:
            # TXT only  
            from scat.writers.txtwriter import TxtWriter
            writer = TxtWriter(args.txt_file)
            # Force legacy example header to improve parity (optional)
            try:
                writer.force_example_header = True
            except Exception:
                pass
            if args.dump and len(args.dump) > 0:
                writer.set_input_filename(args.dump[0])
        # If only PCAP requested with preserve_intermediate, create PcapWriter
        if args.preserve_intermediate and args.pcap_file and not (args.json_file and args.txt_file):
            from scat.writers.pcapwriter import PcapWriter
            pcap_writer = PcapWriter(args.pcap_file, GSMTAP_PORT, IP_OVER_UDP_PORT)
            print("Note: Intermediate PCAP file will be created at:", args.pcap_file)
            writer = pcap_writer
    elif args.pcap_file:
        # PCAP output only
        from scat.writers.pcapwriter import PcapWriter
        writer = PcapWriter(args.pcap_file, GSMTAP_PORT, IP_OVER_UDP_PORT)
    else:
        # Default network output
        writer = scat.writers.SocketWriter(GSMTAP_IP, GSMTAP_PORT, IP_OVER_UDP_PORT)

    current_parser = parser_dict[args.type]
    current_parser.set_io_device(io_device)
    current_parser.set_writer(writer)

    if args.debug:
        logger.setLevel(logging.DEBUG)
        current_parser.set_parameter({'log_level': logging.DEBUG})
    else:
        logger.setLevel(logging.INFO)
        current_parser.set_parameter({'log_level': logging.INFO})
    ch = logging.StreamHandler(stream = sys.stdout)
    f = logging.Formatter('%(asctime)s %(name)s (%(funcName)s) %(levelname)s: %(message)s')
    ch.setFormatter(f)
    logger.addHandler(ch)

    if args.type == 'qc':
        current_parser.set_parameter({
            'qsr-hash': args.qsr_hash,
            'qsr4-hash': args.qsr4_hash,
            'events': args.events,
            'msgs': args.msgs,
            'cacombos': args.cacombos,
            'combine-stdout': args.combine_stdout,
            'disable-crc-check': args.disable_crc_check,
            'layer': layers,
            'format': args.format,
            'gsmtapv3': args.gsmtapv3})
    elif args.type == 'sec':
        current_parser.set_parameter({
            'model': args.model,
            'start-magic': args.start_magic,
            'trace': args.trace,
            'ilm': args.ilm,
            'combine-stdout': args.combine_stdout,
            'layer': layers,
            'all-items': args.all_items,
            'format': args.format,
            'gsmtapv3': args.gsmtapv3})
    elif args.type == 'hisi':
        current_parser.set_parameter({
            'msgs': args.msgs,
            'combine-stdout': args.combine_stdout,
            'disable-crc-check': args.disable_crc_check,
            'layer': layers,
            'format': args.format,
            'gsmtapv3': args.gsmtapv3})

    # Run process
    if args.serial or args.usb:
        current_parser.stop_diag()
        current_parser.init_diag()
        current_parser.prepare_diag()

        signal.signal(signal.SIGINT, sigint_handler)

        if not (args.qmdl == None) and args.type == 'qc':
            current_parser.run_diag(scat.writers.RawWriter(args.qmdl))
        elif not (args.sdmraw == None) and args.type == 'sec':
            current_parser.run_diag(scat.writers.RawWriter(args.sdmraw))
        else:
            current_parser.run_diag()

        current_parser.stop_diag()
    elif args.dump:
        print(f"🔍 Analyzing QMDL file(s): {', '.join(args.dump)}")
        current_parser.read_dump()
        print("✅ Analysis completed successfully!")
    else:
        print('Error: Invalid input handler')
        sys.exit(1)
        
    # Cleanup writers
    if hasattr(writer, 'close'):
        writer.close()
        print(f"Output files written successfully")
        if args.json_file:
            print(f"JSON output: {args.json_file}")
        if args.txt_file:
            print(f"TXT output: {args.txt_file}")
        if args.pcap_file:
            print(f"PCAP output: {args.pcap_file}")

if __name__ == '__main__':
    scat_main()
