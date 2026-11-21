#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: hotspot_voucher_info
short_description: List Hotspot Vouchers in UniFi Network
version_added: "1.0.0"
description:
  - "Lists Hotspot Vouchers at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(createdAt) (timestamp): eq, ne, gt, ge, lt, le."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(code) (string): eq, ne, in, notIn."
  - "C(authorizedGuestLimit) (integer): isNull, isNotNull, eq, ne, gt, ge, lt, le."
  - "C(authorizedGuestCount) (integer): eq, ne, gt, ge, lt, le."
  - "C(activatedAt) (timestamp): eq, ne, gt, ge, lt, le."
  - "C(expiresAt) (timestamp): eq, ne, gt, ge, lt, le."
  - "C(expired) (boolean): eq, ne."
  - "C(timeLimitMinutes) (integer): eq, ne, gt, ge, lt, le."
  - "C(dataUsageLimitMBytes) (integer): isNull, isNotNull, eq, ne, gt, ge, lt, le."
  - "C(rxRateLimitKbps) (integer): isNull, isNotNull, eq, ne, gt, ge, lt, le."
  - "C(txRateLimitKbps) (integer): isNull, isNotNull, eq, ne, gt, ge, lt, le."
  - "Replaces C(hotspot_vouchers_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single Hotspot Voucher to return.
      - The result is a list with that Hotspot Voucher, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [voucher_id, hotspot_voucher_id, unifi_network_hotspot_voucher_id, unifi_network_hotspot_voucher_uuid]
  name:
    description:
      - Return only Hotspot Vouchers with exactly this name.
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
- name: List all Hotspot Vouchers
  kenmoini.unifi_network.hotspot_voucher_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_hotspot_vouchers

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Hotspot Vouchers
      kenmoini.unifi_network.hotspot_voucher_info:
        unifi_network_site_id: default
      register: r_hotspot_vouchers

- name: Get a single Hotspot Voucher by UUID
  kenmoini.unifi_network.hotspot_voucher_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a Hotspot Voucher by name
  kenmoini.unifi_network.hotspot_voucher_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the Hotspot Voucher
  ansible.builtin.debug:
    msg: "{{ r_named.hotspot_vouchers[0].id }}"
  when: r_named.hotspot_vouchers | length > 0

- name: Filter Hotspot Vouchers with one condition
  kenmoini.unifi_network.hotspot_voucher_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: expired
      function: eq
      value: false
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.hotspot_voucher_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: expired
        function: eq
        value: false
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.hotspot_voucher_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Hotspot Vouchers
  kenmoini.unifi_network.hotspot_voucher_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
hotspot_vouchers:
  description:
    - The matching Hotspot Vouchers, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - activatedAt: '2025-01-01T00:00:00Z'
      authorizedGuestCount: 0
      authorizedGuestLimit: 1
      code: 4861409510
      createdAt: '2025-01-01T00:00:00Z'
      dataUsageLimitMBytes: 1024
      expired: true
      expiresAt: '2025-01-01T00:00:00Z'
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      name: hotel-guest
      rxRateLimitKbps: 1000
      timeLimitMinutes: 1440
      txRateLimitKbps: 1000
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module(
        'hotspot/vouchers',
        'hotspot_vouchers',
        id_aliases=['voucher_id', 'hotspot_voucher_id', 'unifi_network_hotspot_voucher_id', 'unifi_network_hotspot_voucher_uuid'],
    )


if __name__ == '__main__':
    main()
