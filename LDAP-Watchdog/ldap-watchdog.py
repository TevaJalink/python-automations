import json
import os
import sys
from datetime import datetime
import time
from ldap3 import Server, Connection, ALL, SUBTREE, NTLM
from ldap3.core.exceptions import LDAPSocketOpenError
import requests

CONTROL_objectGUIDS = ''
CONTROL_USER_ATTRIBUTE = ''

LDAP_SERVER = 'ldap://crb.local:389'
LDAP_USERNAME = os.environ['User_Name']
LDAP_PASSWORD = os.environ['User_Password']
LDAP_USE_SSL = False
BASE_DN = 'DC=crb,DC=local'

DISABLE_COLOR_OUTPUT = False
SEARCH_FILTER = '(|(objectClass=computer)(objectClass=user)(objectClass=group)(objectClass=groupPolicyContainer))'
SEARCH_ATTRIBUTE = ['*','+']

REFRESH_RATE = 3600

SLACK_BULLETPOINT = ' \u2022   '

IGNORED_objectGUIDS = []
IGNORED_ATTRIBUTES = ['logonCount','lastLogon','lastLogonTimestamp','uSNChanged','whenChanged','pwdLastSet','badPasswordTime']
CONDITIONAL_IGNORED_ATTRIBUTES = {}

SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL')



if SLACK_WEBHOOK and len(SLACK_WEBHOOK) > 0:
    import requests

def col(op_type):
    """
    Returns ANSI color codes for different LDAP operation types.

    Parameters:
    - op_type (str): LDAP operation type ('add', 'delete', 'modify').

    Returns:
    - str: ANSI color code.
    """
    if DISABLE_COLOR_OUTPUT:
        return ''
    return {'add': "\033[1m\033[32m", 'delete': "\033[3m\033[31m", 'modify': "\033[33m"}[op_type]


def retrieve_ldap():
    """
    Connects to the LDAP server and retrieves LDAP entries.

    Returns:
    - dict: Dictionary containing LDAP entries.
    """
    entries = {}
    server = Server(LDAP_SERVER, use_ssl=LDAP_USE_SSL, get_info=ALL)
    if LDAP_USERNAME and LDAP_PASSWORD:
        conn = Connection(server, user=LDAP_USERNAME, password=LDAP_PASSWORD, authentication=NTLM, auto_bind=True)
        if not conn.bind():
            print('Error in bind:', conn.result, file=sys.stderr)
            return entries
    else:
        conn = Connection(server)
        if not conn.bind():
            print('Anonymous bind failed:', conn.result, file=sys.stderr)
            return entries

    conn.extend.standard.paged_search(search_base=BASE_DN, search_filter=SEARCH_FILTER, search_scope=SUBTREE, attributes=SEARCH_ATTRIBUTE, paged_size=1000, generator=False)
    
    for entry in conn.entries:
        entry = json.loads(entry.entry_to_json())
        entry_dict = entry['attributes']
#        for attr_name, attr_value in entry.items():
#            print(attr_name)
#            print(attr_value)
#            attr_value = attr_value[0]
            # Some entries may be encoded using base64 and provided by a dictionary.
            # In that case, replace the dictionary with a string of the encoded data.
#            if isinstance(attr_value, dict) and len(attr_value) == 2 and 'encoded' in attr_value and 'encoding' in attr_value and attr_value['encoding'] == 'base64':
#                print("Here")
#                decoded_value = attr_value['encoded']
#                entry[attr_name] = decoded_value

#        entry_dict = entry['attributes']
        entry_dict['dn'] = [entry['dn']]
        entries[entry_dict['objectGUID'][0]] = entry_dict

    return entries

def generate_message(dn_objectGUID, op_type, changes, sAMAccountName):
    """
    Generates formatted messages for Slack and console output based on LDAP changes.

    Parameters:
    - dn_objectGUID (str): LDAP entry's objectGUID.
    - op_type (str): LDAP operation type ('add', 'delete', 'modify').
    - changes (dict): Dictionary containing LDAP attribute changes.

    Returns:
    - tuple: (str, str) Tuple containing Slack and console-formatted messages.
    """
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    rst_col = "\033[0m"
    stt_col = "\033[1m\033[35m"
    if DISABLE_COLOR_OUTPUT:
        rst_col = ""
        stt_col = ""

    bl = f"{SLACK_BULLETPOINT}{op_type}"

    print_msg = f"[{stt_col}{timestamp}{rst_col}] {op_type}{col(op_type)} {dn_objectGUID}{rst_col}\n"
    json_data = {}
    json_data['@timestamp'] = f"{timestamp}"
    json_data['sAMAccountName'] = f"{sAMAccountName}"
    json_data['ObjectGUID'] = f"{dn_objectGUID}"
    json_data[f'{op_type}'] = ""

    if op_type == 'modify':
        for additions in changes['additions']:
            for key, vals in additions.items():
                for val in vals:
                    print_msg += f"{SLACK_BULLETPOINT}add '{col('modify')}{key}{rst_col}' to '{col('add')}{val}{rst_col}'\n"
                    json_data['modify'] += f"added new attribute '{key}' value is '{val}', " 
        for removals in changes['removals']:
            for key, vals in removals.items():
                for val in vals:
                    print_msg += f"{SLACK_BULLETPOINT}delete '{col('modify')}{key}{rst_col}' was '{col('delete')}{val}{rst_col}'\n"
                    json_data['modify'] += f"deleted attribute '{key}' value was '{val}', "
        for modifications in changes['modifications']:
            for key, val in modifications.items():
                print_msg += f"{SLACK_BULLETPOINT}modify '{col('modify')}{key}{rst_col}' to '{col('add')}{val[1]}{rst_col}' was '{col('delete')}{val[0]}{rst_col}'\n"
                json_data['modify'] += f"modified attribute '{key}' value to '{val[1]}' was '{val[0]}', "
    elif op_type == 'delete':
        for key, vals in changes.items():
            for val in vals:
                print_msg += f"{bl} '{col('modify')}{key}{rst_col}' was '{col('delete')}{val}{rst_col}'\n"
                json_data['delete'] += f"'{key}' was '{val}', "
    elif op_type == 'add':
        for key, vals in changes.items():
            for val in vals:
                print_msg += f"{bl} '{col('modify')}{key}{rst_col}' to '{col('add')}{val}{rst_col}'\n"
                json_data['add'] += f"'{key}' to '{val}', "

    return print_msg, json_data


def announce(dn_objectGUID, op_type, changes):
    """
    Sends notification messages to Slack and prints to the console.

    Parameters:
    - dn_objectGUID (str): LDAP entry's objectGUID.
    - op_type (str): LDAP operation type ('add', 'delete', 'modify').
    - changes (dict): Dictionary containing LDAP attribute changes.

    Returns:
    - None
    """
    url = "https://de33d2fc72a0475086a80a9b1710e2c1.us-east-1.aws.found.io/logs-changes-production/_doc/"

    print_msg, json_message = generate_message(dn_objectGUID, op_type, changes)
 #   send_to_slack(slack_msg)
    print(print_msg)
    requests.post(url, data=json.dumps(json_message), headers={'Authorization': f"ApiKey {os.environ['APIKey']}", 'Content-Type': 'application/json'})

def compare_ldap_entries(old_entries, new_entries):
    """
    Compares old and new LDAP entries and announces modifications.

    Parameters:
    - old_entries (dict): Dictionary containing old LDAP entries.
    - new_entries (dict): Dictionary containing new LDAP entries.

    Returns:
    - None
    """

    # XXX: The next four lines of code do not consider ignored objectGUIDs or ignored attributes.
    for objectGUID in old_entries.keys() - new_entries.keys():
        # Any entries that are in old_entries but not new_entries are deletions.
        announce(f"{old_entries[objectGUID]['dn'][0]} ({old_entries[objectGUID]['objectGUID'][0]})", "delete", old_entries[objectGUID], old_entries[objectGUID]['sAMAccountName'][0])

    for objectGUID in new_entries.keys() - old_entries.keys():
        # Any entries that are in new_entries but not old_entries are additions.
        announce(f"{new_entries[objectGUID]['dn'][0]} ({new_entries[objectGUID]['objectGUID'][0]})", "add", new_entries[objectGUID], new_entries[objectGUID]['sAMAccountName'][0])

    for objectGUID in old_entries.keys() & new_entries.keys():
        if objectGUID in IGNORED_objectGUIDS:
            continue  # TODO: print that it was skipped?
        if old_entries[objectGUID] != new_entries[objectGUID]:
            # For changes of a user, there are three types of operations to define: additions, removals, and modifications.
            changes = {}
            # XXX: Could these be dictionaries instead?
            changes.setdefault("additions", []) # A list of addition of values to attributes.
            changes.setdefault("modifications", []) # A list of changes of a single value for an attribute.
            changes.setdefault("removals", []) # A list of removal of values from an atttribute.
            for key in old_entries[objectGUID].keys() | new_entries[objectGUID].keys():
                # Compare each key (attribute) in the old and new entries
                old_value = old_entries[objectGUID].get(key)
                new_value = new_entries[objectGUID].get(key)
                # If they are not the same, we have some type of change.
                if old_value != new_value:
                    if old_value is None:
                        # If the key is not found in old_entries, it's an addition.
                        changes["additions"].append({key: new_value})
                    elif new_value is None:
                        # If the key is not found in new_entries, it's a removal.
                        changes["removals"].append({key: old_value})
                    else:
                        # If the key is in both old_entries and new_entries but the values are not the same, then may be a modification.
                        # There is no way to truly determine whether an attribute's value(s) have been changed, or removed and then a new value added.
                        # Therefore, we define a modification as the change of an attribute that has only a single value.
                        if len(old_value) == len(new_value) == 1:
                            changes["modifications"].append({key: (old_value[0], new_value[0])})
                        else:
                            # If there is either zero or more than one value for an attribute, then the difference beteen the old values and the new values indicate an addition or removal (or a value; not an entry).
                            # That is to say: this is the addition or removal of values for an attribute which does not have exactly one old value and exactly one new value.
                            # Therefore, if a new value (or values) is present for an attribute, it is also an addition.
                            added = set(new_value) - set(old_value)
                            # And if the value (or values) is only in the old data, it is a removal.
                            removed = set(old_value) - set(new_value)
                            if added:
                                changes["additions"].append({key: added})
                            if removed:
                                changes["removals"].append({key: removed})

            # It is worth remembering what "changes" really is.
            #
            # changes["modifications"] is a set of dictionaries. Each dictionary's key is an attribute name, and the value is a tuple of (old_ldap_value, new_ldap_value).
            # changes["modifications"] =
            # [
            #   { attr_name: (old_val, new_val) },
            #   { attr_name2: (old_val2, new_val2) },
            # ]
            #
            # changes["additions"] and changes["removals"] are each a set of dictionaries. Each dictionary's key is an attribute name, and the value is a set of the values for which we wish to ignore.
            # changes["additions"] =
            # [
            #  { attr_name: [val1, val2] },
            #  { attr_name2: [val1, val2] },
            # ]

            for change_type in ["additions", "modifications", "removals"]:
                for ignored_attr_name in IGNORED_ATTRIBUTES:
                    for change in changes[change_type][:]:  # Using a shallow copy of each dictionary.
                        # For each change type, check whether any of the changed attribute names should be ignored.
                        if ignored_attr_name in change:
                           # print(f"Ignoring {old_entries[objectGUID]['dn'][0]} ({old_entries[objectGUID]['objectGUID'][0]}) {change}", file=sys.stderr)
                            changes[change_type].remove(change)

            for change_type in ["additions", "modifications", "removals"]:
                for ignored_attr_name, ignored_attr_list in CONDITIONAL_IGNORED_ATTRIBUTES.items():
                    for change in changes[change_type][:]: # 'change' is each dictionary in changes[change_type].
                        if ignored_attr_name in change: # Check if the ignored attribute is in the dictionary
                            if change_type == "modifications": # For modifications, we ignore the change if either the new or old value of the ignored attribute is the ignored value.
                                old_attr_value = change[ignored_attr_name][0] # old value
                                new_attr_value = change[ignored_attr_name][1] # new value
                                if old_attr_value in ignored_attr_list or new_attr_value in ignored_attr_list:
                                    #print(f"Ignoring {change_type} of {old_entries[objectGUID]['dn'][0]} ({old_entries[objectGUID]['objectGUID'][0]}) {ignored_attr_name}: from {old_attr_value} to {new_attr_value}", file=sys.stderr)
                                    changes[change_type].remove(change) # Remove the whole dictionary from changes["modifications"].
                            else:
                                for added_or_removed_val in change[ignored_attr_name][:]: # val1, val2, ...
                                    if added_or_removed_val in ignored_attr_list: # Check whether the value should be ignored.
                                        #print(f"Ignoring {change_type} of {old_entries[objectGUID]['dn'][0]} ({old_entries[objectGUID]['objectGUID'][0]}) {ignored_attr_name}: {added_or_removed_val}", file=sys.stderr)
                                        change[ignored_attr_name].remove(added_or_removed_val) # Remove the ignored value from the set of added/removed attributes for attribute ignored_attr_name.
                                        if len(change[ignored_attr_name]) == 0: # If the added/removed attribute set for ignored_attr_name is in now empty ( {attr_name: []} ) then delete it.
                                            changes[change_type].remove(change)

            for change_type in ["additions", "modifications", "removals"]:
                if len(changes[change_type]) > 0:
                    announce(f"{old_entries[objectGUID]['dn'][0]} ({old_entries[objectGUID]['objectGUID'][0]})", "modify", changes, old_entries[objectGUID]['sAMAccountName'][0])
                    break

if __name__ == '__main__':
    new_entries = retrieve_ldap()
    while True:
        time.sleep(REFRESH_RATE)

        try:
            retrieved_entries = retrieve_ldap()
        except LDAPSocketOpenError as e:
            print(f"LDAP connection error: {e}", file=sys.stderr)
            continue

        old_entries = new_entries
        new_entries = retrieved_entries
        compare_ldap_entries(old_entries, new_entries)

