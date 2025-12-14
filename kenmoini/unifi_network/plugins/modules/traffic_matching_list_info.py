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
module: traffic_matching_list_info
short_description: Returns the details about a specific Traffic Matching List from Unifi Network
version_added: "1.0.0"
description:
    - Retrieves information about a specific Traffic Matching List in this Unifi Network Application.

extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site_id

options:
  unifi_network_traffic_matching_list_id:
    description:
      - The Traffic Matching List UUID to query for information.
    required: true
    aliases: ['traffic_matching_list_uuid', 'traffic_matching_list_id', 'list', 'list_id', 'list_uuid', 'unifi_network_traffic_matching_list_uuid']
    type: str
    env:
      - name: UNIFI_NETWORK_TRAFFIC_MATCHING_LIST_ID
      - name: UNIFI_NETWORK_TRAFFIC_MATCHING_LIST_UUID

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Get the details of a Traffic Matching List from the Unifi Network
- name: Get Traffic Matching List Info
  kenmoini.unifi_network.traffic_matching_list_info:
    unifi_network_url: https://unifi.example.com
    unifi_network_api_key: 1234567890
    unifi_network_site_id: 88f7af54-1234-5678-9101-abcdefghijklm
    unifi_network_traffic_matching_list_id: 1234abcd-5678-efgh-9101-ijklmnopqrst
  register: r_traffic_matching_list_info
'''

RETURN = '''
traffic_matching_list_info:
    description: The data returned about the Traffic Matching List at the Site managed by this Unifi Network Application
    type: object
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.parameters import env_fallback
from ..module_utils.check_response_errors import check_response_errors
import requests

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        unifi_network_url=dict(type='str', required=True, aliases=['url'], fallback=(env_fallback, ['UNIFI_NETWORK_URL', 'UNIFI_NETWORK_API'])),
        unifi_network_api_key=dict(type='str', required=True, no_log=True, aliases=['api_key'], fallback=(env_fallback, ['UNIFI_NETWORK_API_KEY'])),
        unifi_network_skip_tls_verify=dict(type='bool', required=False, default=False, aliases=['skip_tls_verify'], fallback=(env_fallback, ['UNIFI_NETWORK_SKIP_TLS_VERIFY'])),
        unifi_network_site_id=dict(type='str', required=True, aliases=['site_id', 'site_uuid', 'site', 'unifi_network_site_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_SITE_ID', 'UNIFI_NETWORK_SITE_UUID'])),
        unifi_network_traffic_matching_list_id=dict(type='str', required=True, aliases=['traffic_matching_list_uuid', 'traffic_matching_list_id', 'zone', 'zone_id', 'zone_uuid', 'unifi_network_traffic_matching_list_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_TRAFFIC_MATCHING_LIST_ID', 'UNIFI_NETWORK_TRAFFIC_MATCHING_LIST_UUID'])),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        traffic_matching_list_info={}
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

    targetURL = module.params['unifi_network_url'] + apiBaseURL + '/v1/sites/' + module.params['unifi_network_site_id'] + '/traffic-matching-lists/' + module.params['unifi_network_traffic_matching_list_id']

    # Perform the API request to get the Traffic Matching List Info
    response = requests.get(targetURL, headers=headers, verify=not module.params['unifi_network_skip_tls_verify'])
    if response.status_code != 200:
        check_response_errors(module, response, result, context=' while retrieving specific Traffic Matching List Info')

    result['traffic_matching_list_info'] = response.json()

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
