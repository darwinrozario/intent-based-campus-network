from ncclient import manager
from getpass import getpass

password = getpass("Enter NETCONF root password: ")

config = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <campus-network xmlns="urn:campus:network">
        <policies>
            <name>block-student-admin</name>
            <action>allow</action>
            <source>student</source>
            <destination>administration</destination>
            <enabled>true</enabled>
        </policies>
    </campus-network>
</config>
"""

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

        result = connection.edit_config(
            target="running",
            config=config
        )

        print("\nPolicy Configuration Result:")
        print(result.xml)

except Exception as error:
    print("Error:", repr(error))
