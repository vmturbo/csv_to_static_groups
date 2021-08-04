#! /usr/bin/env python
import vmtconnect as vconn
import csv
import argparse
from getpass import getpass
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import logging
import traceback
from logging.handlers import RotatingFileHandler
import sys
import json
from functools import wraps

__version__ = "1.1.5"

## ----------------------------------------------------
##   Global Variables
## ----------------------------------------------------

# _msg Variables
LOGGER = None
QUIET = True
TRACE = True
WARN = True

# _EventTracker Categories
TRK_DELETE = "Deleted"
TRK_ERROR = "Errors"
TRK_MISS_ENTITY = "Missing Entities"
TRK_ADD = "Added"
TRK_UPDATE = "Updated"
TRK_SKIP = "Skipped"

# GroupParser Variables
ENTITY_TYPE_HEADER = "Entity Type"
ENTITY_NAME_HEADER = "Entity Name"
GROUP_DELIMITER = "_"

## ----------------------------------------------------
##   Error Classes
## ----------------------------------------------------

# CSVGroupParser Exceptions
class CSVGroupParserError(Exception):
    """Base CSVGroupParser Exception.
    """
    pass

class MissingHeaderError(CSVGroupParserError):
    """Raised if a specified header is missing.
    """
    pass

# StaticGroup Exceptions
class StaticGroupError(Exception):
    """Base StaticGroup Exception.
    """
    pass

class GroupAlreadyExistsError(StaticGroupError):
    """Raised when attempting to add a group that already exists.
    """
    pass

class MissingUUIDError(StaticGroupError):
    """Base StaticGroup Missing UUID Exception.
    """
    pass

class NoMatchingGroupError(MissingUUIDError):
    """Raised when attempting to update/remove a group that does not exist.
    """
    pass

class DuplicateMatchingGroupError(MissingUUIDError):
    """Raised when attempting to update/remove a group where mutliple groups
    share the same name.
    """
    pass

class LookupNameError(StaticGroupError):
    """Base StaticGroup Lookup Name Exception.
    """
    pass

class NameMatchError(LookupNameError):
    """Raised if an entity can't be found by name.
    """
    pass

class MultipleMatchingNamesError(LookupNameError):
    """Raised if an entity name is found more than once in the target server.
    """
    pass

## ----------------------------------------------------
##   Classes
## ----------------------------------------------------

class GroupUpdateUtility(object):
    """
        Utility Object to simplify common group update tasks
    """

    def __init__(self, conn):
        self._conn = conn

    @staticmethod
    def _index_objects(key, values, objects, case_sensitive=True):
        """Creates dictionary of objects from a list of objects for quick look up.

        Args:
            key (str): Object atribute to be used as index key.
            values (list): Object atributes to be included in dictionary.
            objects (list): List of dictionaries.
            case_sensitive (bool, optional): If False, keys will be converted
                to lowercase

        Returns:
            Dictionary where values are lists of all entries whose 'key'
            matched.

            {"key": [{object1_values}, {object2_values}]}
        """
        index = {}
        for member in objects:
            index_key = member[key]
            if not case_sensitive:
                index_key = index_key.lower()
            if len(values) == 0:
                # Include all member attributes as values
                v = member.keys()
            else:
                v = values
            entry = {value: member[value] for value in v}
            if index_key not in index:
                index[index_key] = [entry]
            else:
                index[index_key].append([entry])
        return index

    def get_group_index(self, key="displayName", values=["uuid"]):
        """Creates an index of group values based on a group key.

        Args:
            key (str, optional): Key to index on,
            values (list, optional): Value keys to include in values. If empty,
                all values are included.

        Returns:
            Dictionary::

            {
                "groupName": [{values}, {values}]
            }
        """
        all_groups = self._conn.get_groups()
        return self._index_objects(key, values, all_groups)

    def get_entity_index(self, entity_types, key="displayName", values=[],
                         case_sensitive=True):
        """Creates an index of entities based on a group key.

        Args:
            entity_types (list): List of entity_types,
            key (str, optional): Key to index on.
            values (list, optional): Value keys to include in values. If empty,
                all values are included.
            case_sensitive (bool, optional): Group entities with/without case
                sensitivity

        Returns:
            Dictionary::

            {
                "entity type": {"entity_key": [{values}, {values}]}
            }
        """
        index = {}
        all_entities = self._conn.search(types=entity_types)
        for e_type in entity_types:
            e = [e for e in all_entities if e["className"] == e_type]
            index[e_type] = self._index_objects(key, values, e,
                                                case_sensitive=case_sensitive)
        return index

    def get_group_diff(self, group_uuid, utd_members, key="uuid"):
        """Calculates uuids to add and remove to match current group with "utd".

        Args:
            group_uuid (str): Target group uuid.
            utd_members (list): List of desired up to date uuids.
            key (str, optional): Key to compare members by.

        Returns:
            Dictionary::

            {
                "add": ["uuid", "uuid"],
                "remove": ["uuid", "uuid"]
            }
        """
        diffs = {}
        cur_members = [e[key] for e in self._conn.get_group_members(group_uuid)]
        diffs["add"] = list(set(utd_members).difference(set(cur_members)))
        diffs["remove"] = list(set(cur_members).difference(set(utd_members)))
        return diffs

class CSVGroupParser(object):
    """
        Parses a CSV and returns groupings based on headers

        Args:
            entity_type_header (str): Header for the column that contains the
                entity types.
            entity_name_header (str): Header for the column that contains the
                entity names.
            group_delimiter (str): String to separate group column values.
            group_prefix (str): String to prepend group name.
    """

    def __init__(self, entity_type_header, entity_name_header, group_delimiter="_",
                 group_prefix=""):
        self.entity_type_header = entity_type_header
        self.entity_name_header = entity_name_header
        self.group_delimiter = group_delimiter
        self.group_prefix = group_prefix

    @staticmethod
    def _read_csv(file_path):
        """Read CSV file

        Args:
            file_path (str): Path to CSV files

        Returns:
            List of dictionaries with CSV file headers as the keys
        """
        with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            return [row for row in reader]

    @staticmethod
    def _group_values_by_key(dicts, group_keys, value_keys,
                             group_prefix="", group_delimiter="_"):
        """Groups value_keys that share the same group_key values.

        Args:
            dicts (list): List of dictionaries
            group_keys (list): List of dictionary keys to group by.
            value_keys (list): Dictionary keys for target value.
            group_prefix (str): String to prefix group name.
            group_delimiter (str): String to separate group_keys in group name.

        Returns:
            Dictionary where values are lists of entities that all share the same
            'group_keys' values and the key is the common group_key values
            separated by the group_delimiter::

                {"group1_group2":
                    ["object_value", "object_value2"]}
        """
        groups = {}
        for row in dicts:
            cur_groupings = []
            if group_prefix:
                cur_groupings.append(group_prefix)
            for i, group_key in enumerate(group_keys):
                if row[group_key] not in ["", None]:
                    cur_groupings.append(row[group_key])
                if i == len(group_keys)-1:
                    group_name = group_delimiter.join(cur_groupings)
                    if group_name not in groups:
                        groups[group_name] = [{v: row[v] for v in value_keys}]
                    else:
                        groups[group_name] += [{v: row[v] for v in value_keys}]
                else:
                    if row[group_key] not in cur_groupings:
                        cur_groupings.append(row[group_key])
        return groups

    def parse(self, csv_file, group_headers=[]):
        """Create unique groups from additional columns in the csv

        Args:
            csv_file (str): Path to csv file
            group_headers (list, optional): List of headers to group from in order.
                By default all headers in the csv are used in left to right order.

        Returns:
            List of dictionaries::

                {
                 "name": ""
                 "entity_type": ""
                 "members": []
                }

        """
        contents = self._read_csv(csv_file)
        for h in [self.entity_name_header, self.entity_type_header]+group_headers:
            if h not in contents[0].keys():
                raise MissingHeaderError("Header '{}' could not be found".format(h))

        if len(group_headers) == 0:
            group_headers = [h for h in contents[0].keys() if h not in [self.entity_name_header, self.entity_type_header]]
        groups = self._group_values_by_key(contents, group_headers,
                                         [self.entity_name_header, self.entity_type_header],
                                         self.group_prefix, self.group_delimiter)
        # Create Group Dicts
        final_groups = []
        for group, members in groups.items():
            if group == "":
                continue
            entity_types = list(set([m[self.entity_type_header] for m in members]))
            for e_type in entity_types:
                g_members = []
                for m in members:
                    if m[self.entity_type_header] == e_type:
                        g_members.append(m[self.entity_name_header])
                final_groups.append({"name": group,
                                     "entity_type": e_type,
                                     "members": list(set(g_members))})
        return final_groups

class StaticGroup(object):
    """Object that helps create/update/remove a static group in Turbonomic

    Args:
        conn (VMTConnection): VMTConnection instance to target Turbonomic Server.
        name (str): Name of Static Group.
        members (list, optional): List of desired member uuids/names
        entity_type (str): Type of entities in group
            (VirtualMachine, PhysicalMachine, etc).
        uuid (str, optional): UUID of group if already exists. If not provided,
            retrieval will be attempted before operations that require it.

    """
    def __init__(self, conn, name, entity_type, members=[], uuid=None):
        self.name = name
        self.members = members
        self.entity_type = entity_type
        self.uuid = uuid
        self.__conn = conn

    def _requires_uuid(func):
        """Decorator that ensures the group uuid exists before the function
        is executed.

        Raises:
            NoMatchingGroupError: If no group is present with the name
            DuplicateMatchingGroupError: If multiple groups are found matching
                the same name.
        """
        @wraps(func)
        def check_uuid(self,*args,**kwargs):
            self._get_group_uuid()
            return func(self,*args,**kwargs)
        return check_uuid

    def _requires_no_uuid(func):
        """Decorator that ensures the group does not already exist before the
        function is executed.

        Raises:
            GroupAlreadyExistsError: If group already exists with the same name
        """
        @wraps(func)
        def check_uuid(self,*args,**kwargs):
            try:
                group_uuid = self._get_group_uuid()
                raise GroupAlreadyExistsError("Group with name '{}'"
                                              " already exists with uuid"
                                              " {}".format(self.name,
                                                           group_uuid))
            except MissingUUIDError:
                return func(self,*args,**kwargs)
        return check_uuid

    @_requires_uuid
    def remove_entities(self, members, lookup_names=False, case_sensitive=True,
                        dryrun=False):
        """Removes specified members from the current group membership

        Args:
            members (list): List of member uuids/names to add/remove.
            lookup_names (bool, optional): If True uuids will be collected from
                the Turbonomic server that match the entity names in self.members
            case_sensitive (bool, optional): If False and lookup_names is True,
                names will be matched without case sensitivity.

        Returns:
            vmtconnect response object
        """
        entities_to_remove = members
        if lookup_names:
            # Match displayNames to uuids
            entities_to_remove = self._match_names_to_uuid(entities_to_remove,
                                                           case_sensitive=case_sensitive)
        cur_members = [m["uuid"] for m in self.get_current_members()]
        # Remove current group members that are specified in members
        new_members = list(set(cur_members).difference(set(entities_to_remove)))
        if not dryrun:
            self.__conn.update_static_group_members(self.uuid, self.name,
                                                    self.entity_type,
                                                    new_members)

    @_requires_uuid
    def add_entities(self, members, lookup_names=False, case_sensitive=True,
                     dryrun=False):
        """Adds specified members to the current group membership

        Args:
            members (list): List of member uuids/names to add/remove.
            lookup_names (bool, optional): If True uuids will be collected from
                the Turbonomic server that match the entity names in self.members
            case_sensitive (bool, optional): If False and lookup_names is True,
                names will be matched without case sensitivity.

        Returns:
            vmtconnect response object
        """
        entities_to_add = members
        if lookup_names:
            # Match displayNames to uuids
            entities_to_add = self._match_names_to_uuid(entities_to_add,
                                                           case_sensitive=case_sensitive)
        cur_members = [m["uuid"] for m in self.get_current_members()]
        # Add current group member to add new members
        new_members = list(set(cur_members+entities_to_add))
        if not dryrun:
            self.__conn.update_static_group_members(self.uuid, self.name,
                                                    self.entity_type,
                                                    new_members)

    @_requires_uuid
    def update(self, allow_add=True, allow_remove=True, lookup_names=False,
               case_sensitive=True, dryrun=False):
        """Adds/Removes members on the static group on the Turbonomic server.

        Args:
            allow_add (bool, optional): If True, current and new members are
                allowed to be added
            allow_remove (bool, optional): If True, current members are allowed
                to be removed.
            lookup_names (bool, optional): If True uuids will be collected from
                the Turbonomic server that match the entity names in self.members
            case_sensitive (bool, optional): If False and lookup_names is True,
                names will be matched without case sensitivity.
            dryrun (bool, optional): If True, no changes are committed to
                the Turbonomic server

        Returns:
            vmtconnect response object
        """
        entities_to_update = self.members
        if lookup_names:
            # Match displayNames to uuids
            entities_to_update = self._match_names_to_uuid(entities_to_update,
                                                           case_sensitive=case_sensitive)
        new_members = []
        if allow_add is True and allow_remove is True:
            # Completely replace group members
            new_members = entities_to_update
        else:
            cur_members = [m["uuid"] for m in self.get_current_members()]
            if allow_add is True:
                # Add current group member to add new members
                new_members = list(set(cur_members+entities_to_update))
            if allow_remove is True:
                # Remove current group members that are specified in entities_to_update
                new_members = list(set(cur_members).difference(set(entities_to_update)))
        if not dryrun:
            self.__conn.update_static_group_members(self.uuid, new_members,
                                                    name=self.name, type=self.entity_type)
    @_requires_uuid
    def remove(self, dryrun=False):
        """Deletes the group from the Turbonomic server.

        Args:
            dryrun (bool, optional): If True, will not commit changes to
                the Turbonomic server

        Returns:
            vmtconnect response object
        """
        if not dryrun:
            resp = self.__conn.del_group(self.uuid)
            self.uuid = None
            return resp

    @_requires_no_uuid
    def add(self, lookup_names=False, case_sensitive=True, dryrun=False):
        """Adds the group to the Turbonomic server.

        Args:
            lookup_names (bool, optional): If True uuids will be collected from
                the Turbonomic server that match the entity names in self.members
            dryrun (bool, optional): If True, will not commit changes to
                the Turbonomic server

        Returns:
            vmtconnect response object
        """
        entities_to_add = self.members
        if lookup_names:
            # Match displayNames to uuids
            entities_to_add = self._match_names_to_uuid(entities_to_add,
                                                        case_sensitive=case_sensitive)
        if not dryrun:
            return self.__conn.add_static_group(self.name, self.entity_type,
                                                entities_to_add)

    def add_or_update(self, **kwargs):
        """Helper function to update group if it already exists or add it
        if it does not.

        Args:
            dryrun (bool, optional): If True, will not commit changes to
                the Turbonomic server
            **kwargs: Keyword arguments for self.update()

        Returns:
            vmtconnect response object
        """
        try:
            self._get_group_uuid()
            return self.update(**kwargs)
        except MissingUUIDError:
            return self.add(**kwargs)

    @_requires_uuid
    def get_current_members(self):
        """Get list of member entities that currently belong to the group.

        Returns:
            vmtconnect response object
        """
        return self.__conn.get_group_members(self.uuid)

    def exists(self):
        """Checks if group already exists in target environment.

        Returns:
            True if group exists or False if group does not exist
        """
        try:
            self._get_group_uuid()
            return True
        except MissingUUIDError:
            return False

    def _match_names_to_uuid(self, names, case_sensitive):
        """Matches display names to uuids

        Raises:
            NameMatchError: If an entity can't be found by name
            MultipleMatchingNamesError: If multiple entities match a name
        """
        uuids = []
        for name in names:
            matches = self.__conn.search_by_name(name, type=self.entity_type,
                                                 case_sensitive=case_sensitive,
                                                fetch_all=True)
            if len(matches) == 0:
                raise NameMatchError("Unable to find uuid for {}".format(name))
            if len(matches) > 1:
                raise MultipleMatchingNamesError("Multiple {} with the name"
                                                 " {}".format(self.entity_type,
                                                              name))
            uuids.append(matches[0]["uuid"])
        return uuids

    def _get_group_uuid(self):
        """Fetches uuid if not already present and assigns to self.uuid

        Returns:
            str: uuid of group

        Raises:
            NoMatchingGroupError: If no group is present with the name
            DuplicateMatchingGroupError: If multiple groups are found matching
                the same name.
        """
        if self.uuid is None:
            group = self.__conn.get_group_by_name(self.name)
            if group is not None:
                if len(group) == 1:
                    self.uuid = group[0]["uuid"]
                    return self.uuid
                elif len(group) > 1:
                    raise DuplicateMatchingGroupError("Found multiple groups"
                                                      " matching name"
                                                      " {}".format(self.name))
            raise NoMatchingGroupError("No group found matching"
                                       " name '{}'".format(self.name))
        return self.uuid

## ----------------------------------------------------
##   Internal Utility Classes and Functions
## ----------------------------------------------------

# Logging
class _EventTracker(object):
    """Utility Object to store and log events by categories
    """
    def __init__(self, name=None):
        self.name = name
        self.__changes = {}

    def __add_change_object(self, category):
        if category not in self.__changes.keys():
            self.__changes[category] = {"total":0,"events":[]}

    def track(self, category, event=(), msg=True, **kwargs):
        self.__add_change_object(category)
        self.__changes[category]["total"] += 1
        if event:
            # TODO If expanding dictionary, move tuple conversion
            # to static method
            self.__changes[category]["events"].append({"group name":event[0],
                                                       "message": event[1]})
            if msg:
                _msg(event[1], **kwargs)

    def to_dict(self):
        return self.__changes

def _msg(msg, end='\n', logger=None, level=None, exc_info=False, warn=False,
         error=False):
    """Message handler"""
    global LOGGER, QUIET, TRACE, WARN

    empty_trace = (None, None, None)

    if logger is None:
        logger = LOGGER

    if TRACE and sys.exc_info() != empty_trace:
        exc_info = True

    if warn:
        level = "warn"

    if logger:
        if level == 'critical':
            logger.critical(msg, exc_info=exc_info)
        elif level == 'error':
            logger.error(msg, exc_info=exc_info)
        elif level == 'warn' or level == 'warning':
            logger.warning(msg, exc_info=exc_info)
        elif level == 'debug':
            logger.debug(msg, exc_info=exc_info)
        else:
            logger.info(msg, exc_info=exc_info)

    if not QUIET or error:
        if warn and not WARN:
            pass
        else:
            if warn:
                msg = "Warning: {}".format(msg)
            print(msg, end=end)

def _log_summary(change_dict, dryrun, ignore_total=[]):
    summary_bar = "="*15
    title = "    Summary    "
    dryrun_status = ""
    if dryrun:
        dryrun_status = "-dryrun enabled"
    operations = []
    total = 0
    for category, attr in change_dict.items():
        operations.append("{}: {}".format(category, attr["total"]))
        if category not in ignore_total:
            total += attr["total"]
    operations = "\n".join(operations)
    summary_str = "\n".join(["",summary_bar, title, summary_bar, dryrun_status,
                            operations, summary_bar])
    _msg(summary_str, level="info")

# Config Parsing
def _config_to_args(config, args_dict, ignore=[]):
    config_dict = json.load(open(config))
    for i in ignore:
        if i in config_dict.keys():
            config_dict.pop(i)
    args_dict.update(config_dict)
    return args_dict

## ----------------------------------------------------
##   Main Function
## ----------------------------------------------------

def main(conn, csv_file, entity_type_header=ENTITY_TYPE_HEADER,
         entity_name_header=ENTITY_NAME_HEADER, group_headers=[],
         no_add=False, no_remove=False, delete=False, case_sensitive=True,
         group_delimiter=GROUP_DELIMITER, dryrun=False):
    """
        Parses groups from CSV and adds/updates/deletes groups.
        Efficiently collects group and entity uuids to minimize api requests.

    Args:
        conn (VMTConnection): VMTConnection instance to target Turbonomic Server
        csv_file (str): Path to Target CSV
        entity_type_header (str, optional): CSV header for column that contains
            entity types.
        entity_name_header (str, optional): CSV header for column that contains
            entity names.
        group_headers (list, optional): List of CSV headers to group members by
            in order. If empty list, all headers except entity_type_header, and
            entity_name_header are used from left to right.
        no_add (bool, optional): If True, adding current entities to group is
            disabled.
        no_remove (bool, optional): If True, removing current entities from a
            group is disabled
        delete (bool, optional): If True, groups matching names from csv are
            deleted
        case_sensitive (bool, optional): If True, entities will be matched with
            case-sensitivity
        dryrun (bool, optional): If True, changes are not committed to the
            target Turbonomic server.

    Returns:
        Dictionary with change events and totals for each change category

        e.g. ::

            {"Change Category A": {
                 "total": int
                 "events":[
                     {"group name": str,
                      "message": str}
                    ]
                }}

    """
    # Create an _EventTracker instance
    group_changes = _EventTracker()

    # Parse CSV groups and members
    csv_group_parser = CSVGroupParser(entity_type_header, entity_name_header)
    groups = csv_group_parser.parse(csv_file, group_headers=group_headers)

    # Create a GroupUpdateUtility instance
    group_utils = GroupUpdateUtility(conn)

    # Attempt to find group uuids now to minimize api calls
    group_index = group_utils.get_group_index()

    for group in groups:
        uuid = None
        if group["name"] in group_index:
            if len(group_index[group["name"]]) == 1:
                uuid = group_index[group["name"]][0]["uuid"]
        group["uuid"] = uuid

    if delete:
        # Delete groups and return
        for group in groups:
            if not group["uuid"]:
                continue
            group_instance = StaticGroup(conn, group["name"],group["entity_type"],
                                         uuid=group["uuid"])
            try:
                group_instance.remove(dryrun=dryrun)
                event = (group["name"], "Deleted {}".format(group["name"]))
                group_changes.track(TRK_DELETE, event)
            except Exception as e:
                event = (group["name"], "Could not delete group. {}".format(e))
                group_changes.track(TRK_ERROR, event, level='error')
        return group_changes.to_dict()

    # Collect entity uuids and warn if they aren't found
    missing_members = []
    for group in groups:
        discovered_members = []
        for member in group["members"]:
            if member in missing_members:
                continue
            matches = conn.search_by_name(member, type=group["entity_type"],
                                          case_sensitive=case_sensitive,
                                          fetch_all=True)
            if len(matches) == 0:
                event = (group["name"], "Could not find {} {}".format(group["entity_type"],
                                                                      member))
                group_changes.track(TRK_MISS_ENTITY, event, warn=True)
            elif len(matches) > 1:
                msg_str = (group["name"], "More than one instance of"
                           " {} {} found".format(group["entity_type"],
                                                  member))
                group_changes.track(TRK_MISS_ENTITY, msg_str, warn=True)
            else:
                discovered_members.append(matches[0]["uuid"])
        # Overwrite members with uuids
        group["members"] = discovered_members

    # Manage groups
    for group in groups:
        group_instance = StaticGroup(conn, group["name"], group["entity_type"],
                                     group["members"], uuid=group["uuid"])
        try:
            if group["uuid"] is None:
                group_instance.add(dryrun=dryrun)
                event = (group["name"], "Added {} ({} {}s)".format(group["name"],
                                                      len(group["members"]),
                                                      group["entity_type"]))
                group_changes.track(TRK_ADD, event)

            else:
                # Find and log group differences
                diffs = group_utils.get_group_diff(group["uuid"],
                                                   group["members"])
                elligible_changes = []
                change_string = []
                if no_remove is False:
                    elligible_changes += diffs["remove"]
                    change_string += ["{} removed".format(len(diffs["remove"]))]
                if no_add is False:
                    elligible_changes += diffs["add"]
                    change_string += ["{} added".format(len(diffs["add"]))]
                sum_diffs = len(elligible_changes)

                # Only update if needed
                if sum_diffs > 0:
                    group_instance.update(dryrun=dryrun, allow_add=not no_add,
                                          allow_remove=not no_remove)
                    event = (group["name"], "{} Updated ({})".format(group["name"], " ".join(change_string)))
                    group_changes.track(TRK_UPDATE, event, level="info")
                else:
                    event = (group["name"], "{} is already up to date".format(group["name"]))
                    group_changes.track(TRK_SKIP, event, level="info")
        except Exception as e:
            event = (group["name"], "Could not add or update '{}'. {}".format(group["name"],e))
            group_changes.track(TRK_ERROR, event, level="error")

    return group_changes.to_dict()

if __name__ == "__main__":
    # Credentials
    __TURBO_TARGET = "localhost"
    __TURBO_USER = "administrator"
    __TURBO_PASS = ""
    __TURBO_CREDS = b""

    # Parse Arguments
    arg_parser = argparse.ArgumentParser(description="Create/Update/Delete Static Groups From A CSV File")
    arg_parser.add_argument("input_csv", action="store", help="Path to csv file")

    arg_parser.add_argument("-u", "--username", action="store", required=False,
                            help=("Turbonomic Username, Password will be prompted."))

    arg_parser.add_argument("--encoded_creds", action="store", required=False,
                            help=("Base64 encoded credentials"))

    arg_parser.add_argument("-t", "--target", action="store", required=False,
                            help="Turbonomic server address. Default={}".format(__TURBO_TARGET),
                            default=__TURBO_TARGET)

    arg_parser.add_argument("--no_add", action="store_true", required=False,
                            help="Prevents adding entities when updating groups. (Delete Only)")

    arg_parser.add_argument("--no_remove", action="store_true", required=False,
                            help="Prevents removing entities when updating groups. (Add Only)")

    arg_parser.add_argument("--delete", action="store_true", required=False,
                            help="Delete groups")

    arg_parser.add_argument("--case_insensitive", action="store_true", required=False,
                            help="Match entity names without case-sensitivity")

    arg_parser.add_argument("--group_delimiter", action="store", required=False,
                            default=GROUP_DELIMITER,
                            help=("String to separate grouping values. Default='{}'".format(GROUP_DELIMITER)))

    arg_parser.add_argument("--group_headers", nargs='+', action="store",
                            required=False, default=[],
                            help=("CSV Headers to group on. By default all "
                                  " columns except '{}' and '{}' are used"
                                  " in order from"
                                  " left to right".format(ENTITY_TYPE_HEADER,
                                                          ENTITY_NAME_HEADER)
                                  ))

    arg_parser.add_argument("--dryrun", action="store_true", required=False,
                            help="Prevents commits to the Turbonomic server")

    arg_parser.add_argument("--no_warn", action="store_false", required=False,
                            help="Disable warning output to sysout")

    arg_parser.add_argument("-q", "--quiet", action="store_true", required=False,
                            help="Suppress console output")

    arg_parser.add_argument("--log", action="store", required=False,
                            help="Path to log file")

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

    if args_dict["group_delimiter"]:
        GROUP_DELIMITER = args_dict["group_delimiter"]

    # Supress insecure HTTPS warnings
    if args_dict["ignore_insecure_warning"]:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    if args_dict["log"]:
        # Create Logger
        LOGGER = logging.getLogger(__name__)
        LOGGER.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s  %(message)s',
                                          datefmt ='%Y-%m-%d %H:%M:%S')
        log_handler = RotatingFileHandler(args_dict["log"], mode='a', maxBytes=10*1024*1024,
                                          backupCount=1, encoding=None, delay=0)

        log_handler.setFormatter(log_formatter)
        LOGGER.addHandler(log_handler)

    QUIET = args_dict["quiet"]
    WARN =  args_dict["no_warn"]

    try:
        # Make connection object
        conn = vconn.Session(__TURBO_TARGET, __TURBO_USER, __TURBO_PASS,
                             __TURBO_CREDS)
        __TURBO_USER = __TURBO_PASS = __TURBO_ENC = None
        # Execute main function
        change_summary = main(conn, args_dict["input_csv"],
                              group_headers=args_dict["group_headers"],
                              no_add=args_dict["no_add"],
                              no_remove=args_dict["no_remove"],
                              dryrun=args_dict["dryrun"],
                              delete=args_dict["delete"],
                              case_sensitive=not args_dict["case_insensitive"])

        # Log Summary
        _log_summary(change_summary, args_dict["dryrun"], ignore_total=[TRK_MISS_ENTITY])
    except KeyboardInterrupt:
        print("\n")
        pass
    except Exception as e:
        _msg("Fatal Error: {}".format(e), level="error", error=True)
