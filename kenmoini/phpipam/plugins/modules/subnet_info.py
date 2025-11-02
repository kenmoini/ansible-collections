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
module: subnet_info
short_description: Get Subnet Info from phpIPAM
version_added: "2.11"
description:
    - "Find information about a subnet in phpIPAM"

options:
  cidr:
    description:
      - This is the CIDR of the subnet you want to get information about
    required: true
    aliases: ['subnet']
    type: str
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

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Get the information about a specific subnet
- name: Retrieve information about a specific subnet
  kenmoini.phpipam.subnet_info:
    cidr: 192.168.42.0/23
    phpipam_url: https://phpipam.example.com
    phpipam_app_id: 1234567890
    phpipam_app_code: 1234567890
  register: subnet_info
'''

RETURN = '''
subnet_info:
    description: The data returned about the subnet
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
        cidr=dict(type='str', required=True, aliases=['subnet']),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        subnet_info={}
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

    targetURL = module.params['phpipam_url'] + '/api/' + module.params['phpipam_app_id'] + '/subnets/cidr/' + module.params['cidr']

    response = requests.get(targetURL, headers=headers, verify=not module.params['phpipam_skip_tls_verify'])

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['subnet_info'] = response.json().get('data')
    result['changed'] = False

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
