#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: firewall_zone
short_description: Manage firewall zones in UniFi Network
version_added: "2.0.0"
description:
  - Creates, updates or deletes custom firewall zones, and manages which Networks belong to any zone.
  - The zone is found by O(name), or by O(id) when given (which also allows renaming it).
  - Only the options you set are managed; the module reads the zone first and only writes when something differs.
  - System-defined zones (such as Internal, External and Gateway) cannot be created, renamed or deleted,
    but their Network membership can be managed.
options:
  name:
    description:
      - Name of the firewall zone. Used to find the zone when O(id) is not set.
      - Required unless O(id) is set.
    type: str
  id:
    description:
      - UUID of an existing zone to manage. When set, O(name) renames the zone.
    type: str
  state:
    description:
      - V(present) creates or updates the zone, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  networks:
    description:
      - Networks that belong to the zone, given as names or UUIDs.
      - The list is authoritative unless O(append=true); omit it to leave membership unchanged.
      - A Network can only belong to one zone at a time.
    type: list
    elements: str
    aliases: [network_ids]
  append:
    description:
      - When V(true), add O(networks) to the zone's existing Networks instead of replacing them.
    type: bool
    default: false
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Create a zone for untrusted networks
  kenmoini.unifi_network.firewall_zone:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Untrusted
    networks:
      - IoT
      - Cameras

- name: Add one more network without touching the others
  kenmoini.unifi_network.firewall_zone:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Untrusted
    networks: [Guest]
    append: true

- name: Move a network into the system-defined Internal zone
  kenmoini.unifi_network.firewall_zone:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Internal
    networks: [Default, Servers]

- name: Rename a zone by its UUID
  kenmoini.unifi_network.firewall_zone:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
    name: Quarantine

- name: Preview a change without making it (run with --check --diff)
  kenmoini.unifi_network.firewall_zone:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Untrusted
    networks: [IoT]
  check_mode: true
  diff: true

- name: Delete a custom zone
  kenmoini.unifi_network.firewall_zone:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Quarantine
    state: absent
'''

RETURN = r'''
firewall_zone:
  description:
    - The firewall zone as returned by the API after the change, or the predicted zone in check mode.
    - Empty when O(state=absent).
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "name": "Untrusted", "networkIds": ["7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11"],
           "metadata": {"origin": "USER_DEFINED"}}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import (
    StateResource,
    origin_of,
    run_state_module,
)


class FirewallZone(StateResource):
    path = 'firewall/zones'
    result_key = 'firewall_zone'
    label = 'firewall zone'
    create_required = {'name': 'name'}

    def create_defaults(self):
        return {'networkIds': []}

    def to_api(self, current):
        desired = {}
        if self.params['name'] is not None:
            desired['name'] = self.params['name']
        networks = self.refs.resolve_many('network', self.params['networks'])
        if networks is not None:
            if self.params['append'] and current:
                existing = list(current.get('networkIds') or [])
                networks = existing + [n for n in networks if n not in existing]
            desired['networkIds'] = networks
        return desired

    def check_updatable(self, current, desired):
        if origin_of(current) == 'SYSTEM_DEFINED' and 'name' in desired and desired['name'] != current.get('name'):
            raise UnifiNetworkError('The system-defined firewall zone %r cannot be renamed; only its networks can change'
                                    % current.get('name'))

    def check_deletable(self, current):
        if origin_of(current) == 'SYSTEM_DEFINED':
            raise UnifiNetworkError('The system-defined firewall zone %r cannot be deleted' % current.get('name'))


def main():
    spec = state_argument_spec()
    spec.update(
        name=dict(type='str'),
        networks=dict(type='list', elements='str', aliases=['network_ids']),
        append=dict(type='bool', default=False),
    )
    run_state_module(FirewallZone, spec, required_one_of=[('name', 'id')])


if __name__ == '__main__':
    main()
