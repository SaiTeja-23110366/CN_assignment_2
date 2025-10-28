#!/usr/bin/python3

import pandas as pd
import matplotlib.pyplot as plt
import sys

def create_plots(csv_file, prefix):
    # Read the CSV data using pandas
    try:
        data = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: Could not find the file {csv_file}")
        return

    # --- THIS IS YOUR IDEA! ---
    # Filter data to only include queries from h1 (10.0.0.1)
    h1_data = data[data['ClientIP'] == '10.0.0.1'].copy()

    if h1_data.empty:
        print(f"Error: No data found for client '10.0.0.1' in {csv_file}")
        return

    # Select the first 10 rows from the *filtered* data
    # This works because h1 sends its queries in order
    first_10_data = h1_data.head(10)

    # Get the domain names for the x-axis labels
    domains = first_10_data['Domain']

    # --- 1. Create Latency Graph ---
    latencies = first_10_data['TotalTime_ms']
    plt.figure(figsize=(12, 7)) 
    plt.bar(domains, latencies, color='blue')
    plt.title(f'{prefix}: DNS Latency (First 10 Queries from H1)')
    plt.xlabel('Domain Name')
    plt.ylabel('Latency (ms)')
    plt.xticks(rotation=45, ha='right') 
    plt.tight_layout() 

    latency_filename = f"{prefix}_latency_graph.png"
    plt.savefig(latency_filename)
    print(f"Successfully saved: {latency_filename}")


    # --- 2. Create Servers Visited Graph ---
    servers = first_10_data['ServersVisited']
    plt.figure(figsize=(12, 7)) 
    plt.bar(domains, servers, color='green')
    plt.title(f'{prefix}: Servers Visited (First 10 Queries from H1)')
    plt.xlabel('Domain Name')
    plt.ylabel('Number of Servers Visited')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    servers_filename = f"{prefix}_servers_graph.png"
    plt.savefig(servers_filename)
    print(f"Successfully saved: {servers_filename}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'part_f':
        # This is how we'll run it for Part F later
        create_plots('part_f_graph_data.csv', 'part_f')
    else:
        # This is the default, for Part D
        create_plots('part_d_graph_data.csv', 'part_d')
