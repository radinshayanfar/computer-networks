import argparse
import os
import socket
import threading
from enum import Enum


class Mode(Enum):
    TEXT = 1
    # IAP = 2
    UPLOAD = 3
    EXEC_ = 4
    SEND = 5
    S_SEND = 6


class Commands(Enum):
    UPLOAD = 254
    EXEC_ = 253
    SEND = 252
    S_SEND = 251


class ClientState:
    def __init__(self):
        self.iap_on = False
        self.mode = Mode.TEXT
        self.buffer = bytearray()
        self.read_length = 1


IAP: int = 0xff
LENGTH_SIZE: int = 10


def download_file(sock: socket.socket):
    file_name_len = int(sock.recv(LENGTH_SIZE).decode())
    file_name = sock.recv(file_name_len).decode()

    file_len = int(sock.recv(LENGTH_SIZE).decode())

    with open(file_name, "wb") as f:
        while file_len > 0:
            received = sock.recv(4096)
            file_len -= len(received)
            f.write(received)


def retrieve_exec(sock: socket.socket):
    command_len = int(sock.recv(LENGTH_SIZE).decode())
    command = sock.recv(command_len).decode()

    output = os.popen(command).read().encode()
    output_len = str(len(output))
    sock.sendall(b' ' * (LENGTH_SIZE - len(output_len)) + output_len.encode())
    sock.sendall(output)


def process_data(data: int, state: ClientState, sock: socket.socket):
    if state.iap_on:
        if data == IAP:
            print(chr(data), end='')
        if data == Commands.UPLOAD.value:
            download_file(sock)
        if data == Commands.EXEC_.value:
            retrieve_exec(sock)

        state.iap_on = False
    elif data == IAP:
        state.iap_on = True
    else:
        print(chr(data), end='')


def client_handler(sock: socket.socket):
    print(f"-> {sock.getpeername()[0]} connected on port {sock.getpeername()[1]}")

    client_state = ClientState()
    while True:
        data = sock.recv(1)
        if not data:
            print(f"-> {sock.getpeername()[0]}:{sock.getpeername()[1]} disconnected")
            break

        process_data(data[0], client_state, sock)


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
