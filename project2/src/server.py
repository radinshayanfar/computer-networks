import argparse
import socket
import threading

from ClientHandler import ClientHandler

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="MyTelnetServer", allow_abbrev=False)

    parser.add_argument('-s', '--server', type=str, action='store', default='0.0.0.0', metavar='Server address')
    parser.add_argument('-p', '--port', type=int, action='store', default=23, metavar='Port number')

    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((args.server, args.port))
    sock.listen(5)

    print(f"Listening on {args.server}:{args.port}")

    while True:
        connection, address = sock.accept()
        new_client = ClientHandler(connection)
        threading.Thread(target=new_client.handler).start()
