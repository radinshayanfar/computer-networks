import argparse
import csv
import re
import socket

from DNSQuery import DNSQuery
from Question import Question

# DNS_IP = "1.1.1.1"
# DNS_IP = "8.8.8.8"
DNS_IP = "4.2.2.4"
# DNS_IP = "a.nic.ir"
# DNS_IP = "pat.ns.cloudflare.com"
DNS_PORT = 53


def ns_name_to_ip(server_name, additionals):
    ipv4_regex = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if re.match(ipv4_regex, server_name):
        return server_name

    if additionals is not None:
        for additional in additionals:
            if server_name == additional.NAME:
                return additional.RDATA

    resolved = resolve_single(server_name, Question.QTYPE_A, True, (DNS_IP, DNS_PORT), False)
    if resolved is None:
        raise Exception(f"{server_name} not found!")
    return resolved.answers[0].RDATA


def resolve_dfs(query, recursion, server, print_output, resolved_server=None):
    if resolved_server is None:
        resolved_server = server[0]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(query.to_bytes(), (resolved_server, server[1]))
    data, _ = sock.recvfrom(512)
    response = DNSQuery.from_bytes(data)

    if print_output:
        print(F"Server: {server[0]} ({resolved_server})")
        print(response)

    if response.header.ANCOUNT > 0:
        return response
    if len(response.authorities) == 1 and response.authorities[0].TYPE == Question.QTYPE_SOA:
        return None

    for auth in response.authorities:
        try:
            resolvent = resolve_dfs(query, recursion, (auth.RDATA, DNS_PORT), print_output,
                                    ns_name_to_ip(auth.RDATA, response.additionals))
            if resolvent is not None:
                return resolvent
        except Exception as e:
            print(str(e))

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
    result = resolve_dfs(query, recursion, server, print_output)
    if print_output and result is None:
        print("===== Not found :(")

    return result


def resolve_from_file(filename, output_filename, recursion, server=(DNS_IP, DNS_PORT)):
    results = []
    with open(filename, 'r') as f:
        queries_reader = csv.DictReader(f)
        for row in queries_reader:
            resolved = resolve_single(row['name'], row['type'].upper(), True, server, False)
            if resolved is None:
                continue
            for answer in resolved.answers:
                results.append([resolved.questions[0].qname, answer.get_type_text(), answer.RDATA])

    with open(output_filename, 'w') as f:
        results_writer = csv.writer(f)
        results_writer.writerow(['name', 'type', 'value'])
        results_writer.writerows(results)


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
