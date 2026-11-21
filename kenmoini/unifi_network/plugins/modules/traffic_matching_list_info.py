#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: traffic_matching_list_info
short_description: List Traffic Matching Lists in UniFi Network
version_added: "1.0.0"
description:
  - "Lists Traffic Matching Lists at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "Replaces C(traffic_matching_lists_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single Traffic Matching List to return.
      - The result is a list with that Traffic Matching List, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [traffic_matching_list_id, unifi_network_traffic_matching_list_id, unifi_network_traffic_matching_list_uuid]
  name:
    description:
      - Return only Traffic Matching Lists with exactly this name.
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
- name: List all Traffic Matching Lists
  kenmoini.unifi_network.traffic_matching_list_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_traffic_matching_lists

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Traffic Matching Lists
      kenmoini.unifi_network.traffic_matching_list_info:
        unifi_network_site_id: default
      register: r_traffic_matching_lists

- name: Get a single Traffic Matching List by UUID
  kenmoini.unifi_network.traffic_matching_list_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a Traffic Matching List by name
  kenmoini.unifi_network.traffic_matching_list_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the Traffic Matching List
  ansible.builtin.debug:
    msg: "{{ r_named.traffic_matching_lists[0].id }}"
  when: r_named.traffic_matching_lists | length > 0

- name: Filter Traffic Matching Lists with one condition
  kenmoini.unifi_network.traffic_matching_list_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: name
      function: like
      value: "Blocked*"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.traffic_matching_list_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: name
        function: like
        value: "Blocked*"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.traffic_matching_list_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Traffic Matching Lists
  kenmoini.unifi_network.traffic_matching_list_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
traffic_matching_lists:
  description:
    - The matching Traffic Matching Lists, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - id: ffcdb32c-6278-4364-8947-df4f77118df8
      items:
      - type: IP_ADDRESS
        value: 192.168.1.5
      name: Allowed port list|Protected IP list
      type: IPV4_ADDRESSES
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module(
        'traffic-matching-lists',
        'traffic_matching_lists',
        id_aliases=['traffic_matching_list_id', 'unifi_network_traffic_matching_list_id', 'unifi_network_traffic_matching_list_uuid'],
    )


if __name__ == '__main__':
    main()
