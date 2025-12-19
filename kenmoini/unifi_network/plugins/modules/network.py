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
module: network
short_description: Manages the state of a Network in Unifi Network
version_added: "1.0.0"
description:
    - Creates, updates, or deletes a Network managed by this Unifi Network Application.

extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site_id
  - kenmoini.unifi_network.network_id
  - kenmoini.unifi_network.firewall_zone_id

options:
  network_name:
    description:
      - The name of the Network.  If Network ID is defined, it will be used as the identifier to manage the Network.
    required: true
    aliases: ['name', 'unifi_network_network_name']
    type: str
  network_management:
    description:
      - Management mode for the Network.  Options include C'unmanaged' C'gateway' and C'switch'.
    required: false
    aliases: ['management']
    type: str
    choices: ['unmanaged', 'gateway', 'switch']
  network_state:
    description:
      - The desired state of the Network.
    required: true
    aliases: ['state']
    type: str
    choices: ['present', 'absent', 'enabled', 'disabled']
    default: 'present'
  network_vlan_id:
    description:
      - The VLAN ID for the Network.
    required: false
    aliases: ['vlan_id']
    type: int
  network_dhcp_guarding:
    description:
      - Configures DHCP Guarding settings for the Network. Available in all management modes.
    required: false
    aliases: ['dhcp_guarding']
    type: dict
    options:
      enabled:
        description:
          - Whether DHCP Guarding is enabled for the Network.
        type: bool
        default: false
      trusted_servers:
        description:
          - List of trusted DHCP server IP addresses.
        type: list
        elements: str
        default: []
  network_isolated:
    description:
      - Whether the Network is isolated. Available in C'gateway' and C'switch' management modes.
    required: false
    aliases: ['isolated']
    type: bool
    default: false
  network_cellular_backup:
    description:
      - Whether Cellular Backup is enabled for the Network. Available in C'gateway' management mode
    required: false
    aliases: ['cellular_backup']
    type: bool
    default: false
  network_mdns:
    description:
      - Multicast DNS settings for the Network. Available in C'gateway' and C'switch' management modes.
    required: false
    aliases: ['mdns']
    type: bool
    default: false
  network_ipv4:
    description:
      - IPv4 settings for the Network. Available in C'gateway' and C'switch' management modes.
    required: false
    aliases: ['ipv4']
    type: dict
    options:
      enabled:
        description:
          - Whether IPv4 is enabled for the Network.
        type: bool
        default: true
      auto_scale:
        description:
          - Whether to automatically scale the subnet.
        type: bool
        default: false
      host_ip_address:
        description:
          - The IPv4 host IP address on the Network in CIDR notation.
        type: str
      additional_host_ips:
        description:
          - List of additional IPv4 host IP addresses on the Network in CIDR notation.
        type: list
        elements: str
        default: []
      subnet:
        description:
          - The IPv4 subnet in CIDR notation.
        type: str
      gateway:
        description:
          - The IPv4 gateway address.
        type: str
      dhcp_range_start:
        description:
          - The starting IP address of the DHCP range.
        type: str
      dhcp_range_end:
        description:
          - The ending IP address of the DHCP range.
        type: str
author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Create a network in Unifi Network
- name: Create Network
  kenmoini.unifi_network.network:
    unifi_network_url: https://unifi.example.com
    unifi_network_api_key: 1234567890
    unifi_network_site_id: 88f7af54-1234-5678-9101-abcdefghijklm
    unifi_network_network_name: "My New Network"
  register: r_network_info
'''

RETURN = '''
network_info:
    description: The data returned about the Network at the Site managed by this Unifi Network Application
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
    NETWORK_ID_ARG_SPEC,
)

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = copy.deepcopy(UNIFI_NETWORK_ENDPOINT_ARGS)
    module_args.update(copy.deepcopy(SITE_ID_ARG_SPEC))
    module_args.update(copy.deepcopy(NETWORK_ID_ARG_SPEC))
    
    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        network_info={}
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

    targetURL = module.params['unifi_network_url'] + apiBaseURL + '/v1/sites/' + module.params['unifi_network_site_id'] + '/networks/' + module.params['unifi_network_network_id']

    # Perform the API request to get the Network Info
    response = requests.get(targetURL, headers=headers, verify=not module.params['unifi_network_skip_tls_verify'])
    if response.status_code != 200:
        check_response_errors(module, response, result, context=' while retrieving a specific Network Info')

    result['network_info'] = response.json()

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
