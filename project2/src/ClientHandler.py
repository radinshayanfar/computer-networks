import os
import socket
import ssl
import time
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

    def receive_message(self, sock: socket.socket = None):
        if sock is None:
            sock = self.sock

        message_len = int(sock.recv(LENGTH_SIZE).decode())
        message = sock.recv(message_len).decode()

        print(f"---> Message from {sock.getpeername()[0]}:{sock.getpeername()[1]}:\n"
              f"---> {message}")

    def receive_e_message(self):
        # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        # context.load_cert_chain(certfile='../cert/test.crt', keyfile='../cert/test.key')
        ssock = ssl.wrap_socket(self.sock, server_side=True, certfile="../cert/test.crt", keyfile="../cert/test.key",
                                ssl_version=ssl.PROTOCOL_TLSv1_2)

        self.receive_message(ssock)
        self.sock = ssock.unwrap()

    def process_data(self, data: int):
        if self.iap_on:
            if data == IAP:
                print(chr(data), end='')
            elif data == Commands.UPLOAD.value:
                self.download_file()
            elif data == Commands.EXEC_.value:
                self.retrieve_exec()
            elif data == Commands.SEND.value:
                self.receive_message()
            elif data == Commands.S_SEND.value:
                self.receive_e_message()

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
