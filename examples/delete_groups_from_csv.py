'''
    Script that deletes group from a csv.
'''
import vmtconnect as vconn
from csv_to_static_groups import CSVGroupParser, StaticGroup, MissingUUIDError

# Credentials
TURBO_TARGET = "localhost"
TURBO_USER = "administrator"
TURBO_PASS = ""
TURBO_CREDS = b""

ENTITY_TYPE_HEADER = "Entity Type"
ENTITY_NAME_HEADER = "Entity Name"

PATH_TO_CSV = ""

# Establish Turbonomic Connection
conn = vconn.VMTConnection(TURBO_TARGET, TURBO_USER, TURBO_PASS,
                           TURBO_CREDS)

# Instantiate parser
csv_group_parser = CSVGroupParser(ENTITY_TYPE_HEADER, ENTITY_NAME_HEADER)

# Parse PATH_TO_CSV
groups = csv_group_parser.parse(PATH_TO_CSV)

for group in groups:
    # Instantiate a new StaticGroup
    group_instance = StaticGroup(conn, group["name"], group["entity_type"])
    try:
        # Attempt Removal
        group_instance.remove()
    except MissingUUIDError as e:
        print("Unable to delete group: {}".format(e))
        pass
    except Exception as e:
        print("Unhandled exception")
        raise
