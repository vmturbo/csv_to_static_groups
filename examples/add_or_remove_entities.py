'''
    Script that shows how to perform incremental adds/removals without knowing
    all current members of the group.
'''
import vmtconnect as vconn
from csv_to_static_groups import StaticGroup

TARGET_GROUP_NAME = "Sample_Group"
ENTITY_TYPE = "VirtualMachine"
ADD_ENTITIES = ["SampleVM1", "SampleVM2"]

REMOVE_ENTITIES = ["SampleVM2"]


DRYRUN = False

# Credentials
TURBO_TARGET = "localhost"
TURBO_USER = "administrator"
TURBO_PASS = ""
TURBO_CREDS = b""

# Establish Turbonomic Connection
conn = vconn.VMTConnection(TURBO_TARGET, TURBO_USER, TURBO_PASS, TURBO_CREDS)

# Instantiate group
group = StaticGroup(conn, TARGET_GROUP_NAME, ENTITY_TYPE)

 Add Entities
group.add_entities(ADD_ENTITIES, lookup_names=True, case_sensitive=False,
                   dryrun=DRYRUN)

 Remove Entities
group.remove_entities(REMOVE_ENTITIES, lookup_names=True, case_sensitive=False,
                      dryrun=DRYRUN)

# Overwrite Members
group.members = ["SampleVM1"]
group.update(lookup_names=True, case_sensitive=False, dryrun=DRYRUN)
