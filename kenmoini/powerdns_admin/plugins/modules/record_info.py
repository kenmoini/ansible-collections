#!/usr/bin/python

# Copyright: (c) 2024, Ken Moini <ken@kenmoini.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}
DOCUMENTATION = '''
---
module: record_info
short_description: Returns the Records from PowerDNS Admin
version_added: "2.11"
description:
    - "This module allows you to list and find Records in PowerDNS Admin"

options:
  pdns_admin_url:
    description:
      - This is the URL of your PowerDNS Admin instance
    required: true
    aliases: ['url']
    type: str
  pdns_admin_api_key:
    description:
      - This is the API Key for your PowerDNS Admin instance
    required: true
    aliases: ['api_key']
    type: str
  pdns_admin_skip_tls_verify:
    description:
      - Whether or not to skip TLS verification
    required: false
    default: false
    aliases: ['skip_tls_verify']
    type: bool
  pdns_server_id:
    description:
      - The PowerDNS Server ID to use
    required: false
    default: 1
    aliases: ['server_id']
    type: int
  zone:
    description:
      - The Zone to find Records in
    required: true
    type: str
  record:
    description:
      - The Record to find
    required: false
    type: str
  record_type:
    description:
      - The Record Type to find
    required: false
    type: str

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# List all Records in a Zone
- name: Get all the Records from a Zone in PowerDNS Admin
  kenmoini.powerdns_admin.record_info:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
    zone: example.com.
  register: r_records

# Find a specific Record in a Zone
- name: Find a Record in a Zone in PowerDNS Admin
  kenmoini.powerdns_admin.record_info:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
    zone: example.com.
    record: www
    record_type: A
  register: r_record
'''

RETURN = '''
records:
    description: List of Records
    returned: always
    type: list
    sample: [{"id": 1, "name": "www", "type": "A", "content": "192.0.2.1", "ttl": 3600, "status": "Active"}]
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json
import base64


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pdns_admin_url=dict(type='str', required=True, aliases=['url']),
        pdns_admin_api_key=dict(type='str', required=True, no_log=True, aliases=['api_key']),
        pdns_admin_skip_tls_verify=dict(type='bool', default=False, aliases=['skip_tls_verify']),
        pdns_server_id=dict(type='str', default="localhost", aliases=['server_id']),
        zone=dict(type='str', required=True, aliases=['zone_id']),
        record=dict(type='str', required=False),
        record_type=dict(type='str', required=False)
    )
    result = dict(
        changed=False,
        records=[]
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Create the headers for the API request
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': module.params['pdns_admin_api_key']
    }

    targetURL = module.params['pdns_admin_url'] + '/api/v1/servers/' + str(module.params['pdns_server_id']) + '/zones/' + module.params['zone']

    # Get the current list of records
    listResponse = requests.get(targetURL, headers=headers, verify=module.params['pdns_admin_skip_tls_verify'])

    discoveredRecords = []
    if module.params['record'] or module.params['record_type']:
        # Loop through the records and filter them out
        for record in listResponse.json().get('rrsets', []):
            if module.params['record'] and module.params['record_type']:
                if record['name'].rstrip('.') == module.params['record'].rstrip('.') and record['type'] == module.params['record_type']:
                    discoveredRecords.append(record)
            elif module.params['record']:
                if record['name'].rstrip('.') == module.params['record'].rstrip('.'):
                    discoveredRecords.append(record)
            elif module.params['record_type']:
                if record['type'] == module.params['record_type']:
                    discoveredRecords.append(record)

    else:
        discoveredRecords = listResponse.json().get('rrsets', [])

    result['records'] = discoveredRecords

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
