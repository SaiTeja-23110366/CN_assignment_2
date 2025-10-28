# CN_assignment_2
# CS331: Custom DNS Resolver in Mininet

This repository contains the code for an assignment to build, test, and analyze a custom DNS resolver in Python using the Mininet network simulation tool.

## Project Objective & Key Findings

The objective of this project was to quantify the performance differences between a professional, public DNS resolver (like Google's) and a custom-built iterative resolver. We also analyzed the performance impact of implementing a DNS cache.

The key findings were:

* **Professional DNS is Fast**: Google's DNS (`8.8.8.8`) served as a fast and reliable baseline, with an average latency of ~150-170ms and a ~99% success rate.
* **Iterative Resolution is Slow**: Our custom non-cached resolver (Part D) was 2.6x slower (avg. latency ~447ms). This is because it had to perform a full iterative query (visiting 3+ servers) for every single lookup.
* **Caching is the Most Important Factor**: Implementing a simple cache (Part F) provided a 7.3x improvement in average latency (dropping from 447ms to 61ms). This demonstrates that caching is the most critical feature for a high-performance DNS resolver.

---

## Files in this Repository

* `topology.py`: The Mininet script to build the custom network topology, including the NAT gateway for internet access.
* `measure_dns.py`: The Python benchmark script that reads domains from a file and measures DNS performance (latency, throughput, success rate).
* `part_d_resolver.py`: (Part D) The custom DNS resolver without caching. It performs iterative resolution and logs data to `part_d_graph_data.csv` for plotting.
* `part_f_resolver.py`: (Part E & F) The final enhanced DNS resolver that implements both recursion and caching, logging cache statistics on exit.
* `plot_graphs.py`: A helper script that uses pandas and matplotlib to automatically generate the `.png` graph files required by the assignment.
* `domains_h*.txt`: The lists of domains extracted from the provided PCAP files, used by `measure_dns.py` for benchmarking.
* `CN_Assignment_2_Report.pdf`: The final detailed report.

---

## Setup & Prerequisites

Before running the simulation, you must install all required dependencies on your Ubuntu VM.

1.  **Install Mininet** (from source, as `apt` version may be unstable):
    ```bash
    git clone [https://github.com/mininet/mininet](https://github.com/mininet/mininet)
    cd mininet
    sudo util/install.sh -a
    cd ..
    ```

2.  **Install Open vSwitch Controller** (This is the critical fix for Part A):
    ```bash
    sudo apt-get install openvswitch-testcontroller
    ```

3.  **Install Core Network & DNS Tools**:
    ```bash
    sudo apt-get install tshark dnsutils python3-pip
    ```

4.  **Install Required Python Libraries**:
    ```bash
    pip3 install dnslib
    sudo apt-get install python3-pandas python3-matplotlib
    ```

5.  **Enable IP Forwarding** (Required for the NAT to work):
    ```bash
    echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
    ```

---

## How to Run the Assignment

Follow these steps in order to replicate the results from the report. Always run `sudo mn -c` before starting a new test.

### Part B: Baseline (Google DNS)

1.  Run `sudo mn -c`
2.  Run `sudo ./topology.py`
3.  At the `mininet>` prompt, configure hosts to use Google DNS:
    ```bash
    mininet> h1 echo 'nameserver 8.8.8.8' > /etc/resolv.conf
    mininet> h2 echo 'nameserver 8.8.8.8' > /etc/resolv.conf
    mininet> h3 echo 'nameserver 8.8.8.8' > /etc/resolv.conf
    mininet> h4 echo 'nameserver 8.8.8.8' > /etc/resolv.conf
    ```
4.  Run the benchmark on all hosts:
    ```bash
    mininet> h1 ./measure_dns.py domains_h1.txt
    mininet> h2 ./measure_dns.py domains_h2.txt
    mininet> h3 ./measure_dns.py domains_h3.txt
    mininet> h4 ./measure_dns.py domains_h4.txt
    ```
5.  Type `exit`.

### Part C & D: Custom Resolver (No Cache) & Graphing

1.  Run `sudo mn -c`
2.  Run `sudo ./topology.py`
3.  At the `mininet>` prompt, start the Part D resolver in the background:
    ```bash
    mininet> dns python3 ./part_d_resolver.py > dns_server_d.log 2>&1 &
    ```
4.  Wait 3 seconds for the server to start: `mininet> py time.sleep(3)`
5.  Configure hosts to use the custom resolver (Part C):
    ```bash
    mininet> h1 echo 'nameserver 10.0.0.5' > /etc/resolv.conf
    mininet> h2 echo 'nameserver 10.0.0.5' > /etc/resolv.conf
    mininet> h3 echo 'nameserver 10.0.0.5' > /etc/resolv.conf
    mininet> h4 echo 'nameserver 10.0.0.5' > /etc/resolv.conf
    ```
6.  Run the benchmark on all hosts (this will be slow):
    ```bash
    mininet> h1 ./measure_dns.py domains_h1.txt
    mininet> h2 ./measure_dns.py domains_h2.txt
    mininet> h3 ./measure_dns.py domains_h3.txt
    mininet> h4 ./measure_dns.py domains_h4.txt
    ```
7.  Type `exit`.
8.  Back in your main terminal, generate the graphs for Part D:
    ```bash
    python3 ./plot_graphs.py
    ```
    This will create `part_d_latency_graph.png` and `part_d_servers_graph.png`.

### Part E & F: Custom Resolver (With Caching)

1.  Run `sudo mn -c`
2.  Run `sudo ./topology.py`
3.  At the `mininet>` prompt, start the final Part F (caching) resolver:
    ```bash
    mininet> dns python3 ./part_f_resolver.py > dns_server_f.log 2>&1 &
    ```
4.  Wait 3 seconds: `mininet> py time.sleep(3)`
5.  Configure host h1:
    ```bash
    mininet> h1 echo 'nameserver 10.0.0.5' > /etc/resolv.conf
    ```
6.  Run the "Cold Cache" benchmark:
    ```bash
    mininet> h1 ./measure_dns.py domains_h1.txt
    ```
7.  Immediately run the "Warm Cache" benchmark:
    ```bash
    mininet> h1 ./measure_dns.py domains_h1.txt
    ```
8.  Observe the dramatically improved latency and total time in the second run.
9.  Find the server's PID:
    ```bash
    mininet> dns ps -ef | grep python3
    ```
    (Find the PID for `part_f_resolver.py`, e.g., 12345)
10. Send the correct interrupt signal (`-2`) to get the cache stats:
    ```bash
    mininet> dns kill -2 <PID_NUMBER_HERE>
    ```
11. Check the log for the cache statistics:
    ```bash
    mininet> dns tail dns_server_f.log
    ```
12. Type `exit`.
