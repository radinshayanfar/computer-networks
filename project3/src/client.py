import ipaddress
import re
import socket
import struct
import subprocess

from DHCPPacket import DHCPPacket
from Timeout import Timeout

CLIENT_PORT = 68
SERVER_PORT = 67


def get_network_interfaces() -> list:
    output = subprocess.Popen(['ip', 'link', 'show'], stdout=subprocess.PIPE).communicate()[0].decode()
    return re.findall(r"^\d: (.+):.*\s+link/.+ ((?:\w{2}:){5}\w{2}) ", output, re.MULTILINE)


def select_nic(nics: list) -> tuple:
    print("Select network interface:")
    for i, nic in enumerate(nics):
        print(f"[{i + 1}] {nic[0]} ({nic[1]})")
    selected_num = int(input("-> ")) - 1

    return nics[selected_num]


if __name__ == '__main__':
    nic_list = get_network_interfaces()
    selected_nic = select_nic(nic_list)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(("0.0.0.0", CLIENT_PORT))

    discover = DHCPPacket.create_discover(selected_nic)

    sock.sendto(last_sent := discover.to_bytes(), ('<broadcast>', SERVER_PORT))

    timeout = Timeout()
    timeout.start_time()
    wait_state = DHCPPacket.MESSAGE_TYPES["OFFER"]
    while True:
        new_timeout, retransmit = timeout.get_timeout()
        if new_timeout == -1:
            print("Timeout occurred more than max limit. Starting over...")
            discover = DHCPPacket.create_discover(selected_nic)
            sock.sendto(last_sent := discover.to_bytes(), ('<broadcast>', SERVER_PORT))
            timeout = Timeout()
            timeout.start_time()
            new_timeout, _ = timeout.get_timeout()
            wait_state = DHCPPacket.MESSAGE_TYPES["OFFER"]
        elif retransmit:
            sock.sendto(last_sent, ('<broadcast>', SERVER_PORT))

        sock.settimeout(new_timeout)
        try:
            packet_bytes = sock.recv(1024)
        except (BlockingIOError, socket.timeout) as e:
            continue

        packet = DHCPPacket.create_from_bytes(packet_bytes)
        if packet.xid != discover.xid:
            continue
        if packet.type != wait_state:
            continue
        if packet.type == DHCPPacket.MESSAGE_TYPES["NAK"]:
            print("Unable to get IP!")
            break
        if struct.unpack("!I", packet.options[DHCPPacket.OPTIONS["ServerId"]])[0] == int(
                ipaddress.IPv4Address('192.168.1.1')):
            continue

        if wait_state == DHCPPacket.MESSAGE_TYPES["OFFER"]:
            request = DHCPPacket.create_request(packet)
            sock.sendto(last_sent := request.to_bytes(), ('<broadcast>', SERVER_PORT))
            wait_state = DHCPPacket.MESSAGE_TYPES["ACK"]
            timeout = Timeout()
            timeout.start_time()
        elif wait_state == DHCPPacket.MESSAGE_TYPES["ACK"]:
            expire = struct.unpack("!I", packet.options[DHCPPacket.OPTIONS["AddressTime"]])[0]
            print("Got IP address:")
            print(f"-> IP: {str(ipaddress.IPv4Address(packet.yiaddr))}")
            print(f"-> Expire: {expire} second(s)")
            break

    sock.close()
