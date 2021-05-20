import argparse
import ipaddress
import os
import select
import socket
import sys


def sock_send_recv(sock):
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
                data = sys.stdin.readline().encode()
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
