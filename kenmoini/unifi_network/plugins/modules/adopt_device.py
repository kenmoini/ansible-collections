#!/usr/bin/python

# Copyright: (c) 2026, Ken Moini <ken@kenmoini.com>
# MIT License

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: adopt_device
short_description: Adopts a Device into a Site's Unifi Network
version_added: "1.0.0"
description:
    - Adopts a Device into a Site's Unifi Network.

extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site_id

options:
  device_macAddress:
    description:
      - The Device MAC Address to adopt into the Unifi Network.
    required: true
    aliases: ['mac', 'macAddress', 'unifi_network_device_mac', 'unifi_network_device_mac_address']
    type: str
    env:
      - name: UNIFI_NETWORK_DEVICE_MAC_ADDRESS
  ignoreDeviceLimit:
    description:
      - Whether to ignore the device limit when adopting the device.
    required: false
    type: bool
    default: true
    env:
      - name: UNIFI_NETWORK_IGNORE_DEVICE_LIMIT

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Get the List of Pending Devices from the Unifi Network for a Site
- name: Adopt a Device into the Unifi Network
  kenmoini.unifi_network.adopt_device:
    unifi_network_url: https://unifi.example.com
    unifi_network_api_key: 1234567890
    unifi_network_site_id: 88f7af54-1234-5678-9101-abcdefghijklm
    device_macAddress: "00:11:22:33:44:55"
  register: r_adopted_device_info
'''

RETURN = '''
adopted_device_info:
    description: The data returned about the adopted device at the Site managed by this Unifi Network Application
    type: object
    returned: always
'''

import requests, copy
from ansible.module_utils.basic import AnsibleModule
from ..module_utils.check_response_errors import check_response_errors
from ..module_utils.auth import (
    UNIFI_NETWORK_ENDPOINT_ARGS,
)
from ..module_utils.args import (
    SITE_ID_ARG_SPEC,
)

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = copy.deepcopy(UNIFI_NETWORK_ENDPOINT_ARGS)
    module_args.update(copy.deepcopy(SITE_ID_ARG_SPEC))
    module_args.update(
            dict(device_macAddress=dict(type='str', required=True, aliases=['mac', 'macAddress', 'unifi_network_device_mac', 'unifi_network_device_mac_address']),
                  ignoreDeviceLimit=dict(type='bool', required=False, default=True),
        )
    )
    
    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
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
        'X-API-Key': module.params['unifi_network_api_key']
    }
    apiBaseURL = "/proxy/network/integrations"

    targetURL = module.params['unifi_network_url'] + apiBaseURL + '/v1/sites/' + module.params['unifi_network_site_id'] + '/devices'

    # Assemble the payload for the action
    payload = {
        'macAddress': module.params['device_macAddress'],
        'ignoreDeviceLimit': module.params['ignoreDeviceLimit']
    }

    # Perform the API request to get the Adopted Devices Info
    # TODO: Check Mode Enhancement: If this is checkmode, skip the actual POST but query the pending adoption device list to ensure the device exists
    response = requests.post(targetURL, headers=headers, json=payload, verify=not module.params['unifi_network_skip_tls_verify'])
    if response.status_code != 200:
        check_response_errors(module, response, result, context=' while retrieving a specific Device Info')

    result['changed'] = True
    result['adopted_device_info'] = response.json()

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
