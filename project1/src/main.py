import socket
import argparse

from DNSQuery import DNSQuery
from Question import Question

# DNS_IP = "1.1.1.1"
# DNS_IP = "8.8.8.8"
DNS_IP = "4.2.2.4"
# DNS_IP = "a.nic.ir"
# DNS_IP = "pat.ns.cloudflare.com"
DNS_PORT = 53


def resolve_from_std(qname, qtype, recursion):
    if qtype == 'A':
        qtype = Question.QTYPE_A
    elif qtype == 'AAAA':
        qtype = Question.QTYPE_AAAA
    elif qtype == 'NS':
        qtype = Question.QTYPE_NS
    elif qtype == 'CNAME':
        qtype = Question.QTYPE_CNAME
    elif qtype == 'MX':
        qtype = Question.QTYPE_MX
    elif qtype == 'TXT':
        qtype = Question.QTYPE_TXT

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    query = DNSQuery.create_query(
        [{"qname": qname, "qtype": qtype, "qclass": Question.CLASS_IN}])
    # query2 = DNSQuery.create_query(
    #     [{"qname": "www3.l.google.com", "qtype": Question.QTYPE_AAAA, "qclass": Question.CLASS_IN}])

    sock.sendto(query.to_bytes(), (DNS_IP, DNS_PORT))
    # sock.sendto(query2.to_bytes(), (DNS_IP, DNS_PORT))
    data, _ = sock.recvfrom(512)
    # data, _ = sock.recvfrom(512)
    print(data)

    query3 = DNSQuery.from_bytes(data)


def resolve_from_file(filename, output_filename, recursion):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="MyNSLookup", allow_abbrev=False)

    parser.add_argument('-r', '--recursive', action='store_true')
    parser.add_argument('-f', '--file', action='store_true', help='reading input from csv')
    std_file_mutex = parser.add_mutually_exclusive_group()
    std_file_mutex.add_argument('-t', '--type', type=str.upper, choices=['A', 'AAAA', 'NS', 'CNAME', 'MX', 'TXT'],
                                default='A', metavar='<qtype>')
    std_file_mutex.add_argument('-o', '--output', type=str, metavar='<output-file>')

    parser.add_argument('qname', type=str, metavar='<qname | filename>')

    args = parser.parse_args()

    if args.file and args.output is None:
        parser.error('the following arguments are required when using --file: -o, --output')

    if not args.file:
        resolve_from_std(args.qname, args.type, args.recursive)
    else:
        resolve_from_file(args.qname, args.output, args.recursive)
