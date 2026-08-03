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
module: wifi_broadcasts_info
short_description: Returns the list of Wifi Broadcasts (SSIDs) from Unifi Network
version_added: "1.0.0"
description:
    - Retrieves information about the list of Wifi Broadcasts or SSIDs on WAPs managed by this Unifi Network Application.

extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.query_limit
  - kenmoini.unifi_network.query_offset
  - kenmoini.unifi_network.site_id
  - kenmoini.unifi_network.filters

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Get the List of Wifi Broadcasts from the Unifi Network for a Site
- name: Get Wifi Broadcasts at a Site from Unifi Network
  kenmoini.unifi_network.wifi_broadcasts_info:
    unifi_network_url: https://unifi.example.com
    unifi_network_api_key: 1234567890
    unifi_network_site_id: 88f7af54-1234-5678-9101-abcdefghijklm
  register: r_wifi_broadcasts_info
'''

RETURN = '''
wifi_broadcasts_info:
    description: The data returned about the list of Wifi Broadcasts at the Site managed by this Unifi Network Application
    type: object
    returned: always
'''

import requests, copy
from ansible.module_utils.basic import AnsibleModule
from ..module_utils.query_limit import UNIFI_NETWORK_QUERY_LIMIT
from ..module_utils.query_offset import UNIFI_NETWORK_QUERY_OFFSET
from ..module_utils.check_response_errors import check_response_errors
from ..module_utils.filter_requests import filter_requests
from ..module_utils.auth import UNIFI_NETWORK_ENDPOINT_ARGS
from ..module_utils.args import (
    SITE_ID_ARG_SPEC,
    FILTERS_ARG_SPEC,
)

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = copy.deepcopy(UNIFI_NETWORK_ENDPOINT_ARGS)
    module_args.update(copy.deepcopy(UNIFI_NETWORK_QUERY_LIMIT))
    module_args.update(copy.deepcopy(UNIFI_NETWORK_QUERY_OFFSET))
    module_args.update(copy.deepcopy(SITE_ID_ARG_SPEC))
    module_args.update(copy.deepcopy(FILTERS_ARG_SPEC))

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        wifi_broadcasts_info={}
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

    query_params = {
        "limit": str(module.params['query_limit']),
        "offset": str(module.params['query_offset'])
    }

    query_params_str = '&'.join([f"{key}={value}" for key, value in query_params.items()])

    targetURL = module.params['unifi_network_url'] + apiBaseURL + '/v1/sites/' + module.params['unifi_network_site_id'] + '/wifi/broadcasts?' + query_params_str

    # Apply any filters to the request URL
    targetURL = filter_requests(module, targetURL, result)

    # Perform the API request to get the Wifi Broadcasts Info
    response = requests.get(targetURL, headers=headers, verify=not module.params['unifi_network_skip_tls_verify'])
    if response.status_code != 200:
        check_response_errors(module, response, result, context=' while retrieving Wifi Broadcasts Info')
    result['wifi_broadcasts_info'] = response.json()

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
