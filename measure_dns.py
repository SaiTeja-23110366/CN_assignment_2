#!/usr/bin/python3

import os
import re
import sys
import time

def measure_dns(domain_list_file):
    """
    Resolves domains from a file and prints statistics.
    """
    if not os.path.exists(domain_list_file):
        print(f"Error: File not found {domain_list_file}")
        return

    with open(domain_list_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    if not domains:
        print(f"No domains found in {domain_list_file}")
        return

    total_queries = len(domains)
    successful_queries = 0
    failed_queries = 0
    total_latency = 0.0  # Total query time in milliseconds

    print(f"--- Starting DNS benchmark for {domain_list_file} ---")
    print(f"Total domains to query: {total_queries}\n")

    start_time = time.time()

    for domain in domains:
        # Use 'dig' to perform the lookup. 
        # We add +timeout=2 and +tries=1 to fail faster
        command = f"dig {domain} +timeout=2 +tries=1"
        try:
            result = os.popen(command).read()

            # Check for success (status: NOERROR or NXDOMAIN)
            if "status: NOERROR" in result:
                successful_queries += 1
                # Try to parse query time
                match = re.search(r"Query time: (\d+) msec", result)
                if match:
                    total_latency += float(match.group(1))
            else:
                # Any other status (SERVFAIL, timeout) is a failure
                failed_queries += 1

        except Exception as e:
            print(f"Error resolving {domain}: {e}")
            failed_queries += 1

    end_time = time.time()
    total_time_seconds = end_time - start_time

    # Calculate statistics
    avg_latency = (total_latency / successful_queries) if successful_queries > 0 else 0
    # Throughput = queries per second
    avg_throughput = (successful_queries / total_time_seconds) if total_time_seconds > 0 else 0

    # Print results
    print("\n--- Benchmark Complete ---")
    print(f"Total queries:        {total_queries}")
    print(f"Successful queries:   {successful_queries}")
    print(f"Failed queries:       {failed_queries}")
    print(f"Total time taken:     {total_time_seconds:.2f} seconds")
    print(f"Average throughput:   {avg_throughput:.2f} queries/sec")
    print(f"Average lookup latency: {avg_latency:.2f} ms")
    print("----------------------------\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <domain_list_file.txt>")
        sys.exit(1)

    measure_dns(sys.argv[1])
