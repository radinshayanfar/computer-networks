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


def resolve_dfs(query, recursion, server, print_output):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(query.to_bytes(), server)
    data, _ = sock.recvfrom(512)
    response = DNSQuery.from_bytes(data)

    if print_output:
        print(F"Server: {server[0]}")
        print(response)

    if response.header.ANCOUNT > 0:
        return response
    if len(response.authorities) == 1 and response.authorities[0].TYPE == Question.QTYPE_SOA:
        return None

    for auth in response.authorities:
        resolvent = resolve_dfs(query, recursion, (auth.get_data(), DNS_PORT), print_output)
        if resolvent is not None:
            return resolvent

    return None


def resolve_single(qname, qtype, recursion, server=(DNS_IP, DNS_PORT), print_output=True):
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

    query = DNSQuery.create_query([{"qname": qname, "qtype": qtype, "qclass": Question.CLASS_IN}], recursion)
    resolve_dfs(query, recursion, server, print_output)


def resolve_from_file(filename, output_filename, recursion, server=(DNS_IP, DNS_PORT)):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="MyNSLookup", allow_abbrev=False)

    parser.add_argument('-r', '--recursive', action='store_true')
    parser.add_argument('-f', '--file', action='store_true', help='reading input from csv')
    parser.add_argument('-s', '--server', type=str, action='store')
    parser.add_argument('-p', '--port', type=int, action='store')
    std_file_mutex = parser.add_mutually_exclusive_group()
    std_file_mutex.add_argument('-t', '--type', type=str.upper, choices=['A', 'AAAA', 'NS', 'MX', 'TXT'],
                                default='A', metavar='<qtype>')
    std_file_mutex.add_argument('-o', '--output', type=str, metavar='<output-file>')

    parser.add_argument('qname', type=str, metavar='<qname | filename>')

    args = parser.parse_args()

    if args.file and args.output is None:
        parser.error('the following arguments are required when using --file: -o, --output')
    if args.server is not None:
        DNS_IP = args.server
    if args.port is not None:
        DNS_PORT = args.port

    if not args.file:
        resolve_single(args.qname, args.type, args.recursive, (DNS_IP, DNS_PORT))
    else:
        resolve_from_file(args.qname, args.output, args.recursive, (DNS_IP, DNS_PORT))
