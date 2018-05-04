'''
    Script that adds or updates a static group.
'''
import vmtconnect as vconn
from csv_to_static_groups import StaticGroup

DRYRUN = False

# My Group Variables
GROUP_NAME = "Sample_Group"
ENTITY_TYPE = "VirtualMachine"
MEMBERS = ["SampleVM1", "SampleVM2"]

# Credentials
TURBO_TARGET = "localhost"
TURBO_USER = ""
TURBO_PASS = ""
TURBO_CREDS = b""

# Establish Turbonomic Connection
conn = vconn.VMTConnection(TURBO_TARGET, TURBO_USER, TURBO_PASS, TURBO_CREDS)

# Build Group
group = StaticGroup(conn, GROUP_NAME, ENTITY_TYPE, MEMBERS)
group.add_or_update(lookup_names=True, dryrun=DRYRUN, case_sensitive=True)
