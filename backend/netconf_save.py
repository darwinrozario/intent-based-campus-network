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

        connection.copy_config(
            source="running",
            target="startup"
        )

        print("Configuration saved to startup datastore!")

except Exception as error:
    print("Error:", repr(error))
