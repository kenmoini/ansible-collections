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
module: zone_info
short_description: Returns Zones in PowerDNS Admin
version_added: "2.11"
description:
    - "This module allows you to list and find Zones in PowerDNS Admin"

options:
  pdns_admin_url:
    description:
      - This is the URL of your PowerDNS Admin instance
    required: true
    aliases: ['url']
  pdns_admin_api_key:
    description:
      - This is the API Key for your PowerDNS Admin instance
    required: true
    aliases: ['api_key']
  pdns_admin_skip_tls_verify:
    description:
      - Whether or not to skip TLS verification
    required: false
    default: false
    aliases: ['skip_tls_verify']
    type: bool
  server:
    description:
      - The Server to find the Zone in
    required: false
    default: localhost
    aliases: ['server_id']
  id:
    description:
      - The Zone to find by ID
    required: false
    aliases: ['zone_id']
  name:
    description:
      - The Zone to find by Name
    required: false
    aliases: ['zone_name']
  account:
    description:
      - The Zones to find by Account
    required: false

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# List all Zones
- name: Get all the Zones from PowerDNS Admin
  kenmoini.powerdns_admin.zone_info:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
  register: r_zones

# Find a specific Zone
- name: Find a Zone in PowerDNS Admin
  kenmoini.powerdns_admin.zone_info:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
    id: test.example.com.
  register: r_zone
'''

RETURN = '''
zones:
    description: The data returned about the Zone(s)
    type: object
    returned: always
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
        pdns_admin_skip_tls_verify=dict(type='bool', required=False, default=False, aliases=['skip_tls_verify']),
        server=dict(type='str', required=False, default='localhost', aliases=['server_id']),
        id=dict(type='str', required=False, aliases=['zone_id']),
        name=dict(type='str', required=False, aliases=['zone_name']),
        account=dict(type='str', required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        zones={}
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # Create the headers for the API request
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': module.params['pdns_admin_api_key']
    }

    targetURL = module.params['pdns_admin_url'] + '/api/v1/servers/' + module.params['server'] + '/zones'

    # Get the current list of Zones
    listResponse = requests.get(targetURL, headers=headers, verify=module.params['pdns_admin_skip_tls_verify'])

    discoveredZones = []

    if module.params['id'] or module.params['name'] or module.params['account']:
        # Loop through the Zones
        for zone in listResponse.json():
            if module.params['id'] and zone['id'] == module.params['id']:
                discoveredZones.append(zone)
            elif module.params['name'] and zone['name'] == module.params['name']:
                discoveredZones.append(zone)
            elif module.params['account'] and zone['account'] == module.params['account']:
                discoveredZones.append(zone)
    else:
        discoveredZones = listResponse.json()

    result['zones'] = discoveredZones

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
