#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: country_info
short_description: List Countries in UniFi Network
version_added: "1.0.0"
description:
  - "Lists Countries from the UniFi Network application, optionally narrowed by name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(code) (string): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "Replaces C(countries_info), which now redirects to this module."
options:
  name:
    description:
      - Return only Countries with exactly this name.
      - Sent to the API as C(name.eq(...)) and combined with O(unifi_network_filters) using AND.
    type: str
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.filters
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: List all Countries
  kenmoini.unifi_network.country_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
  register: r_countries

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Countries
      kenmoini.unifi_network.country_info:
      register: r_countries

- name: Get a Country by name
  kenmoini.unifi_network.country_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    name: Example
  register: r_named

- name: Show the UUID of the Country
  ansible.builtin.debug:
    msg: "{{ r_named.countries[0].id }}"
  when: r_named.countries | length > 0

- name: Filter Countries with one condition
  kenmoini.unifi_network.country_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    filters:
      property: code
      function: in
      value: ["US", "CA"]
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.country_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    filters_match: any
    filters:
      - property: code
        function: in
        value: ["US", "CA"]
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.country_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Countries
  kenmoini.unifi_network.country_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    limit: 10
  register: r_some
'''

RETURN = r'''
countries:
  description:
    - The matching Countries, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - code: CK|FK|KY
      name: Cook Islands|Falkland Islands, Malvinas|Cayman Islands
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('countries', 'countries', site_scoped=False, id_lookup=None)


if __name__ == '__main__':
    main()
