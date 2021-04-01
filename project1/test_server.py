import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 3232

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(512)
    print(f"Received message from {addr}: {data}")
