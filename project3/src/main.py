import re
import socket
import subprocess

from DHCPPacket import DHCPPacket

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
    discover_rebuild = DHCPPacket.create_from_bytes(discover.to_bytes())
    print(vars(discover_rebuild))

    # sock.sendto(discover.to_bytes(), ('<broadcast>', SERVER_PORT))
    # print(sock.recv(1024))

    sock.close()

