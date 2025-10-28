#!/usr/bin/python3

from mininet.net import Mininet
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.nodelib import NAT  # <--- NEW: Import the NAT class

def create_topology():
    """Create the custom network topology."""

    net = Mininet(controller=OVSController, link=TCLink)

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/8')
    h2 = net.addHost('h2', ip='10.0.0.2/8')
    h3 = net.addHost('h3', ip='10.0.0.3/8')
    h4 = net.addHost('h4', ip='10.0.0.4/8')
    dns = net.addHost('dns', ip='10.0.0.5/8')

    info('*** Adding NAT gateway\n')  # <--- NEW
    # Add a NAT node to connect the virtual network to the host's internet
    # We give it an IP in our network (10.0.0.254)
    # 'inNamespace=False' means it lives in the root VM, not a virtual namespace
    nat = net.addHost('nat', cls=NAT, ip='10.0.0.254/8', inNamespace=False)

    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')

    info('*** Creating links\n')
    # Host to Switch links
    net.addLink(h1, s1, bw=100, delay='2ms') 
    net.addLink(h2, s2, bw=100, delay='2ms') 
    net.addLink(h3, s3, bw=100, delay='2ms') 
    net.addLink(h4, s4, bw=100, delay='2ms') 

    # Switch to Switch links
    net.addLink(s1, s2, bw=100, delay='5ms') 
    net.addLink(s2, s3, bw=100, delay='8ms') 
    net.addLink(s3, s4, bw=100, delay='10ms')

    # DNS Resolver to Switch link
    net.addLink(dns, s2, bw=100, delay='1ms') 

    # NAT gateway to Switch link
    net.addLink(nat, s2, bw=100) # <--- NEW: Connect the NAT node to s2

    info('*** Starting network\n')
    net.start()

    info('*** Setting default routes for hosts\n') # <--- NEW
    # Tell hosts how to reach the internet (via the NAT node's IP)
    # We also do this for 'dns' host, as it will need internet in Part D
    for host in [h1, h2, h3, h4, dns]:
        host.setDefaultRoute(f'via {nat.IP()}')

    info('*** Testing connectivity\n')
    net.pingAll()

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_topology()
