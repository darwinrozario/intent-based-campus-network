from ncclient import manager
from getpass import getpass

password = getpass("Enter NETCONF root password: ")

try:
    with manager.connect(
        host="127.0.0.1",
        port=830,
        username="root",
        password=password,
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        device_params={"name": "default"},
        timeout=30
    ) as connection:

        print("NETCONF connection successful!")

        filter_xml = """
        <campus-network xmlns="urn:campus:network"/>
        """

        result = connection.get_config(
            source="running",
            filter=("subtree", filter_xml)
        )

        print("\nCampus Network Configuration:")
        print(result.xml)

except Exception as error:
    print("Error:", repr(error))
