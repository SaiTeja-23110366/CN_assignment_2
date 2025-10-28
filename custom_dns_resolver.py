#!/usr/bin/python3

import socket
import time
import sys
import os
from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE, RCODE, EDNS0
from datetime import datetime

ROOT_SERVERS = ["198.41.0.4", "199.9.14.201", "192.33.4.12"]

# --- NEW: File for Part F graph data ---
CSV_LOG_FILE = "part_f_graph_data.csv"

# --- NEW: Caching and Stats (Part F) ---
DNS_CACHE = {} # A simple dictionary to store {qname: response_packet}
STATS = {
    'total_queries': 0,
    'cache_hits': 0
}

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}] {msg}")

def send_udp_query(query_packet, server_ip, timeout=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(query_packet.pack(), (server_ip, 53))
        data, _ = sock.recvfrom(4096)
        return DNSRecord.parse(data)
    except socket.timeout:
        log(f"ERROR: Query to {server_ip} timed out")
        return None
    finally:
        sock.close()

def resolve_iterative(qname, client_ip):
    log_prefix = f"Query for {qname} from {client_ip}:"
    total_start_time = time.time()
    nameservers = ROOT_SERVERS
    step_name = "Root"
    servers_visited_count = 0 

    while True:
        server_ip = nameservers[0]
        query = DNSRecord.question(qname, qtype="A")
        step_start_time = time.time()
        log(f"{log_prefix} Resolution mode: Iterative, Step: {step_name}, Contacting Server: {server_ip}")
        servers_visited_count += 1 
        response = send_udp_query(query, server_ip)

        if not response:
            total_time = (time.time() - total_start_time) * 1000
            log(f"{log_prefix} FAILED. No response from {server_ip}")
            with open(CSV_LOG_FILE, "a") as f:
                f.write(f"{client_ip},{qname},{total_time:.2f},{servers_visited_count},FAILED_TIMEOUT\n")
            return None 

        rtt = (time.time() - step_start_time) * 1000
        log(f"{log_prefix} Response from {server_ip} (RTT: {rtt:.2f} ms): {RCODE[response.header.rcode]}, {len(response.rr)} Answers, {len(response.auth)} Authorities, {len(response.ar)} Additional")

        if response.header.rcode == RCODE.NOERROR and response.rr:
            for rr in response.rr:
                if rr.rtype == QTYPE.A:
                    total_time = (time.time() - total_start_time) * 1000
                    log(f"{log_prefix} SUCCESS. Final Answer: {rr.rdata}. Total time: {total_time:.2f} ms")
                    # --- NEW: Store in Cache! ---
                    DNS_CACHE[qname] = response
                    with open(CSV_LOG_FILE, "a") as f:
                        f.write(f"{client_ip},{qname},{total_time:.2f},{servers_visited_count},{rr.rdata}\n")
                    return response 

        if response.header.rcode != RCODE.NOERROR:
            total_time = (time.time() - total_start_time) * 1000
            log(f"{log_prefix} FAILED. Server {server_ip} returned {RCODE[response.header.rcode]}. Total time: {total_time:.2f} ms")
            with open(CSV_LOG_FILE, "a") as f:
                f.write(f"{client_ip},{qname},{total_time:.2f},{servers_visited_count},{RCODE[response.header.rcode]}\n")
            return response 

        if not response.rr and response.auth:
            ns_names = [rr.rdata.label for rr in response.auth if rr.rtype == QTYPE.NS]
            new_nameservers = []
            for rr in response.ar:
                if rr.rtype == QTYPE.A and rr.rname in ns_names:
                    new_nameservers.append(str(rr.rdata))

            if new_nameservers:
                nameservers = new_nameservers
                step_name = "TLD" if step_name == "Root" else "Authoritative" 
                continue 
            else:
                total_time = (time.time() - total_start_time) * 1000
                log(f"{log_prefix} FAILED. No glue records found for NS: {ns_names}. Total time: {total_time:.2f} ms")
                with open(CSV_LOG_FILE, "a") as f:
                    f.write(f"{client_ip},{qname},{total_time:.2f},{servers_visited_count},FAILED_NO_GLUE\n")
                return None 

        total_time = (time.time() - total_start_time) * 1000
        log(f"{log_prefix} FAILED. Unknown state. Total time: {total_time:.2f} ms")
        with open(CSV_LOG_FILE, "a") as f:
            f.write(f"{client_ip},{qname},{total_time:.2f},{servers_visited_count},FAILED_UNKNOWN\n")
        return None

def main():
    listen_ip = "0.0.0.0"
    listen_port = 53
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_ip, listen_port))

    with open(CSV_LOG_FILE, "w") as f:
        f.write("ClientIP,Domain,TotalTime_ms,ServersVisited,Result\n")

    log(f"Custom DNS resolver (Part F - CACHING) starting on {listen_ip}:{listen_port}...")

    try:
        while True:
            data, (client_ip, client_port) = sock.recvfrom(4096)
            try:
                request = DNSRecord.parse(data)
                qname = str(request.q.qname)
                qtype = request.q.qtype # This is the line we fixed
                log(f"Received query for {qname} (Type: {QTYPE[qtype]}) from {client_ip}:{client_port}")

                if qtype != QTYPE.A:
                    log(f"Unsupported query type ({QTYPE[qtype]}). Sending 'Not Implemented' response.")
                    reply = DNSRecord(
                        DNSHeader(id=request.header.id, qr=1, aa=0, rcode=RCODE.NOTIMP),
                        q=request.q
                    ).pack()
                    sock.sendto(reply, (client_ip, client_port))
                    continue 

                # --- This is an 'A' record, count it for stats ---
                STATS['total_queries'] += 1

                # --- NEW: Check Cache First! (Part F) ---
                if qname in DNS_CACHE:
                    log(f"Query for {qname}: Cache status: HIT")
                    STATS['cache_hits'] += 1
                    response_packet = DNS_CACHE[qname] # Get response from cache

                    # Log to CSV even for cache hits
                    with open(CSV_LOG_FILE, "a") as f:
                        # 0 ms time, 0 servers visited
                        f.write(f"{client_ip},{qname},0.00,0,CACHE_HIT\n")
                else:
                    log(f"Query for {qname}: Cache status: MISS")
                    # Not in cache, resolve it normally
                    response_packet = resolve_iterative(qname, client_ip)
                # ------------------------------------

                if response_packet:
                    response_packet.header.id = request.header.id
                    reply = response_packet.pack()
                else:
                    reply = DNSRecord(
                        DNSHeader(id=request.header.id, qr=1, aa=0, rcode=RCODE.SERVFAIL),
                        q=request.q
                    ).pack()
                sock.sendto(reply, (client_ip, client_port))
            except Exception as e:
                log(f"ERROR: Failed to process packet: {e}")

    except KeyboardInterrupt:
        log("Shutting down...")
        # --- NEW: Print Cache Stats on exit ---
        if STATS['total_queries'] > 0:
            hit_percentage = (STATS['cache_hits'] / STATS['total_queries']) * 100
            log("--- Cache Statistics (Part F) ---")
            log(f"Total 'A' Queries: {STATS['total_queries']}")
            log(f"Cache Hits:        {STATS['cache_hits']}")
            log(f"Cache Hit Rate:    {hit_percentage:.2f} %")
            log("---------------------------------")
    finally:
        sock.close()

if __name__ == "__main__":
    if os.geteuid() != 0:
        log("ERROR: This script must be run as root (or with sudo).")
        sys.exit(1)
    main()
