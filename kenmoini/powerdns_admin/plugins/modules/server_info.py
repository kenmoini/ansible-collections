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
module: server_info
short_description: Returns the Servers from PowerDNS Admin
version_added: "2.11"
description:
    - "This module allows you to list and find Servers in PowerDNS Admin"

options:
  pdns_admin_url:
    description:
      - This is the URL of your PowerDNS Admin instance
    required: true
    aliases: ['url']
    type: str
  pdns_admin_api_key:
    description:
      - This is the API Key for your PowerDNS Admin instance
    required: true
    aliases: ['api_key']
    type: str
  pdns_admin_skip_tls_verify:
    description:
      - Whether or not to skip TLS verification
    required: false
    default: false
    aliases: ['skip_tls_verify']
    type: bool
  server:
    description:
      - The Server to find, eg localhost, or empty for all Servers
    required: false
    aliases: ['server_id']
    type: str

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# List all Servers
- name: Get all the Servers from PowerDNS Admin
  kenmoini.powerdns_admin.server_info:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
  register: r_servers

# Find a specific Server
- name: Find a Server in PowerDNS Admin
  kenmoini.powerdns_admin.account:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_api_key: 1234567890
    server: localhost
  register: r_server
'''

RETURN = '''
servers:
    description: The data returned about the Server(s)
    type: object
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json
import base64

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pdns_admin_url=dict(type='str', required=True, aliases=['url']),
        pdns_admin_api_key=dict(type='str', required=True, no_log=True, aliases=['api_key']),
        pdns_admin_skip_tls_verify=dict(type='bool', required=False, default=False, aliases=['skip_tls_verify']),
        server=dict(type='str', required=False, aliases=['server_id']),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        servers={}
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
        'X-API-Key': module.params['pdns_admin_api_key']
    }

    targetURL = module.params['pdns_admin_url'] + '/api/v1/servers'

    # Get the current list of accounts
    listResponse = requests.get(targetURL, headers=headers, verify=not module.params['pdns_admin_skip_tls_verify'])

    discoveredServers = []

    if module.params['server']:
        # Loop through the servers
        for server in listResponse.json():
            if module.params['server'] and server['id'] == module.params['server']:
                discoveredServers.append(server)
    else:
        discoveredServers = listResponse.json()

    result['servers'] = discoveredServers

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
