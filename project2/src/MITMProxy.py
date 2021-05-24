import os
import queue
import select
import socket
import sys
import threading


class MITMProxy:
    PROXY_PORT: int = None
    PROXY_HOST: str = '127.0.0.1'

    def __init__(self):
        self._client_to_server_queue = queue.Queue()
        self._server_to_client_queue = queue.Queue()
        self.sent_buffer = bytearray()
        self.recv_buffer = bytearray()

    def run_server(self, hostname: str, port: int, timeout: int):
        self._start_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._start_socket.bind((self.PROXY_HOST, 0))
        MITMProxy.PROXY_PORT = self._start_socket.getsockname()[1]

        threading.Thread(target=self._server_handler, args=(hostname, port, timeout), daemon=False).start()
        threading.Thread(target=self._client_handler, daemon=False).start()

        return self.PROXY_HOST, self.PROXY_PORT

    def _server_handler(self, hostname: str, port: int, timeout: int):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(timeout)

        try:
            server_socket.connect((hostname, port))
            print(f"Connected to {server_socket.getpeername()[0]}:{server_socket.getpeername()[1]}")
        except socket.timeout as timeout:
            print("Connection timed out")
            self._server_to_client_queue.put(None)
            return
        except socket.error as error:
            print(os.strerror(error.errno), file=sys.stderr)
            self._server_to_client_queue.put(None)
            return

        while True:
            try:
                read, write, _error = select.select([server_socket], [], [], 0.001)

                if server_socket in read:
                    data = server_socket.recv(4096)
                    if not data:
                        print("Connection closed by foreign host.")
                        self._server_to_client_queue.put(None)
                        break
                    self._server_to_client_queue.put(data)

                try:
                    data = self._client_to_server_queue.get_nowait()
                    if data is None:
                        break
                    server_socket.sendall(data)
                except queue.Empty:
                    pass

            except socket.error as error:
                print(os.strerror(error.errno), file=sys.stderr)
                self._server_to_client_queue.put(None)
                break

        server_socket.close()

    def _client_handler(self):
        self._start_socket.listen(1)

        client_socket, address = self._start_socket.accept()

        while True:
            try:
                read, write, _error = select.select([client_socket], [], [], 0.001)

                if client_socket in read:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    self.sent_buffer.extend(data)
                    self._client_to_server_queue.put(data)

                try:
                    data = self._server_to_client_queue.get_nowait()
                    if data is None:
                        break
                    self.recv_buffer.extend(data)
                    client_socket.sendall(data)
                except queue.Empty:
                    pass
            except socket.error as error:
                print(os.strerror(error.errno), file=sys.stderr)
                break

        self._client_to_server_queue.put(None)
        self._start_socket.close()
        client_socket.close()

    def close_sockets(self):
        self._client_to_server_queue.put(None)
        self._server_to_client_queue.put(None)
