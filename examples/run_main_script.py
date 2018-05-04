'''
    Script that runs entire csv_to_static_group logic. This could be used to
    execute csv_to_static_groups within another script.

    Optional Changes:
        QUIET set to False
            - Enables sysout output
        VERBOSE set to True
            - Enables more verbose ouput
        TRK_MISS_ENTITY changed
            -Enables change category string to change
'''
import vmtconnect as vconn
import csv_to_static_groups

PATH_TO_CSV = ""
DRYRUN = True

# Credentials
TURBO_TARGET = "localhost"
TURBO_USER = "administrator"
TURBO_PASS = ""
TURBO_CREDS = b""

# Establish Turbonomic Connection
conn = vconn.VMTConnection(TURBO_TARGET, TURBO_USER, TURBO_PASS,
                           TURBO_CREDS)

# Enable sysout output
csv_to_static_groups.QUIET = False

# Enable verbose output
csv_to_static_groups.VERBOSE = True

# Change change category
csv_to_static_groups.TRK_MISS_ENTITY = "Unable to Find Entities"

# Execute main function
changes = csv_to_static_groups.main(conn, PATH_TO_CSV, dryrun=DRYRUN)

# Print Total Changes
print("\n")
for category, attr in changes.items():
    print("{}: {}".format(category, attr["total"]))
