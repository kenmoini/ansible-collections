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
module: account_info
short_description: Returns Accounts in PowerDNS Admin
version_added: "2.11"
description:
    - "This module allows you to list and find accounts in PowerDNS Admin"

options:
  pdns_admin_url:
    description:
      - This is the URL of your PowerDNS Admin instance
    required: true
    aliases: ['url']
    type: str
  pdns_admin_username:
    description:
        - This is the username for your PowerDNS Admin instance
    required: true
    aliases: ['username']
    type: str
  pdns_admin_password:
    description:
        - This is the password for your PowerDNS Admin instance
    required: true
    aliases: ['password']
    type: str
  pdns_admin_skip_tls_verify:
    description:
      - Whether or not to skip TLS verification
    required: false
    default: false
    aliases: ['skip_tls_verify']
    type: bool
  name:
    description:
      - The name of the account to find - alphanumeric characters only
    required: false
    type: str
  contact:
    description:
      - The contact name of the account(s) to find
    required: false
    type: str
  mail:
    description:
      - The email address of the account(s) to find
    required: false
    aliases: ['email']
    type: str

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# List all Accounts
- name: Get all the Accounts from PowerDNS Admin
  kenmoini.powerdns_admin.account_info:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_username: ansible
    pdns_admin_password: password
  register: r_accounts

# Find a specific Account by name
- name: Find a specific Account by name in PowerDNS Admin
  kenmoini.powerdns_admin.account:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_username: ansible
    pdns_admin_password: password
    name: testaccount
  register: r_account
'''

RETURN = '''
accounts:
    description: The data returned about the Account(s)
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
        pdns_admin_username=dict(type='str', required=True, aliases=['username']),
        pdns_admin_password=dict(type='str', required=True, aliases=['password'], no_log=True),
        pdns_admin_skip_tls_verify=dict(type='bool', required=False, default=False, aliases=['skip_tls_verify']),
        name=dict(type='str', required=False),
        contact=dict(type='str', required=False),
        mail=dict(type='str', required=False, aliases=['email']),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        accounts={}
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # Encode the username and password in base64
    userpass = module.params['pdns_admin_username'] + ':' + module.params['pdns_admin_password']
    userpass_bytes = userpass.encode('ascii')
    base64_bytes = base64.b64encode(userpass_bytes)

    # Create the headers for the API request
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + base64_bytes.decode('ascii'),
    }

    targetURL = module.params['pdns_admin_url'] + '/api/v1/pdnsadmin/accounts'

    # Get the current list of accounts
    listResponse = requests.get(targetURL, headers=headers, verify=module.params['pdns_admin_skip_tls_verify'])

    discoveredAccounts = []

    if module.params['name'] or module.params['contact'] or module.params['mail']:
        # Loop through the accounts
        for account in listResponse.json():
            if module.params['name'] and account['name'] == module.params['name']:
                discoveredAccounts.append(account)
            if module.params['contact'] and account['contact'] == module.params['contact']:
                discoveredAccounts.append(account)
            if module.params['mail'] and account['mail'] == module.params['mail']:
                discoveredAccounts.append(account)
    else:
        discoveredAccounts = listResponse.json()

    result['accounts'] = discoveredAccounts

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
