#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: firewall_policy_ordering
short_description: Set the order of user-defined firewall policies between two zones in UniFi Network
version_added: "2.0.0"
description:
  - Sets the evaluation order of the user-defined firewall policies for one source/destination firewall zone pair.
    Each zone pair has two ordered lists, the policies evaluated before the system-defined policies and those evaluated after them.
  - The policies you list are placed in the given order. User-defined policies you do not list keep their relative order
    and stay in their current list, after (O(position=top)) or before (O(position=bottom)) the listed ones.
    A policy listed in one list is moved out of the other.
  - The module only writes when the resulting order differs from the current one.
  - Use M(kenmoini.unifi_network.firewall_policy_ordering_info) to read the order and
    M(kenmoini.unifi_network.firewall_policy) to manage the policies themselves.
options:
  source_zone:
    description:
      - Source firewall zone of the policies, given as its name or UUID.
    required: true
    type: str
    aliases: [source_firewall_zone_id]
  destination_zone:
    description:
      - Destination firewall zone of the policies, given as its name or UUID.
    required: true
    type: str
    aliases: [destination_firewall_zone_id]
  before_system_defined:
    description:
      - Policies to evaluate before the system-defined policies, in order, given as names or UUIDs.
      - Each must be a user-defined policy from O(source_zone) to O(destination_zone). A name only needs to be unique
        among those policies.
      - Omit to leave this list alone, apart from removing the policies listed in O(after_system_defined).
    type: list
    elements: str
  after_system_defined:
    description:
      - Policies to evaluate after the system-defined policies, in order, given as names or UUIDs.
      - Each must be a user-defined policy from O(source_zone) to O(destination_zone). A name only needs to be unique
        among those policies.
      - Omit to leave this list alone, apart from removing the policies listed in O(before_system_defined).
    type: list
    elements: str
  position:
    description:
      - Where the listed policies go within their list, relative to the user-defined policies you did not list.
      - V(top) puts them first, so they are evaluated before the unlisted ones. V(bottom) puts them last.
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
- name: Evaluate the blocklist first, then allow web traffic, before the system-defined policies
  kenmoini.unifi_network.firewall_policy_ordering:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    source_zone: Internal
    destination_zone: External
    before_system_defined:
      - Block bad actors
      - IoT to web

- name: Move a catch-all policy to the very end, after the system-defined policies
  kenmoini.unifi_network.firewall_policy_ordering:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    source_zone: Internal
    destination_zone: External
    after_system_defined:
      - Log everything else
    position: bottom

- name: Set both lists exactly, using UUIDs
  kenmoini.unifi_network.firewall_policy_ordering:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    source_zone: 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
    destination_zone: 1b0e3d7c-9a52-4f6e-8c41-6d2f0a9b8e77
    before_system_defined:
      - 497f6eca-6276-4993-bfeb-53cbbbba6f08
    after_system_defined:
      - 3c2e8f10-4b6a-4c1e-9d2a-0f5b7e9a1c33

- name: Preview a reorder without making it (run with --check --diff)
  kenmoini.unifi_network.firewall_policy_ordering:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    source_zone: Internal
    destination_zone: External
    before_system_defined: [IoT to web]
  check_mode: true
  diff: true
'''

RETURN = r'''
ordering:
  description:
    - The firewall policy ordering of the zone pair after the change, as returned by the API, or the predicted ordering in check mode.
  returned: always
  type: dict
  sample: {"orderedFirewallPolicyIds": {"beforeSystemDefined": ["497f6eca-6276-4993-bfeb-53cbbbba6f08",
                                                                "6a0d2c4e-1f3b-4a5c-8e7d-9b0a1c2d3e4f"],
                                        "afterSystemDefined": ["3c2e8f10-4b6a-4c1e-9d2a-0f5b7e9a1c33"]}}
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkClient, UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import (
    connection_argument_spec,
    site_argument_spec,
)
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.filters import FilterError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.references import is_uuid
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import fail_from_exception, resolve_site

LISTS = (('before_system_defined', 'beforeSystemDefined'), ('after_system_defined', 'afterSystemDefined'))


def _ordering(before, after):
    return {'orderedFirewallPolicyIds': {'beforeSystemDefined': list(before), 'afterSystemDefined': list(after)}}


class FirewallPolicyOrdering(object):

    def __init__(self, module, client=None):
        self.module = module
        self.params = module.params
        self.client = client or UnifiNetworkClient.from_module(module)
        self.refs = resolve_site(module, self.client)
        self.given = {}
        self.path = '/v1/sites/%s/firewall/policies/ordering' % self.refs.site_id
        self.query = {
            'sourceFirewallZoneId': self.refs.resolve('firewall_zone', self.params['source_zone']),
            'destinationFirewallZoneId': self.refs.resolve('firewall_zone', self.params['destination_zone']),
        }

    def zone_pair(self):
        return 'from zone %r to zone %r' % (self.params['source_zone'], self.params['destination_zone'])

    def resolve_policy(self, value, ordered):
        """Return the UUID of a policy ordered in this zone pair; names only need to be unique within the pair."""
        if is_uuid(value):
            if value not in ordered:
                raise UnifiNetworkError('Firewall policy %s is not a user-defined policy %s, so it cannot be ordered here'
                                        % (value, self.zone_pair()))
            return value
        matches = self.refs.lookup('firewall_policy', value)
        if not matches:
            raise UnifiNetworkError('No firewall policy named %r was found in the site' % value)
        in_pair = [m['id'] for m in matches if m['id'] in ordered]
        if not in_pair:
            raise UnifiNetworkError('Firewall policy %r is not a user-defined policy %s, so it cannot be ordered here'
                                    % (value, self.zone_pair()))
        if len(in_pair) > 1:
            raise UnifiNetworkError('Multiple firewall policies %s are named %r (ids: %s); use the UUID instead'
                                    % (self.zone_pair(), value, ', '.join(in_pair)))
        return in_pair[0]

    def resolve_list(self, option, ordered):
        values = self.params[option]
        if values is None:
            return None
        ids = []
        for value in values:
            policy_id = self.resolve_policy(value, ordered)
            if policy_id in ids:
                raise UnifiNetworkError('Firewall policy %r is listed more than once in %s' % (value, option))
            ids.append(policy_id)
            self.given[policy_id] = value
        return ids

    def arrange(self, current, listed, listed_elsewhere):
        """Return the new content of one list."""
        moved_out = set(listed_elsewhere or ())
        if listed is None:
            return [i for i in current if i not in moved_out]
        rest = [i for i in current if i not in listed and i not in moved_out]
        return listed + rest if self.params['position'] == 'top' else rest + listed

    def run(self):
        current = self.client.get(self.path, query=self.query) or {}
        ids = current.get('orderedFirewallPolicyIds') or {}
        current_lists = dict((key, list(ids.get(key) or [])) for _option, key in LISTS)
        ordered = set(current_lists['beforeSystemDefined']) | set(current_lists['afterSystemDefined'])

        before = self.resolve_list('before_system_defined', ordered)
        after = self.resolve_list('after_system_defined', ordered)
        both = [i for i in (before or []) if i in (after or [])]
        if both:
            raise UnifiNetworkError('Firewall policy %s cannot be in both before_system_defined and after_system_defined'
                                    % ', '.join(repr(self.given[i]) for i in both))

        new_before = self.arrange(current_lists['beforeSystemDefined'], before, after)
        new_after = self.arrange(current_lists['afterSystemDefined'], after, before)
        before_state = _ordering(current_lists['beforeSystemDefined'], current_lists['afterSystemDefined'])
        desired = _ordering(new_before, new_after)
        changed = desired != before_state

        result = current
        if changed:
            result = desired
            if not self.module.check_mode:
                response = self.client.put(self.path, desired, query=self.query)
                if isinstance(response, dict) and response.get('orderedFirewallPolicyIds') is not None:
                    result = response
        output = {'changed': changed, 'ordering': result}
        if self.module._diff:
            output['diff'] = {'before': before_state, 'after': desired}
        self.module.exit_json(**output)


def argument_spec():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    spec.update(
        source_zone=dict(type='str', required=True, aliases=['source_firewall_zone_id']),
        destination_zone=dict(type='str', required=True, aliases=['destination_firewall_zone_id']),
        before_system_defined=dict(type='list', elements='str'),
        after_system_defined=dict(type='list', elements='str'),
        position=dict(type='str', default='top', choices=['top', 'bottom']),
    )
    return spec


def main():
    module = AnsibleModule(argument_spec=argument_spec(), supports_check_mode=True,
                           required_one_of=[('before_system_defined', 'after_system_defined')])
    try:
        FirewallPolicyOrdering(module).run()
    except (UnifiNetworkError, FilterError) as exc:
        fail_from_exception(module, exc)


if __name__ == '__main__':
    main()
