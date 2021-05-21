import argparse
import ipaddress
import os
import select
import shlex
import socket
import ssl
import sys
import time
import traceback
from enum import Enum


class Commands(Enum):
    UPLOAD = 254
    EXEC_ = 253
    SEND = 252
    S_SEND = 251


IAP: int = 0xff
LENGTH_SIZE: int = 10


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
    send.add_argument('-e', '--encrypt', action='store_true', help='Encrypt the message using TLS')
    send.add_argument('message', type=str, metavar='Message to be sent')

    cmd_args = cmd_parser.parse_args(in_str)
    return cmd_args


def upload_file(sock: socket.socket, path: str):
    out = bytearray(b'\xff')
    out.append(Commands.UPLOAD.value)

    file = bytearray()
    with open(path, "rb") as f:
        while byte := f.read(1):
            file.extend(byte)

    file_name = os.path.basename(path)
    file_name_len = str(len(file_name))
    out.extend(b' ' * (LENGTH_SIZE - len(file_name_len)) + file_name_len.encode())
    out.extend(file_name.encode())

    file_len = str(len(file))
    out.extend(b' ' * (LENGTH_SIZE - len(file_len)) + file_len.encode())
    out.extend(file)

    sock.sendall(bytes(out))


def send_exec(sock: socket.socket, command: str):
    out = bytearray(b'\xff')
    out.append(Commands.EXEC_.value)

    command_len = str(len(command))
    out.extend(b' ' * (LENGTH_SIZE - len(command_len)) + command_len.encode())
    out.extend(command.encode())

    sock.sendall(bytes(out))

    output_len = int(sock.recv(LENGTH_SIZE).decode())
    while output_len > 0:
        received = sock.recv(4096)
        output_len -= len(received)
        print(received.decode(), end='')


def send_message(sock: socket.socket, message: str, send_iac: bool = True):
    out = bytearray()
    if send_iac:
        out.append(0xff)
        out.append(Commands.SEND.value)

    message_len = str(len(message))
    out.extend(b' ' * (LENGTH_SIZE - len(message_len)) + message_len.encode())
    out.extend(message.encode())

    sock.send(bytes(out))


def send_e_message(sock: socket.socket, message: str):
    sock.send(b'\xff')
    sock.send(Commands.S_SEND.value.to_bytes(1, 'big'))

    ssock = ssl.wrap_socket(sock, server_side=False, ssl_version=ssl.PROTOCOL_TLSv1_2, do_handshake_on_connect=True)
    send_message(ssock, message, send_iac=False)

    return ssock.unwrap()


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
                if data[0] == 0x1d:  # Toggle mode
                    command_mode = not command_mode
                else:
                    try:
                        if command_mode:
                            cmd_args = command_parser(shlex.split(in_str.strip()))
                            if cmd_args.commands == 'upload':
                                upload_file(sock, cmd_args.path)
                            elif cmd_args.commands == 'exec':
                                send_exec(sock, cmd_args.command)
                            elif cmd_args.commands == 'send':
                                if not cmd_args.encrypt:
                                    send_message(sock, cmd_args.message)
                                else:
                                    sock = send_e_message(sock, cmd_args.message)
                        else:
                            data = escape_iap(data)
                            sock.sendall(data)
                    except argparse.ArgumentError as e:
                        print(str(e))
                    except Exception as e:
                        traceback.print_exc()
                if command_mode:
                    print("telnet> ", end='')
                    sys.stdout.flush()
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
