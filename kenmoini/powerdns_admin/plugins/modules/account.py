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
module: account
short_description: Manage Accounts in PowerDNS Admin
version_added: "2.11"
description:
    - "This module allows you to manage accounts in PowerDNS Admin"

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
  state:
    description:
      - Whether the account should exist or not
    required: false
    default: present
    choices: ['present', 'absent']
    type: str
  name:
    description:
      - The name of the account - alphanumeric characters only
    required: true
    type: str
  description:
    description:
      - The description of the account
    required: false
    type: str
  contact:
    description:
      - The contact name of the account
    required: false
    type: str
  mail:
    description:
      - The email address of the account
    required: false
    aliases: ['email']
    type: str

author:
    - Ken Moini (@kenmoini)
'''

EXAMPLES = '''
# Create an Account
- name: Create an Account in PowerDNS Admin
  kenmoini.powerdns_admin.account:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_username: ansible
    pdns_admin_password: password
    state: present
    name: testaccount
    description: This is a test account
  register: r_account

# Delete an Account
- name: Delete an Account in PowerDNS Admin
  kenmoini.powerdns_admin.account:
    pdns_admin_url: https://phpipam.example.com
    pdns_admin_username: ansible
    pdns_admin_password: password
    state: absent
    name: testaccount
'''

RETURN = '''
account:
    description: The data returned about the Account
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
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        name=dict(type='str', required=True),
        description=dict(type='str', required=False),
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
        account={}
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
    listResponse = requests.get(targetURL, headers=headers, verify=not module.params['pdns_admin_skip_tls_verify'])

    # Loop through the accounts
    accountFound = False
    for account in listResponse.json():
        if account['name'] == module.params['name']:
            accountFound = True
            if module.params['state'] == 'absent':
                # Delete the account
                deleteResponse = requests.delete(targetURL + '/' + str(account['id']), headers=headers, verify=not module.params['pdns_admin_skip_tls_verify'])
                if deleteResponse.status_code == 204:
                  result['account'] = account
                  result['changed'] = True
            else:
                # Update the account
                dataChanged = False
                payload = {
                    'name': module.params['name']
                }
                if module.params['description'] and account['description'] != module.params['description']:
                    payload['description'] = module.params['description']
                    dataChanged = True
                if module.params['contact'] and account['contact'] != module.params['contact']:
                    payload['contact'] = module.params['contact']
                    dataChanged = True
                if module.params['mail'] and account['mail'] != module.params['mail']:
                    payload['mail'] = module.params['mail']
                    dataChanged = True

                updateResponse = requests.put(targetURL + '/' + str(account['id']), headers=headers, data=json.dumps(payload), verify=not module.params['pdns_admin_skip_tls_verify'])

                if updateResponse.status_code == 204:
                    newAccount = account
                    # Update the newAccount with all the passed parameters
                    if module.params['description']:
                        newAccount['description'] = module.params['description']
                    if module.params['contact']:
                        newAccount['contact'] = module.params['contact']
                    if module.params['mail']:
                        newAccount['mail'] = module.params['mail']

                    result['account'] = newAccount
                    result['changed'] = dataChanged

    if module.params['state'] == 'present' and accountFound == False:
        # Create a new account
        payload = {
            'name': module.params['name']
        }
        if module.params['description']:
            payload['description'] = module.params['description']
        if module.params['contact']:
            payload['contact'] = module.params['contact']
        if module.params['mail']:
            payload['mail'] = module.params['mail']

        response = requests.post(targetURL, headers=headers, data=json.dumps(payload), verify=not module.params['pdns_admin_skip_tls_verify'])
        result['account'] = response.json()
        result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
