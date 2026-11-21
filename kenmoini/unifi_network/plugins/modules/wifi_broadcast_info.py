#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: wifi_broadcast_info
short_description: List WiFi Broadcasts in UniFi Network
version_added: "1.0.0"
description:
  - "Lists WiFi Broadcasts at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(type) (string): eq, ne, in, notIn."
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(enabled) (boolean): eq, ne."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(broadcastingFrequenciesGHz) (set(decimal)): contains, containsAny, containsAll, containsExactly."
  - "C(metadata.origin) (string): eq, ne, in, notIn."
  - "C(network.type) (string): eq, ne, in, notIn, isNull, isNotNull."
  - "C(network.networkId) (uuid): eq, ne, in, notIn."
  - "C(securityConfiguration.type) (string): eq, ne, in, notIn."
  - "C(broadcastingDeviceFilter.type) (string): eq, ne, in, notIn, isNull, isNotNull."
  - "C(broadcastingDeviceFilter.deviceIds) (set(uuid)): contains, containsAny, containsAll, containsExactly."
  - "C(broadcastingDeviceFilter.deviceTagIds) (set(uuid)): contains, containsAny, containsAll, containsExactly."
  - "C(hotspotConfiguration.type) (string): eq, ne, in, notIn."
  - "Passphrases (including private pre-shared keys) are removed from the results."
  - "Replaces C(wifi_broadcasts_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single WiFi Broadcast to return.
      - The result is a list with that WiFi Broadcast, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [wifi_broadcast_id, unifi_network_wifi_broadcast_id, unifi_network_wifi_broadcast_uuid]
  name:
    description:
      - Return only WiFi Broadcasts with exactly this name.
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
- name: List all WiFi Broadcasts
  kenmoini.unifi_network.wifi_broadcast_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_wifi_broadcasts

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List WiFi Broadcasts
      kenmoini.unifi_network.wifi_broadcast_info:
        unifi_network_site_id: default
      register: r_wifi_broadcasts

- name: Get a single WiFi Broadcast by UUID
  kenmoini.unifi_network.wifi_broadcast_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a WiFi Broadcast by name
  kenmoini.unifi_network.wifi_broadcast_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the WiFi Broadcast
  ansible.builtin.debug:
    msg: "{{ r_named.wifi_broadcasts[0].id }}"
  when: r_named.wifi_broadcasts | length > 0

- name: Filter WiFi Broadcasts with one condition
  kenmoini.unifi_network.wifi_broadcast_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: securityConfiguration.type
      function: eq
      value: "WPA2_PERSONAL"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.wifi_broadcast_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: securityConfiguration.type
        function: eq
        value: "WPA2_PERSONAL"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.wifi_broadcast_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 WiFi Broadcasts
  kenmoini.unifi_network.wifi_broadcast_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
wifi_broadcasts:
  description:
    - The matching WiFi Broadcasts, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - broadcastingDeviceFilter:
        deviceIds:
        - 497f6eca-6276-4993-bfeb-53cbbbba6f08
        type: DEVICES
      enabled: true
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      metadata:
        origin: DERIVED
      name: string
      network:
        type: NATIVE
      securityConfiguration:
        type: OPEN
      type: IOT_OPTIMIZED
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module(
        'wifi/broadcasts',
        'wifi_broadcasts',
        id_aliases=['wifi_broadcast_id', 'unifi_network_wifi_broadcast_id', 'unifi_network_wifi_broadcast_uuid'],
        secret_paths=[('securityConfiguration', 'passphrase'), ('securityConfiguration', 'presharedKeys', '*', 'passphrase')],
    )


if __name__ == '__main__':
    main()
