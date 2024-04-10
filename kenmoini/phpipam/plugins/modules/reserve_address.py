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
module: reserve_address
short_description: Update an IP address in phpIPAM
version_added: "2.11"
description:
    - "Update an IP address in phpIPAM"

options:
  phpipam_url:
    description:
      - This is the URL of your phpIPAM instance
    required: true
    type: str
  phpipam_app_id:
    description:
      - This is the app ID for your phpIPAM instance
    required: true
    type: str
  phpipam_app_code:
    description:
      - This is the app code for your phpIPAM instance
    required: true
    type: str
  phpipam_skip_tls_verify:
    description:
      - Whether or not to skip TLS verification
    required: false
    default: false
    type: bool
    aliases: ['skip_tls_verify']
  subnet_id:
    description:
      - This is the ID of the subnet you want to get the first free IP Address from
    required: true
    type: int
    aliases: ['subnet']
  ip:
    description:
      - This is the IP Address you want to reserve
    required: true
    type: str
    aliases: ['address', 'ip_address']
  hostname:
    description:
      - This is the hostname you want to assign to the IP Address
    required: false
    type: str
  description:
    description:
      - This is the description you want to assign to the IP Address
    required: false
    type: str
  tag:
    description:
      - This is the tag you want to assign to the IP Address
    required: false
    choices: ['offline', 'used', 'reserved', 'dhcp']
    default: 'reserved'
    type: str
  is_gateway:
    description:
      - Whether or not the IP Address is a gateway
    required: false
    type: bool
  ping_exclude:
    description:
      - Whether or not to exclude the IP Address from pings
    required: false
    type: bool
  ptr_exclude:
    description:
      - Whether or not to exclude the IP Address from PTR records
    required: false
    type: bool
  owner:
    description:
      - The owner of the IP Address
    required: false
    type: str
  note:
    description:
      - A note about the IP Address
    required: false
    type: str

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Reserve an IP Address
- name: Reserve an IP Address
  kenmoini.phpipam.reserve_address:
    phpipam_url: https://phpipam.example.com
    phpipam_app_id: 1234567890
    phpipam_app_code: 1234567890
    subnet_id: 123
    ip: 1.2.3.4
    hostname: "test-hostname.example.com"
    description: "Test Description"
    tag: "reserved"
  register: r_address
'''

RETURN = '''
ip_address:
    description: Details of the IP Address reservation request
    type: object
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        phpipam_url=dict(type='str', required=True),
        phpipam_app_id=dict(type='str', required=True),
        phpipam_app_code=dict(type='str', required=True, no_log=True),
        phpipam_skip_tls_verify=dict(type='bool', required=False, default=False, aliases=['skip_tls_verify']),

        subnet_id=dict(type='int', required=True, aliases=['subnet']),
        ip=dict(type='str', required=True, aliases=['address', 'ip_address']),

        hostname=dict(type='str', required=False),
        description=dict(type='str', required=False),

        tag=dict(type='str', required=False, choices=['offline', 'used', 'reserved', 'dhcp'], default='reserved'),
        is_gateway=dict(type='bool', required=False),
        ping_exclude=dict(type='bool', required=False),
        ptr_exclude=dict(type='bool', required=False),

        owner=dict(type='str', required=False),
        note=dict(type='str', required=False),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        ip_address_id=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    headers = {
        'Content-Type': 'application/json',
        'token': module.params['phpipam_app_code']
    }

    # make the API call
    targetURL = module.params['phpipam_url'] + '/api/' + module.params['phpipam_app_id'] + '/addresses/'

    # Set the required parameters
    payload = {
        'ip': module.params['ip'],
        'subnetId': int(module.params['subnet_id']),
    }

    # Append any set optional parameters
    if module.params['hostname']:
        payload['hostname'] = module.params['hostname']
    if module.params['description']:
        payload['description'] = module.params['description']
    if module.params['tag']:
        if module.params['tag'] == 'offline':
            payload['tag'] = 1
        elif module.params['tag'] == 'used':
            payload['tag'] = 2
        elif module.params['tag'] == 'reserved':
            payload['tag'] = 3
        elif module.params['tag'] == 'dhcp':
            payload['tag'] = 4
    if module.params['is_gateway']:
        payload['is_gateway'] = module.params['is_gateway']
    if module.params['ping_exclude']:
        payload['ping_exclude'] = module.params['ping_exclude']
    if module.params['ptr_exclude']:
        payload['ptr_exclude'] = module.params['ptr_exclude']

    response = requests.post(targetURL, headers=headers, json=payload, verify=module.params['phpipam_skip_tls_verify'])
    responseJSON = response.json()

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    #result['ip_address_id'] = response.json().get('id')
    result['ip_address_id'] = responseJSON
    result['changed'] = False

    #if response.json().get('success') == True and response.json().code == 201:
    #    result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
