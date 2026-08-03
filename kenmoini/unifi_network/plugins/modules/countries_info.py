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
module: countries_info
short_description: Returns the list of Countries from Unifi Network
version_added: "1.0.0"
description:
    - Returns ISO-standard country codes and names, used for region-based configuration or regulatory compliance.

extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.query_limit
  - kenmoini.unifi_network.query_offset

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Get the List of Countries running on the Unifi Network for a Site
- name: Get Countries from Unifi Network
  kenmoini.unifi_network.countries_info:
    unifi_network_url: https://unifi.example.com
    unifi_network_api_key: 1234567890
  register: r_countries_info
'''

RETURN = '''
countries_info:
    description: The data returned about the list of Countries from this Unifi Network Application
    type: object
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.query_limit import UNIFI_NETWORK_QUERY_LIMIT
from ..module_utils.query_offset import UNIFI_NETWORK_QUERY_OFFSET
from ..module_utils.check_response_errors import check_response_errors
import requests, copy
from ..module_utils.auth import (
    UNIFI_NETWORK_ENDPOINT_ARGS,
)

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = copy.deepcopy(UNIFI_NETWORK_ENDPOINT_ARGS)
    module_args.update(copy.deepcopy(UNIFI_NETWORK_QUERY_LIMIT))
    module_args.update(copy.deepcopy(UNIFI_NETWORK_QUERY_OFFSET))

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        countries_info={}
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

    targetURL = module.params['unifi_network_url'] + apiBaseURL + '/v1/countries?' + query_params_str

    # Perform the API request to get the Countries
    response = requests.get(targetURL, headers=headers, verify=not module.params['unifi_network_skip_tls_verify'])
    if response.status_code != 200:
        check_response_errors(module, response, result, context=' while retrieving Countries Info')

    result['countries_info'] = response.json()

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
