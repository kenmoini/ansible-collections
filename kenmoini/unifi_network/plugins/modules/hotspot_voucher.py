#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: hotspot_voucher
short_description: Generate and revoke Hotspot vouchers in UniFi Network
version_added: "2.0.0"
description:
  - Makes sure a number of non-expired guest Hotspot vouchers exist, or deletes vouchers.
  - "With O(state=present) the module counts the non-expired vouchers named O(name) whose limits match the options you set,
    and only generates the shortfall up to O(count). Running it again does not create more vouchers."
  - With O(state=absent) the module deletes the voucher O(id), or every voucher named O(name) (optionally only expired ones).
options:
  name:
    description:
      - The voucher note, shared by every voucher in the batch. Used to count and find vouchers.
      - Required unless O(id) is set.
    type: str
  id:
    description:
      - UUID of a single voucher to delete. Only with O(state=absent).
    type: str
  state:
    description:
      - V(present) generates vouchers until O(count) matching ones exist, V(absent) deletes vouchers.
    type: str
    choices: [present, absent]
    default: present
  count:
    description:
      - How many matching, non-expired vouchers should exist (1 to 1000).
    type: int
    default: 1
  time_limit_minutes:
    description:
      - How long a voucher grants access after the first guest uses it. Required with O(state=present).
    type: int
  authorized_guest_limit:
    description:
      - How many different guests may use the same voucher.
    type: int
  data_usage_limit_mbytes:
    description:
      - Data usage limit in megabytes.
    type: int
  rx_rate_limit_kbps:
    description:
      - Download rate limit in kilobits per second.
    type: int
  tx_rate_limit_kbps:
    description:
      - Upload rate limit in kilobits per second.
    type: int
  only_expired:
    description:
      - With O(state=absent), only delete vouchers that have expired.
    type: bool
    default: false
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
notes:
  - Diff mode is not supported for vouchers; the result lists the matching vouchers and how many were created or deleted.
'''

EXAMPLES = r'''
- name: Make sure 20 one-day vouchers exist for the conference
  kenmoini.unifi_network.hotspot_voucher:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Conference 2025
    count: 20
    time_limit_minutes: 1440
    data_usage_limit_mbytes: 2048
    rx_rate_limit_kbps: 20000
    tx_rate_limit_kbps: 5000
  register: r_vouchers

- name: Print the voucher codes
  ansible.builtin.debug:
    msg: "{{ r_vouchers.hotspot_vouchers | map(attribute='code') | list }}"

- name: Clean up expired conference vouchers
  kenmoini.unifi_network.hotspot_voucher:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Conference 2025
    state: absent
    only_expired: true

- name: Revoke every conference voucher
  kenmoini.unifi_network.hotspot_voucher:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Conference 2025
    state: absent
'''

RETURN = r'''
hotspot_vouchers:
  description:
    - With O(state=present), the matching non-expired vouchers, including any just generated (in check mode only the existing ones).
    - With O(state=absent), the vouchers that were (or would be) deleted.
  returned: always
  type: list
  elements: dict
  sample: [{"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "name": "Conference 2025", "code": "4861409510", "expired": false,
            "timeLimitMinutes": 1440, "authorizedGuestCount": 0, "createdAt": "2025-01-01T00:00:00Z"}]
created_count:
  description: How many vouchers were (or in check mode would be) generated.
  returned: when O(state=present)
  type: int
  sample: 18
deleted_count:
  description: How many vouchers were (or in check mode would be) deleted.
  returned: when O(state=absent)
  type: int
  sample: 2
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkClient, UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import connection_argument_spec, site_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.convert import pick
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.filters import (
    FilterError,
    build_filter,
    render_condition,
    server_filterable,
)
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import fail_from_exception, resolve_site

LIMITS = {
    'time_limit_minutes': 'timeLimitMinutes',
    'authorized_guest_limit': 'authorizedGuestLimit',
    'data_usage_limit_mbytes': 'dataUsageLimitMBytes',
    'rx_rate_limit_kbps': 'rxRateLimitKbps',
    'tx_rate_limit_kbps': 'txRateLimitKbps',
}


def name_condition(name):
    """The name for a server-side filter, or None when it must be matched client-side only."""
    return name if server_filterable(name) else None


def ensure_present(module, client, path):
    p = module.params
    if p['time_limit_minutes'] is None:
        raise UnifiNetworkError('time_limit_minutes is required to generate vouchers')
    limits = pick(p, LIMITS)
    filter_expr = build_filter(name=name_condition(p['name']), filters=[{'property': 'expired', 'function': 'eq', 'value': False}])
    existing = client.paginate(path, filter_expr=filter_expr)
    matching = [v for v in existing if v.get('name') == p['name'] and not v.get('expired')
                and all(v.get(key) == value for key, value in limits.items())]
    shortfall = max(p['count'] - len(matching), 0)
    if shortfall and not module.check_mode:
        body = dict(limits, name=p['name'], count=shortfall)
        created = (client.post(path, body) or {}).get('vouchers') or []
        matching.extend(created)
    module.exit_json(changed=shortfall > 0, hotspot_vouchers=matching, created_count=shortfall)


def ensure_absent(module, client, path):
    p = module.params
    if p['id']:
        voucher = client.get_or_none('%s/%s' % (path, p['id']))
        if voucher and not module.check_mode:
            client.delete('%s/%s' % (path, p['id']))
        vouchers = [voucher] if voucher else []
        module.exit_json(changed=bool(voucher), hotspot_vouchers=vouchers, deleted_count=len(vouchers))
    filters = [{'property': 'expired', 'function': 'eq', 'value': True}] if p['only_expired'] else None
    filter_expr = build_filter(name=name_condition(p['name']), filters=filters)
    doomed = [v for v in client.paginate(path, filter_expr=filter_expr)
              if v.get('name') == p['name'] and (v.get('expired') or not p['only_expired'])]
    if doomed and not module.check_mode:
        # Delete exactly the vouchers matched above, by id, so nothing beyond the reported list is removed.
        ids = sorted(v['id'] for v in doomed)
        client.delete(path, query={'filter': render_condition({'property': 'id', 'function': 'in', 'value': ids})})
    module.exit_json(changed=bool(doomed), hotspot_vouchers=doomed, deleted_count=len(doomed))


def main():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    spec.update(
        name=dict(type='str'),
        id=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        count=dict(type='int', default=1),
        time_limit_minutes=dict(type='int'),
        authorized_guest_limit=dict(type='int'),
        data_usage_limit_mbytes=dict(type='int'),
        rx_rate_limit_kbps=dict(type='int'),
        tx_rate_limit_kbps=dict(type='int'),
        only_expired=dict(type='bool', default=False),
    )
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True, required_one_of=[('name', 'id')],
                           mutually_exclusive=[('name', 'id')],
                           required_if=[('state', 'present', ('name',))])
    try:
        client = UnifiNetworkClient.from_module(module)
        path = '/v1/sites/%s/hotspot/vouchers' % resolve_site(module, client).site_id
        if module.params['state'] == 'present':
            ensure_present(module, client, path)
        else:
            ensure_absent(module, client, path)
    except (UnifiNetworkError, FilterError) as exc:
        fail_from_exception(module, exc)


if __name__ == '__main__':
    main()
