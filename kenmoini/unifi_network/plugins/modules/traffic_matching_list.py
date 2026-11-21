#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: traffic_matching_list
short_description: Manage traffic matching lists (IP and port groups) in UniFi Network
version_added: "2.0.0"
description:
  - Creates, updates or deletes traffic matching lists, the reusable IP address and port groups referenced by firewall policies.
  - The list is found by O(name), or by O(id) when given (which also allows renaming it).
  - Only the options you set are managed; the module reads the list first and only writes when something differs.
options:
  name:
    description:
      - Name of the traffic matching list. Used to find the list when O(id) is not set.
      - Required unless O(id) is set.
    type: str
  id:
    description:
      - UUID of an existing list to manage. When set, O(name) renames the list.
    type: str
  state:
    description:
      - V(present) creates or updates the list, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  type:
    description:
      - What the list matches. Required when creating a list.
    type: str
    choices: [ipv4_addresses, ipv6_addresses, ports]
  items:
    description:
      - The entries of the list. The list is authoritative; order does not matter.
      - "For V(ipv4_addresses): an address (V(192.168.1.10)), a subnet in CIDR notation (V(10.0.0.0/24)),
        or an inclusive range (V(172.16.0.1-172.16.0.20))."
      - "For V(ipv6_addresses): an address (V(2001:db8::1)) or a subnet (V(2001:db8::/64))."
      - "For V(ports): a port number (V(443)) or an inclusive range (V(8000-8100))."
      - Subnets are normalized to their network address, so V(10.0.0.5/24) is stored as V(10.0.0.0/24).
      - Required when creating a list.
    type: list
    elements: raw
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Maintain a list of hosts that may reach the management network
  kenmoini.unifi_network.traffic_matching_list:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Admin Workstations
    type: ipv4_addresses
    items:
      - 192.168.10.15
      - 192.168.10.16
      - 10.20.0.0/28
      - 10.30.0.100-10.30.0.110

- name: Web ports
  kenmoini.unifi_network.traffic_matching_list:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Web
    type: ports
    items: [80, 443, "8000-8100"]

- name: IPv6 prefixes
  kenmoini.unifi_network.traffic_matching_list:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Trusted v6
    type: ipv6_addresses
    items:
      - 2001:db8:10::/64
      - 2001:db8::53

- name: Preview a change (run with --check --diff)
  kenmoini.unifi_network.traffic_matching_list:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Web
    items: [443]
  check_mode: true
  diff: true

- name: Remove a list
  kenmoini.unifi_network.traffic_matching_list:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Web
    state: absent
'''

RETURN = r'''
traffic_matching_list:
  description:
    - The traffic matching list as returned by the API after the change, or the predicted list in check mode.
    - Empty when O(state=absent).
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "name": "Web", "type": "PORTS",
           "items": [{"type": "PORT_NUMBER", "value": 443}, {"type": "PORT_NUMBER_RANGE", "start": 8000, "stop": 8100}]}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.convert import parse_ip_item, parse_port_item
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import StateResource, run_state_module

TYPES = {'ipv4_addresses': 'IPV4_ADDRESSES', 'ipv6_addresses': 'IPV6_ADDRESSES', 'ports': 'PORTS'}


class TrafficMatchingList(StateResource):
    path = 'traffic-matching-lists'
    result_key = 'traffic_matching_list'
    label = 'traffic matching list'
    create_required = {'type': 'type', 'items': 'items'}

    def to_api(self, current):
        p = self.params
        desired = {}
        if p['name'] is not None:
            desired['name'] = p['name']
        list_type = TYPES.get(p['type']) or (current or {}).get('type')
        if p['type']:
            desired['type'] = list_type
        if p['items'] is not None:
            if list_type == 'PORTS':
                desired['items'] = [parse_port_item(i) for i in p['items']]
            elif list_type == 'IPV4_ADDRESSES':
                desired['items'] = [parse_ip_item(i, 4) for i in p['items']]
            elif list_type == 'IPV6_ADDRESSES':
                desired['items'] = [parse_ip_item(i, 6) for i in p['items']]
            else:
                raise UnifiNetworkError('Set type so the items can be interpreted')
        return desired


def main():
    spec = state_argument_spec()
    spec.update(
        name=dict(type='str'),
        type=dict(type='str', choices=list(TYPES)),
        items=dict(type='list', elements='raw'),
    )
    run_state_module(TrafficMatchingList, spec, required_one_of=[('name', 'id')])


if __name__ == '__main__':
    main()
