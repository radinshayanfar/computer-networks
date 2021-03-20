from DNSQuery import DNSQuery
import socket

from Question import Question

DNS_IP = "8.8.8.8"
DNS_IP = "4.2.2.4"
# DNS_IP = "a.nic.ir"
# DNS_IP = "pat.ns.cloudflare.com"
DNS_PORT = 53

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    query = DNSQuery.create_query([{"qname": "radin-shayanfar.ir", "qtype": Question.QTYPE_A, "qclass": Question.CLASS_IN}])
    query2 = DNSQuery.create_query([{"qname": "www3.l.google.com", "qtype": Question.QTYPE_AAAA, "qclass": Question.CLASS_IN}])

    sock.sendto(query.to_bytes(), (DNS_IP, DNS_PORT))
    # sock.sendto(query2.to_bytes(), (DNS_IP, DNS_PORT))
    data, _ = sock.recvfrom(512)
    # data, _ = sock.recvfrom(512)
    print(data)
