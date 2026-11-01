from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class CampusTopo(Topo):

    def build(self):

        switch1 = self.addSwitch('s1', failMode='standalone')

        departments = {
            'cs': {
                'vlan': 10,
                'hosts': ['10.0.1.1/24', '10.0.1.2/24']
            },
            'it': {
                'vlan': 20,
                'hosts': ['10.0.2.1/24', '10.0.2.2/24']
            },
            'ece': {
                'vlan': 30,
                'hosts': ['10.0.3.1/24', '10.0.3.2/24']
            },
            'mech': {
                'vlan': 40,
                'hosts': ['10.0.4.1/24', '10.0.4.2/24']
            },
            'faculty': {
                'vlan': 50,
                'hosts': ['10.0.5.1/24', '10.0.5.2/24']
            },
            'admin': {
                'vlan': 60,
                'hosts': ['10.0.6.1/24', '10.0.6.2/24']
            }
        }

        for department, details in departments.items():

            for index, ip in enumerate(details['hosts'], start=1):

                host = self.addHost(
                    f'{department}{index}',
                    ip=ip
                )

                self.addLink(host, switch1)


if __name__ == '__main__':

    setLogLevel('info')

    topo = CampusTopo()

    net = Mininet(
        topo=topo,
        controller=None,
        autoSetMacs=True
    )

    info('\n*** Starting Campus Network\n')

    net.start()

    info('\n*** Campus Network Started\n')

    CLI(net)

    net.stop()
