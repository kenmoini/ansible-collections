#!/usr/bin/python

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: port_action
short_description: Performs an action on a specific Port on a Device from Unifi Network
version_added: "1.0.0"
description:
    - Perform an action on an specific port of a adopted device.

extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site_id
  - kenmoini.unifi_network.device_id
  - kenmoini.unifi_network.port_id

options:
  port_action:
    description:
      - The action to take on the device's port.
    required: true
    type: str
    options:
      - power_cycle
    aliases: ['action']

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Power Cycle a Port on a PoE Device in Unifi Network
- name: Power Cycle port
  kenmoini.unifi_network.port_action:
    unifi_network_url: https://unifi.example.com
    unifi_network_api_key: 1234567890
    unifi_network_site_id: 88f7af54-1234-5678-9101-abcdefghijklm
    unifi_network_device_id: 1234abcd-5678-efgh-9101-ijklmnopqrst
    unifi_network_port_id: 1
    port_action: power_cyle
'''

import requests, copy
from ansible.module_utils.basic import AnsibleModule
from ..module_utils.check_response_errors import check_response_errors
from ..module_utils.auth import (
    UNIFI_NETWORK_ENDPOINT_ARGS,
)
from ..module_utils.args import (
    SITE_ID_ARG_SPEC,
    DEVICE_ID_ARG_SPEC,
    PORT_ID_ARG_SPEC,
)

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = copy.deepcopy(UNIFI_NETWORK_ENDPOINT_ARGS)
    module_args.update(copy.deepcopy(SITE_ID_ARG_SPEC))
    module_args.update(copy.deepcopy(DEVICE_ID_ARG_SPEC))
    module_args.update(copy.deepcopy(PORT_ID_ARG_SPEC))
    module_args.update(
            dict(action=dict(type='str', required=True, choices=['power_cycle'], aliases=['port_action']),
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

    targetURL = module.params['unifi_network_url'] + apiBaseURL + '/v1/sites/' + module.params['unifi_network_site_id'] + '/devices/' + module.params['unifi_network_device_id'] + '/interfaces/ports/' + str(module.params['unifi_network_port_id']) + '/actions'

    # Assemble the payload for the action
    payload = {
        'action': module.params['action'].upper()
    }

    # Perform the API request to get the Adopted Devices Info
    # TODO: Check Mode Enhancement: If this is checkmode, skip the actual POST but query the device list to ensure the device exists
    response = requests.post(targetURL, headers=headers, json=payload, verify=not module.params['unifi_network_skip_tls_verify'])
    if response.status_code != 200:
        check_response_errors(module, response, result, context=' while retrieving a specific Device Info')

    result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
