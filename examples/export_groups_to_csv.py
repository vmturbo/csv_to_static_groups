#! /usr/bin/python3
import vmtconnect as vconn
import csv_to_static_groups
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from enum import Enum
import argparse
from getpass import getpass
import csv
import sys

__version__ = "1.0.2"

class CSV_HEADER(Enum):
    entity_type = "Entity Type"
    entity_name = "Entity Name"
    group_name = "Group Name"
    group_type = "Group Type"

    @classmethod
    def get_values(self):
        values = []
        for i in self:
            if i.name.startswith("_"):
                continue
            values.append(i.value)
        return values

def write_csv(outfile, data, fieldnames):
    with open(outfile, "w") as _file:
        writer = csv.DictWriter(_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def get_custom_groups(conn):
    return conn.request("/groups/GROUP-MyGroups/members")

def bool_to_group_type(bool):
    if bool:
        return "Static"
    else:
        return "Dynamic"

def main(conn, output_csv, include_group_type=False, all_groups=False):
    all_group_members = []
    if all_groups:
        all_groups = conn.get_groups()
    else:
        all_groups = get_custom_groups(conn)
    for group in all_groups:
        sgroup = csv_to_static_groups.StaticGroup(conn, group["displayName"], group["groupType"])
        for entity in sgroup.get_current_members():
            cur_entity = {CSV_HEADER.entity_type.value: group["groupType"],
                          CSV_HEADER.group_name.value: group["displayName"],
                          CSV_HEADER.entity_name.value: entity["displayName"]}
            if include_group_type:
                cur_entity[CSV_HEADER.group_type.value] = bool_to_group_type(group["isStatic"])
            all_group_members.append(cur_entity)
    headers = CSV_HEADER.get_values()
    if not include_group_type:
        headers.pop(headers.index(CSV_HEADER.group_type.value))
    else:
        print('Remember to specify "{}" as the only group header if using this csv to import groups.'.format(CSV_HEADER.group_type.value))
    write_csv(output_csv, all_group_members, headers)

if __name__ == "__main__":
    # Credentials
    __TURBO_TARGET = "localhost"
    __TURBO_USER = "administrator"
    __TURBO_PASS = ""
    __TURBO_CREDS = b""

    # Parse Arguments
    arg_parser = argparse.ArgumentParser(description="Create/Update/Delete Static Groups From A CSV File")
    arg_parser.add_argument("output_csv", action="store", help="Path to csv file")
    arg_parser.add_argument("--all_groups", action="store_true", required=False,
                            help="Also export non-custom Turbonomic groups")
    arg_parser.add_argument("--include_group_type", action="store_true", required=False,
                            help="Include a column to indicate if a group is static or dynamic.")
    arg_parser.add_argument("-u", "--username", action="store", required=False,
                            help=("Turbonomic Username, Password will be prompted."))
    arg_parser.add_argument("--encoded_creds", action="store", required=False,
                            help=("Base64 encoded credentials"))
    arg_parser.add_argument("-t", "--target", action="store", required=False,
                            help="Turbonomic server address. Default={}".format(__TURBO_TARGET),
                            default=__TURBO_TARGET)
    arg_parser.add_argument("--ignore_insecure_warning", action="store_true", required=False,
                            help="Suppress insecure HTTPS request warnings")
    arg_parser.add_argument("--config", action="store", required=False,
                            help=("Path to JSON Config file with arguments"))

    # Parse Arguments
    args_dict = vars(arg_parser.parse_args())

    # Overide CLI args if config file is passed
    if args_dict["config"]:
        args_dict = _config_to_args(args_dict["config"], args_dict,
                                    ignore=["config", "input_csv"])

    # Overide credentials if passed as args
    if args_dict["encoded_creds"]:
        __TURBO_CREDS = args_dict["encoded_creds"].encode()
    elif args_dict["username"]:
        __TURBO_USER = args_dict["username"]
        try:
            __TURBO_PASS = getpass()
        except KeyboardInterrupt:
            print("\n")
            sys.exit()
    if args_dict["target"]:
        __TURBO_TARGET = args_dict["target"]

    # Supress insecure HTTPS warnings
    if args_dict["ignore_insecure_warning"]:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    try:
        # Make connection object
        conn = vconn.Session(__TURBO_TARGET, __TURBO_USER, __TURBO_PASS,
                             __TURBO_CREDS)
        __TURBO_USER = __TURBO_PASS = __TURBO_ENC = None

        main(conn, args_dict["output_csv"], args_dict["include_group_type"],
             args_dict["all_groups"])
    except KeyboardInterrupt:
        print("\n")
        pass
    except Exception as e:
        print("Fatal Error: {}".format(e))
