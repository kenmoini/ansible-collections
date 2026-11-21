#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: acl_rule_ordering
short_description: Set the priority order of user-defined ACL rules in UniFi Network
version_added: "2.0.0"
description:
  - Reorders the user-defined ACL rules at a site. Rules earlier in the order take priority.
  - The rules in O(rules) are placed in the given order, at the top (or bottom) of the order.
    Rules that are not listed keep their relative order.
  - The module reads the current order first and only writes when it differs.
  - Use M(kenmoini.unifi_network.acl_rule_ordering_info) to read the order.
options:
  rules:
    description:
      - ACL rules in the desired order, given as names or UUIDs.
    type: list
    elements: str
    required: true
  position:
    description:
      - Where the listed rules go relative to the rules that are not listed.
    type: str
    choices: [top, bottom]
    default: top
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Make sure the allow rule is evaluated before the block rule
  kenmoini.unifi_network.acl_rule_ordering:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    rules:
      - Allow admin to NAS
      - Block IoT to NAS

- name: Push a catch-all rule to the end
  kenmoini.unifi_network.acl_rule_ordering:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    rules: [Block everything else]
    position: bottom
'''

RETURN = r'''
ordering:
  description: The ACL rule order after the change, or the predicted order in check mode.
  returned: always
  type: dict
  sample: {"orderedAclRuleIds": ["497f6eca-6276-4993-bfeb-53cbbbba6f08", "7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11"]}
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkClient, UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import connection_argument_spec, site_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import fail_from_exception, resolve_site


def reorder(current, listed, position):
    """Place ``listed`` in order at the top or bottom; the rest keep their relative order."""
    rest = [item for item in current if item not in listed]
    return listed + rest if position == 'top' else rest + listed


def run(module):
    client = UnifiNetworkClient.from_module(module)
    refs = resolve_site(module, client)
    path = '/v1/sites/%s/acl-rules/ordering' % refs.site_id
    current = client.get(path) or {}
    current_ids = list(current.get('orderedAclRuleIds') or [])
    listed = []
    for rule in module.params['rules']:
        rule_id = refs.resolve('acl_rule', rule)
        if rule_id not in current_ids:
            raise UnifiNetworkError('ACL rule %r is not a user-defined rule in the ordering and cannot be reordered' % rule)
        if rule_id not in listed:
            listed.append(rule_id)
    desired = {'orderedAclRuleIds': reorder(current_ids, listed, module.params['position'])}
    changed = desired['orderedAclRuleIds'] != current_ids
    result = desired
    if changed and not module.check_mode:
        result = client.put(path, desired) or desired
    output = {'changed': changed, 'ordering': result}
    if module._diff:
        output['diff'] = {'before': {'orderedAclRuleIds': current_ids}, 'after': desired}
    module.exit_json(**output)


def main():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    spec.update(
        rules=dict(type='list', elements='str', required=True),
        position=dict(type='str', default='top', choices=['top', 'bottom']),
    )
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    try:
        run(module)
    except UnifiNetworkError as exc:
        fail_from_exception(module, exc)


if __name__ == '__main__':
    main()
