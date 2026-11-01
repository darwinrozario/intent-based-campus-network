from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import Node
import subprocess


class LinuxRouter(Node):

    def config(self, **params):
        super().config(**params)

        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        self.cmd("sysctl -w net.ipv4.conf.all.rp_filter=0")

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()


class CampusTopo(Topo):

    def build(self):

        switch1 = self.addSwitch(
            's1',
            failMode='secure'
        )

        departments = {
            'cs': {
                'vlan': 10,
                'gateway': '10.0.1.254/24',
                'hosts': ['10.0.1.1/24', '10.0.1.2/24']
            },
            'it': {
                'vlan': 20,
                'gateway': '10.0.2.254/24',
                'hosts': ['10.0.2.1/24', '10.0.2.2/24']
            },
            'ece': {
                'vlan': 30,
                'gateway': '10.0.3.254/24',
                'hosts': ['10.0.3.1/24', '10.0.3.2/24']
            },
            'mech': {
                'vlan': 40,
                'gateway': '10.0.4.254/24',
                'hosts': ['10.0.4.1/24', '10.0.4.2/24']
            },
            'faculty': {
                'vlan': 50,
                'gateway': '10.0.5.254/24',
                'hosts': ['10.0.5.1/24', '10.0.5.2/24']
            },
            'admin': {
                'vlan': 60,
                'gateway': '10.0.6.254/24',
                'hosts': ['10.0.6.1/24', '10.0.6.2/24']
            }
        }

        router = self.addNode(
            'r1',
            cls=LinuxRouter,
            ip=None
        )

        # Create the 12 department hosts.
        # Mininet automatically assigns switch ports 1-12.

        for department, details in departments.items():

            for index, ip in enumerate(
                details['hosts'],
                start=1
            ):

                host = self.addHost(
                    f'{department}{index}',
                    ip=ip,
                    defaultRoute=f"via {details['gateway'].split('/')[0]}"
                )

                self.addLink(host, switch1)

        # Connect the router to the switch.
        # These links automatically receive switch ports 13-18.

        for index, department in enumerate(departments):

            self.addLink(
                router,
                switch1,
                intfName1=f'r1-eth{index}'
            )


def configure_vlan():

    info('\n*** Configuring VLANs\n')

    vlan_ids = [10, 20, 30, 40, 50, 60]

    for index, vlan in enumerate(vlan_ids):

        # Two department host ports per VLAN.

        for host_index in range(2):

            switch_port = (index * 2) + host_index + 1

            subprocess.run(
                [
                    'ovs-vsctl',
                    'set',
                    'port',
                    f's1-eth{switch_port}',
                    f'tag={vlan}'
                ],
                check=True
            )

        # One router port per VLAN.

        router_port = 13 + index

        subprocess.run(
            [
                'ovs-vsctl',
                'set',
                'port',
                f's1-eth{router_port}',
                f'tag={vlan}'
            ],
            check=True
        )


def configure_router(router):

    info('\n*** Configuring Router Interfaces\n')

    gateways = [
        '10.0.1.254/24',
        '10.0.2.254/24',
        '10.0.3.254/24',
        '10.0.4.254/24',
        '10.0.5.254/24',
        '10.0.6.254/24'
    ]

    for index, gateway in enumerate(gateways):

        interface = f'r1-eth{index}'

        router.cmd(
            f'ip addr add {gateway} dev {interface}'
        )

        router.cmd(
            f'ip link set {interface} up'
        )


def configure_openflow():

    info('\n*** Installing Baseline OpenFlow Rule\n')

    subprocess.run(
        [
            'ovs-ofctl',
            'add-flow',
            's1',
            'cookie=0xBEEF,priority=0,actions=NORMAL'
        ],
        check=True
    )


def start_network():

    setLogLevel('info')

    topo = CampusTopo()

    net = Mininet(
        topo=topo,
        controller=None,
        autoSetMacs=True
    )

    try:

        info('\n*** Starting Campus Network\n')

        net.start()

        router = net.get('r1')

        configure_vlan()

        configure_router(router)

        configure_openflow()

        info('\n*** Campus Network Started Successfully\n')

        info('\n*** Available Departments:\n')
        info('Computer Science       - VLAN 10\n')
        info('Information Technology - VLAN 20\n')
        info('ECE                    - VLAN 30\n')
        info('Mechanical              - VLAN 40\n')
        info('Faculty                 - VLAN 50\n')
        info('Administration          - VLAN 60\n')

        CLI(net)

    finally:

        info('\n*** Stopping Campus Network\n')

        net.stop()


if __name__ == '__main__':
    start_network()
