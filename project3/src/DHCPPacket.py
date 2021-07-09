import socket
import struct
import ipaddress
from random import randint

import server


class DHCPPacket:
    MAGIC_COOKIE = 0x63825363
    OPTIONS = {"MSGType": 53, "ClientID": 61, "ParameterList": 55, "SubnetMask": 1, "DNS": 6, "Hostname": 12,
               "ServerId": 54, "AddressRequest": 50, "AddressTime": 51, "End": 255}

    MESSAGE_TYPES = {"DISCOVER": 1, "OFFER": 2, "REQUEST": 3, "DECLINE": 4, "ACK": 5}

    @staticmethod
    def create_discover(interface: tuple) -> '__class__':
        packet = DHCPPacket()
        packet.type = DHCPPacket.MESSAGE_TYPES["DISCOVER"]
        packet.op = 1
        packet.htype = 1
        packet.hlen = 6
        packet.hops = 0
        packet.xid = randint(0, 1 << 31)
        packet.secs = 0
        packet.broadcast = 0
        packet.ciaddr = 0
        packet.yiaddr = 0
        packet.siaddr = 0
        packet.giaddr = 0
        packet.chaddr = int(interface[1].replace(":", ""), 16)

        packet.hostname = socket.gethostname()

        return packet

    @staticmethod
    def create_offer(discover_packet: '__class__', offered_ip: str, subnet_mask: str, dns: str, lease: int) -> '__class__':
        packet = DHCPPacket()
        packet.type = DHCPPacket.MESSAGE_TYPES["OFFER"]
        packet.op = 2
        packet.htype = 1
        packet.hlen = 6
        packet.hops = 0
        packet.xid = discover_packet.xid
        packet.secs = 0
        packet.broadcast = 0
        packet.ciaddr = 0
        packet.yiaddr = int(ipaddress.IPv4Address(offered_ip))
        packet.siaddr = int(ipaddress.IPv4Address(server.SERVER_ID))
        packet.giaddr = 0
        packet.chaddr = discover_packet.chaddr

        if DHCPPacket.OPTIONS["SubnetMask"] in discover_packet.options[DHCPPacket.OPTIONS["ParameterList"]]:
            packet.subnet = int(ipaddress.IPv4Address(subnet_mask))
        if DHCPPacket.OPTIONS["DNS"] in discover_packet.options[DHCPPacket.OPTIONS["ParameterList"]]:
            packet.dns = int(ipaddress.IPv4Address(dns))
        packet.lease = lease

        return packet

    @staticmethod
    def create_request(offer_packet: '__class__') -> '__class__':
        packet = DHCPPacket()
        packet.type = DHCPPacket.MESSAGE_TYPES["REQUEST"]
        packet.op = 1
        packet.htype = 1
        packet.hlen = 6
        packet.hops = 0
        packet.xid = offer_packet.xid
        packet.secs = 0
        packet.broadcast = 0
        packet.ciaddr = 0
        packet.yiaddr = 0
        packet.siaddr = 0
        packet.giaddr = 0
        packet.chaddr = offer_packet.chaddr

        packet.hostname = socket.gethostname()
        packet.ip_address = offer_packet.yiaddr

        # This value is stored as byte-like object. It doesn't need further packing
        packet.server_id = offer_packet.options["ServerId"]

        return packet

    @staticmethod
    def create_from_bytes(_in: bytes):
        packet = DHCPPacket()
        packet.op, packet.htype, packet.hlen, packet.hops, packet.xid, packet.secs, flags, packet.ciaddr, \
        packet.yiaddr, packet.siaddr, packet.giaddr = struct.unpack("!BBBBIHHIIII", _in[:7 * 4])

        packet.broadcast = flags >> 15

        chaddr = struct.unpack("!IH", _in[7 * 4:7 * 4 + 6])
        packet.chaddr = (chaddr[0] << 16) | chaddr[1]

        # +4 is for magic cookie
        options_bytes = _in[59 * 4 + 4:]

        packet.options = {}
        i = 0
        while (option := options_bytes[i]) != 0xff:
            length = options_bytes[i + 1]
            i += 2
            packet.options[option] = options_bytes[i: i + length]
            i += length

        packet.type = struct.unpack("!B", packet.options[DHCPPacket.OPTIONS["MSGType"]])[0]

        return packet

    def fixed_fields_to_bytes(self) -> bytearray:
        out = bytearray()

        # HEADER
        out.extend(struct.pack("!B", self.op))
        out.extend(struct.pack("!B", self.htype))
        out.extend(struct.pack("!B", self.hlen))
        out.extend(struct.pack("!B", self.hops))
        out.extend(struct.pack("!I", self.xid))
        out.extend(struct.pack("!H", self.secs))
        out.extend(struct.pack("!H", self.broadcast << 15))
        out.extend(struct.pack("!I", self.ciaddr))
        out.extend(struct.pack("!I", self.yiaddr))
        out.extend(struct.pack("!I", self.siaddr))
        out.extend(struct.pack("!I", self.giaddr))

        out.extend(struct.pack("!IH", self.chaddr >> 16, self.chaddr & 0xffff))
        out.extend(struct.pack("!dh", 0, 0))

        # BOOTP legacy padding
        out.extend(bytes(192))

        # Magic cookie
        out.extend(struct.pack("!I", DHCPPacket.MAGIC_COOKIE))

        return out

    def discover_to_bytes(self) -> bytearray:
        out = bytearray()

        out.extend(self.fixed_fields_to_bytes())

        # Options
        out.extend(struct.pack("!BBB", DHCPPacket.OPTIONS["MSGType"], 1, self.type))
        out.extend(struct.pack("!BBBB", DHCPPacket.OPTIONS["ParameterList"], 2, DHCPPacket.OPTIONS["SubnetMask"],
                               DHCPPacket.OPTIONS["DNS"]))

        out.extend(struct.pack("!BB", DHCPPacket.OPTIONS["Hostname"], len(self.hostname)))
        out.extend(self.hostname.encode())

        out.extend(struct.pack("!B", DHCPPacket.OPTIONS["End"]))

        return out

    def offer_to_bytes(self):
        out = bytearray()

        out.extend(self.fixed_fields_to_bytes())

        # Options
        out.extend(struct.pack("!BBB", DHCPPacket.OPTIONS["MSGType"], 1, self.type))

        out.extend(struct.pack("!BBI", DHCPPacket.OPTIONS["ServerId"], 4, self.siaddr))
        out.extend(struct.pack("!BBI", DHCPPacket.OPTIONS["AddressTime"], 4, self.lease))
        if self.subnet is not None:
            out.extend(struct.pack("!BBI", DHCPPacket.OPTIONS["SubnetMask"], 4, self.subnet))
        if self.dns is not None:
            out.extend(struct.pack("!BBI", DHCPPacket.OPTIONS["DNS"], 4, self.dns))

        out.extend(struct.pack("!B", DHCPPacket.OPTIONS["End"]))

        return out

    def request_to_bytes(self) -> bytearray:
        out = bytearray()

        out.extend(self.fixed_fields_to_bytes())

        # Options
        out.extend(struct.pack("!BBB", DHCPPacket.OPTIONS["MSGType"], 1, self.type))
        out.extend(struct.pack("!BBBB", DHCPPacket.OPTIONS["ParameterList"], 2, DHCPPacket.OPTIONS["SubnetMask"],
                               DHCPPacket.OPTIONS["DNS"]))

        out.extend(struct.pack("!BB", DHCPPacket.OPTIONS["Hostname"], len(self.hostname)))
        out.extend(self.hostname.encode())

        out.extend(struct.pack("!BBI", DHCPPacket.OPTIONS["AddressRequest"], 4, self.ip_address))
        out.extend(struct.pack("!BB", DHCPPacket.OPTIONS["ServerId"], 4))
        out.extend(self.server_id)

        out.extend(struct.pack("!B", DHCPPacket.OPTIONS["End"]))

        return out

    def decline_to_bytes(self):
        pass

    def ack_to_bytes(self):
        pass

    def to_bytes(self):
        if self.type == DHCPPacket.MESSAGE_TYPES["DISCOVER"]:
            return self.discover_to_bytes()
        elif self.type == DHCPPacket.MESSAGE_TYPES["OFFER"]:
            return self.offer_to_bytes()
        elif self.type == DHCPPacket.MESSAGE_TYPES["REQUEST"]:
            return self.request_to_bytes()
        elif self.type == DHCPPacket.MESSAGE_TYPES["DECLINE"]:
            return self.decline_to_bytes()
        elif self.type == DHCPPacket.MESSAGE_TYPES["ACK"]:
            return self.ack_to_bytes()
