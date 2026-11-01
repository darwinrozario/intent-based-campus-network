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
        print("Session ID:", connection.session_id)
        print("Server capabilities:")

        for capability in connection.server_capabilities:
            print(capability)

except Exception as error:
    print("Connection failed:", repr(error))
