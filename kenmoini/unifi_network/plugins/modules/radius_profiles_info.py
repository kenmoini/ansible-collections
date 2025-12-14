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
module: radius_profiles_info
short_description: Returns the list of RADIUS Profiles from Unifi Network
version_added: "1.0.0"
description:
    - Retrieves information about the list of RADIUS Profiles managed by this Unifi Network Application.

extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site_id

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Get the List of RADIUS Profiles from the Unifi Network for a Site
- name: Get RADIUS Profiles at a Site from Unifi Network
  kenmoini.unifi_network.radius_profiles_info:
    unifi_network_url: https://unifi.example.com
    unifi_network_api_key: 1234567890
    unifi_network_site_id: 88f7af54-1234-5678-9101-abcdefghijklm
  register: r_radius_profiles_info
'''

RETURN = '''
radius_profiles_info:
    description: The data returned about the list of RADIUS Profiles at the Site managed by this Unifi Network Application
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

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        radius_profiles_info={}
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

    targetURL = module.params['unifi_network_url'] + apiBaseURL + '/v1/sites/' + module.params['unifi_network_site_id'] + '/radius/profiles'

    # Perform the API request to get the RADIUS Profiles Info
    response = requests.get(targetURL, headers=headers, verify=not module.params['unifi_network_skip_tls_verify'])
    if response.status_code != 200:
        check_response_errors(module, response, result, context=' while retrieving RADIUS Profiles Info')

    result['radius_profiles_info'] = response.json()

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
