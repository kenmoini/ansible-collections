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
module: release_address
short_description: Release an IP address in phpIPAM
version_added: "2.11"
description:
    - "Release an IP address in phpIPAM"

options:
  subnet_id:
    description:
      - This is the ID of the subnet you want to release the IP Address from
    required: true
    type: int
    aliases: ['subnet']
  ip_id:
    description:
      - This is the ID of the IP Address you want to release
    required: true
    type: int
    aliases: ['address', 'ip_address']
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
# Release an IP Address
- name: Release an IP Address
  kenmoini.phpipam.release_address:
    phpipam_url: https://phpipam.example.com
    phpipam_app_id: 1234567890
    phpipam_app_code: 1234567890
    subnet_id: 123
    ip_id: 567
  register: r_address
'''

RETURN = '''
ip_address:
    description: Details of the IP Address release request
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
        phpipam_skip_tls_verify=dict(type='bool', required=False, default=False),

        subnet_id=dict(type='int', required=True, aliases=['subnet']),
        ip_id=dict(type='int', required=True, aliases=['address', 'ip_address']),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        ip_address=''
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
    targetURL = module.params['phpipam_url'] + '/api/' + module.params['phpipam_app_id'] + '/addresses/' + str(module.params['ip_id']) + '/' + str(module.params['subnet_id']) + '/'

    response = requests.delete(targetURL, headers=headers, verify=not module.params['phpipam_skip_tls_verify'])
    responseJSON = response.json()

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['ip_address'] = responseJSON
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
