import json
import socket
import struct
from ipaddress import IPv4Address

import redis

from DHCPPacket import DHCPPacket

CLIENT_PORT = 68
SERVER_PORT = 67

with open("config.json", "r") as fh:
    CONFIG = json.load(fh)

SERVER_ID = CONFIG["server_address"]

if CONFIG["pool_mode"] == "range":
    ADDRESS_RANGE = list(map(int, map(IPv4Address, CONFIG["range"].values())))
elif CONFIG["pool_mode"] == "subnet":
    block_range = 0xffffffff - int(IPv4Address(CONFIG["subnet"]["subnet_mask"]))
    ADDRESS_RANGE = (network := int(IPv4Address(CONFIG["subnet"]["ip_block"]))) + 1, network + block_range - 1

rdb = redis.Redis(host='localhost', port=6379, db=2)


def mac_num_to_str(mac_num: int) -> str:
    return ':'.join(format(s, '02x') for s in mac_num.to_bytes(6, byteorder='big'))


def get_new_ip(mac: int, hostname: str) -> int:
    # Check if client already has IP
    redis_ip_key = rdb.get(f"dhcp:mac:{mac}")
    if redis_ip_key is not None:
        return int(redis_ip_key.decode().split(":")[-1])

    # Searching for new available IP
    for ip in range(ADDRESS_RANGE[0], ADDRESS_RANGE[1] + 1):
        if str(IPv4Address(ip)) not in CONFIG["reservation_list"].values() and not rdb.exists(f"dhcp:ip:{ip}"):
            with rdb.pipeline() as pipe:
                pipe.lpush(f"dhcp:ip:{ip}", hostname, mac)
                pipe.expire(f"dhcp:ip:{ip}", CONFIG["offer_lease"])
                pipe.set(f"dhcp:mac:{mac}", f"dhcp:ip:{ip}", ex=CONFIG["offer_lease"])
                pipe.execute()

                return ip


def discover_handle(discover: 'DHCPPacket') -> 'DHCPPacket':
    # Check for blocked or reserved MACs
    mac_str = mac_num_to_str(discover.chaddr)
    if mac_str in CONFIG["black_list"]:
        return None
    elif mac_str in CONFIG["reservation_list"]:
        return DHCPPacket.create_offer(discover, int(IPv4Address(CONFIG["reservation_list"][mac_str])), '255.255.255.0',
                                       CONFIG["dns"], (1 << 32) - 1, SERVER_ID)

    new_ip = get_new_ip(discover.chaddr, discover.options[DHCPPacket.OPTIONS["Hostname"]].decode())
    # TODO: CHECK NO IP AVAILABLE
    offer = DHCPPacket.create_offer(discover, new_ip, '255.255.255.0', CONFIG["dns"], CONFIG["lease_time"], SERVER_ID)

    return offer


def request_handle(request: 'DHCPPacket') -> 'DHCPPacket':
    server_id = struct.unpack("!I", request.options.get(DHCPPacket.OPTIONS["ServerId"], bytes(4)))[0]
    if server_id != int(IPv4Address(SERVER_ID)):
        return None

    # Check for blocked or reserved MACs
    mac_str = mac_num_to_str(request.chaddr)
    if mac_str in CONFIG["black_list"]:
        return None
    elif mac_str in CONFIG["reservation_list"]:
        lease_time = (1 << 32) - 1
    else:
        lease_time = CONFIG["lease_time"]

    requested_ip = struct.unpack("!I", request.options[DHCPPacket.OPTIONS["AddressRequest"]])[0]
    db_record = rdb.lrange(f"dhcp:ip:{requested_ip}", 0, 0)

    if len(db_record) == 1 and int(db_record[0].decode()) != request.chaddr:  # reserved for someone else
        return DHCPPacket.create_nak(request)
    if (requested_ip_str := str(IPv4Address(requested_ip))) in CONFIG["reservation_list"].values() and mac_str in \
            CONFIG["reservation_list"] and CONFIG["reservation_list"][mac_str] != requested_ip_str:
        return DHCPPacket.create_nak(request)

    with rdb.pipeline() as pipe:
        pipe.delete(f"dhcp:ip:{requested_ip}")
        pipe.lpush(f"dhcp:ip:{requested_ip}", request.options[DHCPPacket.OPTIONS["Hostname"]].decode(), request.chaddr)
        pipe.expire(f"dhcp:ip:{requested_ip}", lease_time)
        pipe.set(f"dhcp:mac:{request.chaddr}", f"dhcp:ip:{requested_ip}", ex=lease_time)
        pipe.execute()

    return DHCPPacket.create_ack(request, requested_ip, '255.255.255.0', CONFIG["dns"], lease_time,
                                 SERVER_ID)


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(("0.0.0.0", SERVER_PORT))

    while True:
        packet_bytes, addr = sock.recvfrom(1024)
        print(f"Received packet from {addr[0]}:{addr[1]}")

        packet = DHCPPacket.create_from_bytes(packet_bytes)

        response_packet = None
        if packet.type == DHCPPacket.MESSAGE_TYPES["DISCOVER"]:
            response_packet = discover_handle(packet)
        elif packet.type == DHCPPacket.MESSAGE_TYPES["REQUEST"]:
            response_packet = request_handle(packet)

        if response_packet is not None:
            sock.sendto(response_packet.to_bytes(), ('<broadcast>', CLIENT_PORT))

    sock.close()
