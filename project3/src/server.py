import socket

from DHCPPacket import DHCPPacket

CLIENT_PORT = 68
SERVER_PORT = 67

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(("0.0.0.0", SERVER_PORT))

    while True:
        packet_bytes = sock.recv(1024)
        packet = DHCPPacket.create_from_bytes(packet_bytes)

        offer = DHCPPacket.create_offer(packet, '10.1.1.1', '255.255.255.0', '1.1.1.1', 86400)
        sock.sendto(offer.to_bytes(), ('<broadcast>', CLIENT_PORT))

    sock.close()
