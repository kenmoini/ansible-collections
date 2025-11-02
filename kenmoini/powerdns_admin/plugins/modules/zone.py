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
module: zone
short_description: Manage Zones in PowerDNS Admin
version_added: "2.11"
description:
    - "This module allows you to manage Zones in PowerDNS Admin"

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
    default: localhost
    aliases: ['server_id']
    type: str
  zone_name:
    description:
      - The name of the Zone to manage
    required: true
    aliases: ['name', 'zone']
    type: str
  zone_type:
    description:
      - The type of the Zone to manage
    required: false
    default: Native
    choices: ['Native', 'Master', 'Slave']
    type: str
  soa_edit_api:
    description:
      - The SOA Edit API setting for the Zone
    required: false
    default: DEFAULT
    choices: ['DEFAULT', 'INCREASE', 'EPOCH', 'OFF']
  account:
    description:
      - The Account to assign the Zone to
    required: false
    type: str
  state:
    description:
      - Whether the zone should exist or not
    required: false
    default: present
    choices: ['present', 'absent']
    type: str


author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Create a Zone
- name: Create a Zone in PowerDNS Admin
  kenmoini.powerdns_admin.zone:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
    zone_name: example.com.
    zone_type: Master
    account: someaccount
  register: r_zone

# Delete a Zone
- name: Delete a Zone in PowerDNS Admin
  kenmoini.powerdns_admin.zone:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
    zone_name: example.com.
    state: absent
'''

RETURN = '''
zone:
    description: Details about the Zone
    returned: when state is 'present'
    type: object
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
        zone_name=dict(type='str', required=True, aliases=['name', 'zone']),
        zone_type=dict(type='str', choices=['Native', 'Master', 'Slave'], default='Native'),
        soa_edit_api=dict(type='str', choices=['DEFAULT', 'INCREASE', 'EPOCH', 'OFF'], default='DEFAULT'),
        account=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present')
    )
    result = dict(
        changed=False,
        zone={}
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

    targetURL = module.params['pdns_admin_url'] + '/api/v1/servers/' + module.params['pdns_server_id'] + '/zones'

    # Check to see if the zone exists
    apiResponse = requests.get(targetURL + '/' + module.params['zone_name'], headers=headers, verify=module.params['pdns_admin_skip_tls_verify'])
    zone_exists = apiResponse.status_code == 200
    if zone_exists:
      # Delete the Zone if state is absent
      if module.params['state'] == 'absent':
          targetURL += '/' + module.params['zone_name']
          apiResponse = requests.delete(targetURL, headers=headers, verify=module.params['pdns_admin_skip_tls_verify'])
          if apiResponse.status_code == 204:
              result['changed'] = True
          else:
              module.fail_json(msg='Failed to delete zone: {}'.format(apiResponse.text), **result)
          module.exit_json(**result)

      # The zone exists, compare and update if necessary
      if module.params['state'] == 'present':
          existing_zone = apiResponse.json()
          needs_update = False
          zone_payload = {}

          if existing_zone.get('kind') != module.params['zone_type']:
              needs_update = True
              zone_payload['kind'] = module.params['zone_type']
          if existing_zone.get('soa_edit_api') != module.params['soa_edit_api']:
              needs_update = True
              zone_payload['soa_edit_api'] = module.params['soa_edit_api']
          if module.params['account'] and existing_zone.get('account') != module.params['account']:
              needs_update = True
              zone_payload['account'] = module.params['account']

          if needs_update:
              apiResponse = requests.put(targetURL + '/' + module.params['zone_name'], headers=headers, json=zone_payload, verify=module.params['pdns_admin_skip_tls_verify'])

              if apiResponse.status_code == 204:
                  result['changed'] = True
                  result['zone'] = existing_zone
              else:
                  module.fail_json(msg='Failed to update zone: {}'.format(apiResponse.text), **result)
          else:
              result['zone'] = existing_zone

          module.exit_json(**result)

    else:
        # The zone does not exist, exit if state is absent
        if module.params['state'] == 'absent':
            result['changed'] = False
            module.exit_json(**result)

        # The zone does not exist, create it if state is present
        if module.params['state'] == 'present':

            # Create the Zone payload
            zone_payload = {
                "name": module.params['zone_name'],
                "type": "Zone",
                "kind": module.params['zone_type'],
                "soa_edit_api": module.params['soa_edit_api']
            }
            if module.params['account']:
                zone_payload['account'] = module.params['account']

            apiResponse = requests.post(targetURL, headers=headers, json=zone_payload, verify=module.params['pdns_admin_skip_tls_verify'])

            if apiResponse.status_code == 201:
                result['changed'] = True
                result['zone'] = apiResponse.json()
            else:
                module.fail_json(msg='Failed to manage zone: {}'.format(apiResponse.text), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
