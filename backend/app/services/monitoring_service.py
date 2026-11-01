
import subprocess
import re

SWITCH = "s1"
APP_COOKIE = "0xcace"


def run_command(command):
    result = subprocess.run(
        ["sudo"] + command,
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout


def get_switch_status():
    run_command([
        "ovs-vsctl",
        "br-exists",
        SWITCH
    ])

    return "OPERATIONAL"


def get_switch_ports():

    output = run_command([
        "ovs-ofctl",
        "show",
        SWITCH
    ])

    ports = []

    for line in output.splitlines():

        match = re.match(
            r"\s*(\d+)\(([^)]+)\):",
            line
        )

        if match:
            ports.append({
                "port": int(match.group(1)),
                "interface": match.group(2),
                "status": "UP"
            })

    return ports


def get_port_statistics():

    output = run_command([
        "ovs-ofctl",
        "dump-ports",
        SWITCH
    ])

    port_statistics = []
    current_port = None

    for line in output.splitlines():

        port_match = re.search(
            r"port\s+(\d+):",
            line
        )

        if port_match:
            current_port = {
                "port": int(port_match.group(1))
            }
            port_statistics.append(current_port)

        elif current_port is not None:

            rx_match = re.search(
                r"rx pkts=(\d+), bytes=(\d+)",
                line
            )

            tx_match = re.search(
                r"tx pkts=(\d+), bytes=(\d+)",
                line
            )

            if rx_match:
                current_port["rx_packets"] = int(rx_match.group(1))
                current_port["rx_bytes"] = int(rx_match.group(2))

            if tx_match:
                current_port["tx_packets"] = int(tx_match.group(1))
                current_port["tx_bytes"] = int(tx_match.group(2))

    return port_statistics


def get_flow_statistics():

    output = run_command([
        "ovs-ofctl",
        "dump-flows",
        SWITCH
    ])

    active_blocking_rules = 0
    total_packets = 0
    total_bytes = 0
    dropped_packets = 0
    flow_details = []

    for line in output.splitlines():

        if APP_COOKIE not in line.lower():
            continue

        packet_match = re.search(
            r"n_packets=(\d+)",
            line
        )

        byte_match = re.search(
            r"n_bytes=(\d+)",
            line
        )

        packets = int(packet_match.group(1)) if packet_match else 0
        bytes_count = int(byte_match.group(1)) if byte_match else 0

        total_packets += packets
        total_bytes += bytes_count

        is_blocking = "actions=drop" in line.lower()

        if is_blocking:
            active_blocking_rules += 1
            dropped_packets += packets

        flow_details.append({
            "packets": packets,
            "bytes": bytes_count,
            "action": "BLOCK" if is_blocking else "ALLOW",
            "rule": line.strip()
        })

    return {
        "active_blocking_rules": active_blocking_rules,
        "total_packets": total_packets,
        "total_bytes": total_bytes,
        "dropped_packets": dropped_packets,
        "flow_details": flow_details
    }


def get_network_metrics():

    return {
        "switch": SWITCH,
        "status": get_switch_status(),
        "ports": get_switch_ports(),
        "port_statistics": get_port_statistics(),
        "flow_statistics": get_flow_statistics()
    }

