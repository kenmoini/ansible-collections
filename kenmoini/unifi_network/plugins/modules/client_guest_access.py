#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: client_guest_access
short_description: Authorize or unauthorize guest network access for a UniFi client
version_added: "2.0.0"
description:
  - Grants or revokes Hotspot guest access for a connected guest client, like using a voucher or clicking the
    authorize button in the UniFi UI.
  - The module reads the client first and only acts when its authorization differs from O(state).
    An already authorized client is left alone, even if the limits differ.
options:
  client:
    description:
      - The connected client, given as its MAC address, IPv4 address, name or UUID.
    type: str
    required: true
    aliases: [client_id, mac_address]
  state:
    description:
      - V(authorized) grants guest access, V(unauthorized) revokes it.
    type: str
    choices: [authorized, unauthorized]
    default: authorized
  time_limit_minutes:
    description:
      - How long the guest stays authorized. Defaults to the Hotspot settings. Only with O(state=authorized).
    type: int
  data_usage_limit_mbytes:
    description:
      - Data usage limit in megabytes. Only with O(state=authorized).
    type: int
  rx_rate_limit_kbps:
    description:
      - Download rate limit in kilobits per second. Only with O(state=authorized).
    type: int
  tx_rate_limit_kbps:
    description:
      - Upload rate limit in kilobits per second. Only with O(state=authorized).
    type: int
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
notes:
  - Diff mode is not supported; the result contains the client after the change.
'''

EXAMPLES = r'''
- name: Give a visitor's phone two hours of guest access
  kenmoini.unifi_network.client_guest_access:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    client: "aa:bb:cc:dd:ee:02"
    time_limit_minutes: 120
    data_usage_limit_mbytes: 1024

- name: Revoke guest access
  kenmoini.unifi_network.client_guest_access:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    client: Visitor phone
    state: unauthorized
'''

RETURN = r'''
client:
  description: The client details, re-read from the API after the change (in check mode, before it).
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "name": "Visitor phone", "macAddress": "aa:bb:cc:dd:ee:02",
           "type": "WIRELESS", "access": {"type": "GUEST", "authorized": true}}
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkClient, UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import connection_argument_spec, site_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.convert import pick
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import fail_from_exception, resolve_site

LIMITS = {
    'time_limit_minutes': 'timeLimitMinutes',
    'data_usage_limit_mbytes': 'dataUsageLimitMBytes',
    'rx_rate_limit_kbps': 'rxRateLimitKbps',
    'tx_rate_limit_kbps': 'txRateLimitKbps',
}


def run(module):
    p = module.params
    authorize = p['state'] == 'authorized'
    limits = pick(p, LIMITS)
    if limits and not authorize:
        raise UnifiNetworkError('Option(s) %s only apply when state=authorized' % ', '.join(
            sorted(opt for opt in LIMITS if p[opt] is not None)))
    client = UnifiNetworkClient.from_module(module)
    refs = resolve_site(module, client)
    client_id = refs.resolve('client', p['client'])
    path = '/v1/sites/%s/clients/%s' % (refs.site_id, client_id)
    details = client.get(path)
    access = details.get('access') or {}
    if access.get('type') != 'GUEST':
        raise UnifiNetworkError('Client %r is not a guest client (access type %s); guest access does not apply' % (
            p['client'], access.get('type')))
    changed = bool(access.get('authorized')) != authorize
    if changed and not module.check_mode:
        body = dict(limits, action='AUTHORIZE_GUEST_ACCESS' if authorize else 'UNAUTHORIZE_GUEST_ACCESS')
        client.post(path + '/actions', body)
        details = client.get(path)
    module.exit_json(changed=changed, client=details)


def main():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    spec.update(
        client=dict(type='str', required=True, aliases=['client_id', 'mac_address']),
        state=dict(type='str', default='authorized', choices=['authorized', 'unauthorized']),
        time_limit_minutes=dict(type='int'),
        data_usage_limit_mbytes=dict(type='int'),
        rx_rate_limit_kbps=dict(type='int'),
        tx_rate_limit_kbps=dict(type='int'),
    )
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    try:
        run(module)
    except UnifiNetworkError as exc:
        fail_from_exception(module, exc)


if __name__ == '__main__':
    main()
