'''
    Script that creates an "anti-group", or a group with every entity that was
    not specified for a group in the csv.
'''
import vmtconnect as vconn
from csv_to_static_groups import CSVGroupParser, StaticGroup

DRYRUN = True
PATH_TO_CSV = ""

# Credentials
TURBO_TARGET = "localhost"
TURBO_USER = "administrator"
TURBO_PASS = ""
TURBO_CREDS = b""

# CSV Parsing Variables
ENTITY_TYPE_HEADER = "Entity Type"
ENTITY_NAME_HEADER = "Entity Name"

# Establish Turbonomic Connection
conn = vconn.VMTConnection(TURBO_TARGET, TURBO_USER, TURBO_PASS, TURBO_CREDS)

# Instantiate parser
csv_group_parser = CSVGroupParser(ENTITY_TYPE_HEADER, ENTITY_NAME_HEADER)

# Parse PATH_TO_CSV
groups = csv_group_parser.parse(PATH_TO_CSV)

# Get all entity types found in csv
all_entity_types = list(set([g["entity_type"] for g in groups]))

# Get all entities from Turbonomic
entities = conn.search(types=all_entity_types)

for group in groups:
    group_instance = StaticGroup(conn, group["name"], group["entity_type"])

    # All Entity Names
    all_entity_names = [e["displayName"] for e in entities if e["className"] == group["entity_type"]]

    # Calculate all vms that are not in csv group members.
    anti_members = list(set(all_entity_names).difference(set(group["members"])))

    # Set group_instance.members to anti_members
    group_instance.members = anti_members

    # Commit Changes
    group_instance.add_or_update(lookup_names=True)
