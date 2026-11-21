#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: network_info
short_description: List Networks in UniFi Network
version_added: "1.0.0"
description:
  - "Lists Networks at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(management) (string): eq, ne, in, notIn."
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(enabled) (boolean): eq, ne."
  - "C(vlanId) (integer): eq, ne, gt, ge, lt, le, in, notIn."
  - "C(deviceId) (uuid): eq, ne, in, notIn, isNull, isNotNull."
  - "C(metadata.origin) (string): eq, ne, in, notIn."
  - "Replaces C(networks_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single Network to return.
      - The result is a list with that Network, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [network_id, network_uuid, unifi_network_network_id, unifi_network_network_uuid]
  name:
    description:
      - Return only Networks with exactly this name.
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
- name: List all Networks
  kenmoini.unifi_network.network_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_networks

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Networks
      kenmoini.unifi_network.network_info:
        unifi_network_site_id: default
      register: r_networks

- name: Get a single Network by UUID
  kenmoini.unifi_network.network_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a Network by name
  kenmoini.unifi_network.network_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the Network
  ansible.builtin.debug:
    msg: "{{ r_named.networks[0].id }}"
  when: r_named.networks | length > 0

- name: Filter Networks with one condition
  kenmoini.unifi_network.network_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: vlanId
      function: gt
      value: 10
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.network_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: vlanId
        function: gt
        value: 10
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.network_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Networks
  kenmoini.unifi_network.network_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
networks:
  description:
    - The matching Networks, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - default: true
      enabled: true
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      management: GATEWAY
      metadata:
        origin: ORCHESTRATED
      name: Default Network
      vlanId: 1
      zoneId: 497f6eca-6276-4993-bfeb-53cbbbba6f08
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module(
        'networks',
        'networks',
        id_aliases=['network_id', 'network_uuid', 'unifi_network_network_id', 'unifi_network_network_uuid'],
    )


if __name__ == '__main__':
    main()
