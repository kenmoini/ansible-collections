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
module: record
short_description: Manage Records in PowerDNS Admin
version_added: "2.11"
description:
    - "This module allows you to manage Records in PowerDNS Admin"

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
    aliases: ['zone_id']
    type: str
  record_name:
    description:
      - The name of the Record to manage
    required: true
    aliases: ['name', 'record']
    type: str
  record_type:
    description:
      - The type of the Record to manage
    required: true
    aliases: ['type']
    type: str
  record_value:
    description:
      - The value of the Record to manage
    required: true
    aliases: ['value']
    type: str
  record_ttl:
    description:
      - The TTL of the Record to manage
    required: false
    aliases: ['ttl']
    default: 3600
    type: int
  state:
    description:
      - Whether the record should exist or not
    required: false
    default: present
    choices: ['present', 'absent', 'disabled']
    type: str

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Create a Record in a Zone
- name: Create a Record in a Zone in PowerDNS Admin
  kenmoini.powerdns_admin.record:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
    zone: example.com.
    record_name: www
    record_type: A
    value: 192.0.2.1
    ttl: 3600
    state: present

# Delete a Record in a Zone
- name: Delete a Record in a Zone in PowerDNS Admin
  kenmoini.powerdns_admin.record:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
    zone: example.com.
    record_name: www
    record_type: A
    state: absent
'''

RETURN = '''
record:
    description: Details about the Record
    returned: always
    type: dict
    sample: {"id": 1, "name": "www", "type": "A", "content": "192.0.2.1", "ttl": 3600}
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
        record_name=dict(type='str', required=True, aliases=['name', 'record']),
        record_type=dict(type='str', required=True, aliases=['type']),
        record_value=dict(type='str', required=True, aliases=['value']),
        record_ttl=dict(type='int', required=False, default=3600, aliases=['ttl']),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent', 'disabled']),
    )

    result = dict(
        changed=False,
        record={},
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # Create the headers for the API request
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': module.params['pdns_admin_api_key']
    }

    targetURL = module.params['pdns_admin_url'] + '/api/v1/servers/' + str(module.params['pdns_server_id']) + '/zones/' + module.params['zone']

    # Create the payload for the API request
    payload = {
        "rrsets": [
            {
                "name": module.params['record_name'],
                "type": module.params['record_type'],
                "changetype": "REPLACE" if module.params['state'] in ['present', 'disabled'] else "DELETE",
                "ttl": module.params['record_ttl'],
                "records": [
                    {
                        "content": module.params['record_value'],
                        "disabled": module.params['state'] == 'disabled'
                    }
                ] if module.params['state'] in ['present', 'disabled'] else []
            }
        ]
    }

    # Get the current list of records
    listResponse = requests.patch(targetURL, headers=headers, json=payload, verify=not module.params['pdns_admin_skip_tls_verify'])

    if listResponse.status_code in [200, 201, 204]:
        # Fetch the updated record details
        getResponse = requests.get(targetURL, headers=headers, verify=not module.params['pdns_admin_skip_tls_verify'])
        for record in getResponse.json().get('rrsets', []):
            if record['name'].rstrip('.') == module.params['record_name'].rstrip('.') and record['type'] == module.params['record_type']:
                result['record'] = record
                break
        result['changed'] = True 

    else:
        module.fail_json(msg='Failed to manage record: ' + listResponse.text, **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

