#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: device_info
short_description: List adopted Devices in UniFi Network
version_added: "1.0.0"
description:
  - "Lists adopted Devices at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(macAddress) (string): eq, ne, in, notIn."
  - "C(ipAddress) (string): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(model) (string): eq, ne, in, notIn."
  - "C(state) (string): eq, ne, in, notIn."
  - "C(supported) (boolean): eq, ne."
  - "C(firmwareVersion) (string): isNull, isNotNull, eq, ne, gt, ge, lt, le, like, in, notIn."
  - "C(firmwareUpdatable) (boolean): eq, ne."
  - "C(features) (set(string)): isEmpty, contains, containsAny, containsAll, containsExactly."
  - "C(interfaces) (set(string)): isEmpty, contains, containsAny, containsAll, containsExactly."
  - "Replaces C(adopted_devices_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single adopted Device to return.
      - The result is a list with that adopted Device, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [device_id, device_uuid, unifi_network_device_id, unifi_network_device_uuid]
  name:
    description:
      - Return only adopted Devices with exactly this name.
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
- name: List all adopted Devices
  kenmoini.unifi_network.device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_devices

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List adopted Devices
      kenmoini.unifi_network.device_info:
        unifi_network_site_id: default
      register: r_devices

- name: Get a single adopted Device by UUID
  kenmoini.unifi_network.device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a adopted Device by name
  kenmoini.unifi_network.device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the adopted Device
  ansible.builtin.debug:
    msg: "{{ r_named.devices[0].id }}"
  when: r_named.devices | length > 0

- name: Filter adopted Devices with one condition
  kenmoini.unifi_network.device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: state
      function: eq
      value: "ONLINE"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: state
        function: eq
        value: "ONLINE"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 adopted Devices
  kenmoini.unifi_network.device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
devices:
  description:
    - The matching adopted Devices, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - features:
      - switching
      firmwareUpdatable: true
      firmwareVersion: 6.6.55
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      interfaces:
      - ports
      ipAddress: 192.168.1.55
      macAddress: 94:2a:6f:26:c6:ca
      model: UHDIW
      name: IW HD
      state: ONLINE
      supported: true
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module(
        'devices',
        'devices',
        id_aliases=['device_id', 'device_uuid', 'unifi_network_device_id', 'unifi_network_device_uuid'],
    )


if __name__ == '__main__':
    main()
