import os
import xml.etree.ElementTree as ET
from pathlib import Path

from dotenv import load_dotenv
from ncclient import manager


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

NETCONF_HOST = os.getenv("NETCONF_HOST", "127.0.0.1")
NETCONF_PORT = int(os.getenv("NETCONF_PORT", "830"))
NETCONF_USER = os.getenv("NETCONF_USER", "root")
NETCONF_PASSWORD = os.getenv("NETCONF_PASSWORD")

CAMPUS_NS = "urn:campus:network"
NETCONF_NS = "urn:ietf:params:xml:ns:netconf:base:1.0"

ET.register_namespace("campus", CAMPUS_NS)


def get_connection():
    if not NETCONF_PASSWORD:
        raise RuntimeError("NETCONF_PASSWORD is not configured")

    return manager.connect(
        host=NETCONF_HOST,
        port=NETCONF_PORT,
        username=NETCONF_USER,
        password=NETCONF_PASSWORD,
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        device_params={"name": "default"},
        timeout=30
    )


def get_departments():
    with get_connection() as connection:
        filter_xml = f"""
        <campus-network xmlns="{CAMPUS_NS}"/>
        """

        response = connection.get_config(
            source="running",
            filter=("subtree", filter_xml)
        )

        root = ET.fromstring(response.xml)
        namespace = {"campus": CAMPUS_NS}

        departments = []

        for department in root.findall(
            ".//campus:departments", namespace
        ):
            members = []

            for member in department.findall(
                "campus:members", namespace
            ):
                members.append({
                    "name": member.findtext(
                        "campus:name",
                        namespaces=namespace
                    ),
                    "ip_address": member.findtext(
                        "campus:ip-address",
                        namespaces=namespace
                    ),
                    "switch_port": int(member.findtext(
                        "campus:switch-port",
                        namespaces=namespace
                    ))
                })

            departments.append({
                "name": department.findtext(
                    "campus:name",
                    namespaces=namespace
                ),
                "vlan_id": int(department.findtext(
                    "campus:vlan-id",
                    namespaces=namespace
                )),
                "subnet": department.findtext(
                    "campus:subnet",
                    namespaces=namespace
                ),
                "members": members
            })

        return departments


def get_policies():
    with get_connection() as connection:
        filter_xml = f"""
        <campus-network xmlns="{CAMPUS_NS}"/>
        """

        response = connection.get_config(
            source="running",
            filter=("subtree", filter_xml)
        )

        root = ET.fromstring(response.xml)
        namespace = {"campus": CAMPUS_NS}

        policies = []

        for policy in root.findall(
            ".//campus:policies", namespace
        ):
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


def update_policy_action(policy_name, action):
    if action not in ["allow", "block"]:
        raise ValueError("Action must be allow or block")

    config_root = ET.Element(
        f"{{{NETCONF_NS}}}config"
    )

    campus_network = ET.SubElement(
        config_root,
        f"{{{CAMPUS_NS}}}campus-network"
    )

    policy = ET.SubElement(
        campus_network,
        f"{{{CAMPUS_NS}}}policies"
    )

    ET.SubElement(
        policy,
        f"{{{CAMPUS_NS}}}name"
    ).text = policy_name

    ET.SubElement(
        policy,
        f"{{{CAMPUS_NS}}}action"
    ).text = action

    config = ET.tostring(
        config_root,
        encoding="unicode"
    )

    with get_connection() as connection:
        connection.edit_config(
            target="running",
            config=config
        )

        connection.copy_config(
            source="running",
            target="startup"
        )

        return True
def upsert_policy(policy_name, source, destination, action, enabled=True):

    if action not in ["allow", "block"]:
        raise ValueError("Action must be allow or block")

    config_root = ET.Element(
        f"{{{NETCONF_NS}}}config"
    )

    campus_network = ET.SubElement(
        config_root,
        f"{{{CAMPUS_NS}}}campus-network"
    )

    policy = ET.SubElement(
        campus_network,
        f"{{{CAMPUS_NS}}}policies"
    )

    ET.SubElement(
        policy,
        f"{{{CAMPUS_NS}}}name"
    ).text = policy_name

    ET.SubElement(
        policy,
        f"{{{CAMPUS_NS}}}action"
    ).text = action

    ET.SubElement(
        policy,
        f"{{{CAMPUS_NS}}}source"
    ).text = source

    ET.SubElement(
        policy,
        f"{{{CAMPUS_NS}}}destination"
    ).text = destination

    ET.SubElement(
        policy,
        f"{{{CAMPUS_NS}}}enabled"
    ).text = str(enabled).lower()

    config = ET.tostring(
        config_root,
        encoding="unicode"
    )

    with get_connection() as connection:

        connection.edit_config(
            target="running",
            config=config
        )

        connection.copy_config(
            source="running",
            target="startup"
        )

    return True
def delete_policy(policy_name):
    config_root = ET.Element(
        f"{{{NETCONF_NS}}}config"
    )

    campus_network = ET.SubElement(
        config_root,
        f"{{{CAMPUS_NS}}}campus-network"
    )

    policy = ET.SubElement(
        campus_network,
        f"{{{CAMPUS_NS}}}policies",
        {
            f"{{{NETCONF_NS}}}operation": "delete"
        }
    )

    ET.SubElement(
        policy,
        f"{{{CAMPUS_NS}}}name"
    ).text = policy_name

    config = ET.tostring(
        config_root,
        encoding="unicode"
    )

    with get_connection() as connection:

        connection.edit_config(
            target="running",
            config=config
        )

        connection.copy_config(
            source="running",
            target="startup"
        )

    return True
