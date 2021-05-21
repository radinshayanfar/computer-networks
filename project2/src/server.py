import socket
import threading
import argparse
from enum import Enum


class Mode(Enum):
    TEXT = 1
    # IAP = 2
    UPLOAD = 3
    _EXEC = 4
    SEND = 5
    S_SEND = 6

class Commands(Enum):
    UPLOAD = 254
    _EXEC = 253
    SEND = 252
    S_SEND = 251

class ClientState:
    def __init__(self):
        self.iap_on = False
        self.mode = Mode.TEXT


IAP: int = 0xff
LENGTH_SIZE: int = 10


def process_data(data: bytes, state: ClientState):
    i = 0
    while i < len(data):
        if state.iap_on:
            if data[i] == IAP:
                print(chr(data[i]), end='')

            state.iap_on = False
        elif data[i] == IAP:
            state.iap_on = True
        elif state.mode == Mode.TEXT:
            print(chr(data[i]), end='')
        i += 1


def client_handler(sock: socket.socket):
    print(f"-> {sock.getpeername()[0]} connected on port {sock.getpeername()[1]}")

    client_state = ClientState()
    while True:
        data = sock.recv(4096)
        if not data:
            print(f"-> {sock.getpeername()[0]}:{sock.getpeername()[1]} disconnected")
            break

        process_data(data, client_state)


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
        threading.Thread(target=client_handler, args=(connection,)).start()
