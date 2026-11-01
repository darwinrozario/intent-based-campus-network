import subprocess

SWITCH = "s1"
APP_COOKIE = "0xCACE"

NETWORKS = {
    "computer-science": {
        "subnet": "10.0.1.0/24",
        "router_port": 13,
        "vlan": 10
    },
    "information-technology": {
        "subnet": "10.0.2.0/24",
        "router_port": 14,
        "vlan": 20
    },
    "ece": {
        "subnet": "10.0.3.0/24",
        "router_port": 15,
        "vlan": 30
    },
    "mechanical": {
        "subnet": "10.0.4.0/24",
        "router_port": 16,
        "vlan": 40
    },
    "faculty": {
        "subnet": "10.0.5.0/24",
        "router_port": 17,
        "vlan": 50
    },
    "administration": {
        "subnet": "10.0.6.0/24",
        "router_port": 18,
        "vlan": 60
    }
}


def run_ovs_command(command):

    result = subprocess.run(
        ["sudo"] + command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip()
        )


def validate_policies(policies):

    valid_policies = []

    for policy in policies:

        source = policy.get("source")
        destination = policy.get("destination")
        action = policy.get("action")
        enabled = policy.get("enabled", True)

        if source not in NETWORKS:
            raise ValueError(f"Invalid source department: {source}")

        if destination not in NETWORKS:
            raise ValueError(
                f"Invalid destination department: {destination}"
            )

        if source == destination:
            raise ValueError(
                "Source and destination cannot be the same"
            )

        if action not in {"allow", "block"}:
            raise ValueError(f"Invalid action: {action}")

        if enabled:
            valid_policies.append(policy)

    return valid_policies


def reconcile_policies(policies):

    valid_policies = validate_policies(policies)

    # Remove only OpenFlow rules owned by this application.
    # The baseline 0xBEEF forwarding rule remains untouched.

    run_ovs_command([
        "ovs-ofctl",
        "del-flows",
        SWITCH,
        f"cookie={APP_COOKIE}/-1"
    ])

    blocked_pairs = set()

    for policy in valid_policies:

        if policy["action"] == "block":

            blocked_pairs.add((
                policy["source"],
                policy["destination"]
            ))

    # Install directional blocking rules.

    for source, destination in sorted(blocked_pairs):

        source_subnet = NETWORKS[source]["subnet"]

        destination_subnet = NETWORKS[destination]["subnet"]

        destination_router_port = NETWORKS[destination]["router_port"]

        flow = (
            f"cookie={APP_COOKIE},"
            f"priority=200,"
            f"in_port={destination_router_port},"
            f"ip,"
            f"nw_src={source_subnet},"
            f"nw_dst={destination_subnet},"
            f"actions=drop"
        )

        run_ovs_command([
            "ovs-ofctl",
            "add-flow",
            SWITCH,
            flow
        ])

    return {
        "status": "APPLIED",
        "active_blocking_rules": len(blocked_pairs),
        "blocked_pairs": [
            {
                "source": source,
                "destination": destination
            }
            for source, destination in sorted(blocked_pairs)
        ]
    }
