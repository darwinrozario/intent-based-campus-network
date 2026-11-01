from ncclient import manager
from getpass import getpass
import subprocess
import xml.etree.ElementTree as ET

NETCONF_HOST = "127.0.0.1"
NETCONF_PORT = 830
NETCONF_USER = "root"

SWITCH = "s1"
APP_COOKIE = "0xCACE"

NETWORKS = {
    "student": {
        "ip": "10.0.0.1",
        "port": 1
    },
    "faculty": {
        "ip": "10.0.0.2",
        "port": 2
    },
    "administration": {
        "ip": "10.0.0.3",
        "port": 3
    }
}


def run_ovs_command(command):
    subprocess.run(command, check=True)


def retrieve_policies(password):

    with manager.connect(
        host=NETCONF_HOST,
        port=NETCONF_PORT,
        username=NETCONF_USER,
        password=password,
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        device_params={"name": "default"},
        timeout=30
    ) as connection:

        filter_xml = """
        <campus-network xmlns="urn:campus:network"/>
        """

        response = connection.get_config(
            source="running",
            filter=("subtree", filter_xml)
        )

        root = ET.fromstring(response.xml)

        namespace = {
            "campus": "urn:campus:network"
        }

        policies = []

        for policy in root.findall(".//campus:policies", namespace):

            policies.append({
                "name": policy.findtext(
                    "campus:name",
                    namespaces=namespace
                ),
                "action": policy.findtext(
                    "campus:action",
                    namespaces=namespace
                ),
                "source": policy.findtext(
                    "campus:source",
                    namespaces=namespace
                ),
                "destination": policy.findtext(
                    "campus:destination",
                    namespaces=namespace
                ),
                "enabled": policy.findtext(
                    "campus:enabled",
                    namespaces=namespace
                ) != "false"
            })

        return policies


def validate_policies(policies):

    valid_policies = []

    for policy in policies:

        if not policy["enabled"]:
            print(f"Skipping disabled policy: {policy['name']}")
            continue

        if policy["source"] not in NETWORKS:
            raise ValueError(
                f"Invalid source: {policy['source']}"
            )

        if policy["destination"] not in NETWORKS:
            raise ValueError(
                f"Invalid destination: {policy['destination']}"
            )

        if policy["source"] == policy["destination"]:
            raise ValueError(
                "Source and destination cannot be the same"
            )

        if policy["action"] not in ["allow", "block"]:
            raise ValueError(
                f"Invalid action: {policy['action']}"
            )

        valid_policies.append(policy)

    return valid_policies


def reconcile_policies(policies):

    print("\nStarting policy reconciliation...")

    # Remove only rules managed by this application.
    run_ovs_command([
        "sudo", "ovs-ofctl", "del-flows",
        SWITCH,
        f"cookie={APP_COOKIE}/-1"
    ])

    blocked_pairs = set()

    for policy in policies:

        source = policy["source"]
        destination = policy["destination"]
        action = policy["action"]

        pair = (source, destination)

        if action == "block":
            blocked_pairs.add(pair)

    # Generate and install blocking rules.
    for source, destination in sorted(blocked_pairs):

        source_port = NETWORKS[source]["port"]
        destination_ip = NETWORKS[destination]["ip"]

        flow = (
            f"cookie={APP_COOKIE},"
            f"priority=100,"
            f"in_port={source_port},"
            f"ip,"
            f"nw_dst={destination_ip},"
            f"actions=drop"
        )

        run_ovs_command([
            "sudo", "ovs-ofctl", "add-flow",
            SWITCH,
            flow
        ])

        print(f"BLOCK: {source} -> {destination}")

    # Install default forwarding rule.
    default_flow = (
        f"cookie={APP_COOKIE},"
        f"priority=0,"
        f"actions=NORMAL"
    )

    run_ovs_command([
        "sudo", "ovs-ofctl", "add-flow",
        SWITCH,
        default_flow
    ])

    print("\nPolicy reconciliation completed!")
    print(f"Active blocking rules: {len(blocked_pairs)}")


def main():

    password = getpass("Enter NETCONF root password: ")

    print("\nRetrieving policies from NETCONF...")

    policies = retrieve_policies(password)

    print(f"Retrieved {len(policies)} policies.")

    valid_policies = validate_policies(policies)

    reconcile_policies(valid_policies)


if __name__ == "__main__":
    main()
