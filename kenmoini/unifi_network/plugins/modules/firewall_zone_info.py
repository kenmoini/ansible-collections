#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: firewall_zone_info
short_description: List Firewall Zones in UniFi Network
version_added: "1.0.0"
description:
  - "Lists Firewall Zones at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(metadata.origin) (string): eq, ne, in, notIn."
  - "C(metadata.configurable) (boolean): eq, ne, isNull, isNotNull."
  - "Replaces C(firewall_zones_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single Firewall Zone to return.
      - The result is a list with that Firewall Zone, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [firewall_zone_id, zone_id, unifi_network_firewall_zone_id, unifi_network_firewall_zone_uuid]
  name:
    description:
      - Return only Firewall Zones with exactly this name.
      - Sent to the API as C(name.eq(...)) and combined with O(unifi_network_filters) using AND.
    type: str
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.filters
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: List all Firewall Zones
  kenmoini.unifi_network.firewall_zone_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_firewall_zones

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Firewall Zones
      kenmoini.unifi_network.firewall_zone_info:
        unifi_network_site_id: default
      register: r_firewall_zones

- name: Get a single Firewall Zone by UUID
  kenmoini.unifi_network.firewall_zone_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a Firewall Zone by name
  kenmoini.unifi_network.firewall_zone_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the Firewall Zone
  ansible.builtin.debug:
    msg: "{{ r_named.firewall_zones[0].id }}"
  when: r_named.firewall_zones | length > 0

- name: Filter Firewall Zones with one condition
  kenmoini.unifi_network.firewall_zone_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: metadata.origin
      function: eq
      value: "USER_DEFINED"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.firewall_zone_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: metadata.origin
        function: eq
        value: "USER_DEFINED"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.firewall_zone_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Firewall Zones
  kenmoini.unifi_network.firewall_zone_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
firewall_zones:
  description:
    - The matching Firewall Zones, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - id: ffcdb32c-6278-4364-8947-df4f77118df8
      metadata:
        origin: SYSTEM_DEFINED
      name: Hotspot|My custom zone
      networkIds:
      - dfb21062-8ea0-4dca-b1d8-1eb3da00e58b
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module(
        'firewall/zones',
        'firewall_zones',
        id_aliases=['firewall_zone_id', 'zone_id', 'unifi_network_firewall_zone_id', 'unifi_network_firewall_zone_uuid'],
    )


if __name__ == '__main__':
    main()
