import argparse
import ipaddress
import os
import select
import socket
import sys


class Commands(Enum):
    UPLOAD = 254
    _EXEC = 253
    SEND = 252
    S_SEND = 251


IAP: int = 0xff


def escape_iap(data: bytes):
    data = bytearray(data)
    i = 0
    while i < len(data):
        if data[i] == IAP:
            data.insert(i, IAP)
            i += 1
        i += 1

    return bytes(data)


def command_parser(in_str: list):
    cmd_parser = argparse.ArgumentParser(prog="", allow_abbrev=False, add_help=False, exit_on_error=False)
    subparser = cmd_parser.add_subparsers(dest='commands')

    upload = subparser.add_parser('upload')
    _exec = subparser.add_parser('exec')
    send = subparser.add_parser('send')

    upload.add_argument('path', type=str, metavar='Path to the file')
    _exec.add_argument('command', type=str, metavar='Command to be executed on the host')
    send.add_argument('-e', '-encrypt', action='store_true', help='Encrypt the message using TLS')
    send.add_argument('message', type=str, metavar='Message to be sent')

    cmd_args = cmd_parser.parse_args(in_str)
    return cmd_args


def sock_send_recv(sock: socket.socket):
    command_mode = False
    while True:
        try:
            read, write, _error = select.select([sys.stdin, sock], [], [])

            if sock in read:
                data = sock.recv(4096)
                if not data:
                    print("Connection closed by foreign host.")
                    break
                print(data.decode(), end='')

            if sys.stdin in read:
                in_str = sys.stdin.readline()
                data = in_str.encode()
                if data[:1] == 0x1d.to_bytes(1, 'big'):  # Toggle mode
                    command_mode = not command_mode
                elif command_mode:
                    try:
                        cmd_args = command_parser(in_str.strip().split())
                    except argparse.ArgumentError as e:
                        print(str(e))
                else:
                    data = escape_iap(data)
                    sock.sendall(data)

        except KeyboardInterrupt as e:
            break
        except socket.error as error:
            print(os.strerror(error.errno), file=sys.stderr)
            exit()


def connection_mode(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(args.timeout)

    try:
        sock.connect((args.hostname, args.port))
        print(f"Connected to {sock.getpeername()[0]}:{sock.getpeername()[1]}")
    except socket.timeout as timeout:
        print("Connection timed out")
        exit()
    except socket.error as error:
        print(os.strerror(error.errno), file=sys.stderr)
        exit()

    sock_send_recv(sock)

    sock.close()


def scan_mode(args):
    for ip in ipaddress.IPv4Network(args.scan):
        print(f"-> Scanning {str(ip)} ports 0-1023")
        for port in range(1024):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(args.timeout)
                try:
                    sock.connect((str(ip), port))
                    print(f"-> {str(ip)}:{port} is open")
                except socket.timeout as timeout:
                    pass
                except socket.error as error:
                    # print(f"port number: {port}, error: {os.strerror(error.errno)}", file=sys.stderr)
                    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="MyTelnet", allow_abbrev=False)

    parser.add_argument('-s', '--scan', type=str, action='store')
    parser.add_argument('-t', '--timeout', type=float, action='store', metavar='Timeout in seconds', default=2)

    parser.add_argument('hostname', type=str, nargs='?', metavar='Host name')
    parser.add_argument('port', type=int, nargs='?', metavar='Port number')

    args = parser.parse_args()

    if args.scan is None and (args.hostname is None or args.port is None):
        parser.error('Hostname and port number must be given in non-scan mode.')

    if args.scan is not None:
        scan_mode(args)
    else:
        connection_mode(args)
