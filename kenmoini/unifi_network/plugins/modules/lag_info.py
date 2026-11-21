#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: lag_info
short_description: List Link Aggregation Groups (LAGs) in UniFi Network
version_added: "2.0.0"
description:
  - "Lists Link Aggregation Groups (LAGs) at a site of the UniFi Network application, optionally narrowed by ID or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(type) (string): eq, ne, in, notIn."
  - "C(switchStackId) (uuid): eq, ne, in, notIn, isNull, isNotNull."
  - "C(mcLagDomainId) (uuid): eq, ne, in, notIn, isNull, isNotNull."
  - "C(members.deviceId) (set(uuid)): contains, containsAny, containsAll, containsExactly."
  - "C(members.portIdxs) (set(integer)): contains, containsAny, containsAll, containsExactly."
  - "C(metadata.origin) (string): eq, ne, in, notIn."
options:
  id:
    description:
      - UUID of a single Link Aggregation Group (LAG) to return.
      - The result is a list with that Link Aggregation Group (LAG), or an empty list when it does not exist.
      - Mutually exclusive with O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [lag_id]
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
- name: List all Link Aggregation Groups (LAGs)
  kenmoini.unifi_network.lag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_lags

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Link Aggregation Groups (LAGs)
      kenmoini.unifi_network.lag_info:
        unifi_network_site_id: default
      register: r_lags

- name: Get a single Link Aggregation Group (LAG) by UUID
  kenmoini.unifi_network.lag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Filter Link Aggregation Groups (LAGs) with one condition
  kenmoini.unifi_network.lag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: type
      function: eq
      value: "LOCAL"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.lag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: type
        function: eq
        value: "LOCAL"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.lag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Link Aggregation Groups (LAGs)
  kenmoini.unifi_network.lag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
lags:
  description:
    - The matching Link Aggregation Groups (LAGs), exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      members:
      - deviceId: 497f6eca-6276-4993-bfeb-53cbbbba6f08
        portIdxs: []
      metadata:
        origin: DERIVED
        source: SDWAN
      type: LOCAL
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('switching/lags', 'lags', id_aliases=['lag_id'], name_lookup=None)


if __name__ == '__main__':
    main()
