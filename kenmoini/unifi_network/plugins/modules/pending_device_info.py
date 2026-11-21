#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: pending_device_info
short_description: List Devices pending adoption in UniFi Network
version_added: "1.0.0"
description:
  - "Lists Devices pending adoption from the UniFi Network application, optionally narrowed by filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(macAddress) (string): eq, ne, in, notIn."
  - "C(ipAddress) (string): eq, ne, in, notIn."
  - "C(model) (string): eq, ne, in, notIn."
  - "C(state) (string): eq, ne, in, notIn."
  - "C(supported) (boolean): eq, ne."
  - "C(firmwareVersion) (string): isNull, isNotNull, eq, ne, gt, ge, lt, le, like, in, notIn."
  - "C(firmwareUpdatable) (boolean): eq, ne."
  - "C(features) (set(string)): isEmpty, contains, containsAny, containsAll, containsExactly."
  - "Replaces C(pending_devices), which now redirects to this module."
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.filters
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: List all Devices pending adoption
  kenmoini.unifi_network.pending_device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
  register: r_pending_devices

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Devices pending adoption
      kenmoini.unifi_network.pending_device_info:
      register: r_pending_devices

- name: Filter Devices pending adoption with one condition
  kenmoini.unifi_network.pending_device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    filters:
      property: model
      function: eq
      value: "U7PG2"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.pending_device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    filters_match: any
    filters:
      - property: model
        function: eq
        value: "U7PG2"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.pending_device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Devices pending adoption
  kenmoini.unifi_network.pending_device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    limit: 10
  register: r_some
'''

RETURN = r'''
pending_devices:
  description:
    - The matching Devices pending adoption, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - adoptionTargetSiteIds:
      - 497f6eca-6276-4993-bfeb-53cbbbba6f08
      features:
      - switching
      firmwareUpdatable: true
      firmwareVersion: 6.6.55
      ipAddress: 192.168.1.55
      macAddress: 94:2a:6f:26:c6:ca
      model: UHDIW
      state: ONLINE
      supported: true
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('pending-devices', 'pending_devices', site_scoped=False, id_lookup=None, name_lookup=None)


if __name__ == '__main__':
    main()
