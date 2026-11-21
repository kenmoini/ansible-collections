#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: acl_rule_info
short_description: List ACL Rules in UniFi Network
version_added: "1.0.0"
description:
  - "Lists ACL Rules at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(type) (string): eq, ne, in, notIn."
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(enabled) (boolean): eq, ne."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(description) (string): isNull, isNotNull, eq, ne, in, notIn, like."
  - "C(action) (string): eq, ne, in, notIn."
  - "C(index) (integer): eq, ne, gt, ge, lt, le, in, notIn."
  - "C(protocolFilter) (set(string)): isNull, isNotNull, contains, containsAny, containsAll, containsExactly."
  - "C(networkId) (uuid): isNull, isNotNull, eq, ne, in, notIn."
  - "C(enforcingDeviceFilter.deviceIds) (set(uuid)): isNull, isNotNull, contains, containsAny, containsAll, containsExactly."
  - "C(metadata.origin) (string): eq, ne, in, notIn."
  - "C(sourceFilter.type) (string): isNull, isNotNull, eq, ne, in, notIn."
  - "C(sourceFilter.ipAddressesOrSubnets) (set(string)): contains, containsAny, containsAll, containsExactly."
  - "C(sourceFilter.portFilter) (set(integer)): isNull, isNotNull, contains, containsAny, containsAll, containsExactly."
  - "C(sourceFilter.networkIds) (set(uuid)): contains, containsAny, containsAll, containsExactly."
  - "C(sourceFilter.macAddresses) (set(string)): contains, containsAny, containsAll, containsExactly."
  - "C(sourceFilter.prefixLength) (integer): isNull, isNotNull, eq, ne, gt, ge, lt, le, in, notIn."
  - "C(destinationFilter.type) (string): isNull, isNotNull, eq, ne, in, notIn."
  - "C(destinationFilter.ipAddressesOrSubnets) (set(string)): contains, containsAny, containsAll, containsExactly."
  - "C(destinationFilter.portFilter) (set(integer)): isNull, isNotNull, contains, containsAny, containsAll, containsExactly."
  - "C(destinationFilter.networkIds) (set(uuid)): contains, containsAny, containsAll, containsExactly."
  - "C(destinationFilter.macAddresses) (set(string)): contains, containsAny, containsAll, containsExactly."
  - "C(destinationFilter.prefixLength) (integer): isNull, isNotNull, eq, ne, gt, ge, lt, le, in, notIn."
  - "Replaces C(acl_rules_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single ACL Rule to return.
      - The result is a list with that ACL Rule, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [acl_rule_id, rule_id, unifi_network_acl_rule_id, unifi_network_acl_rule_uuid]
  name:
    description:
      - Return only ACL Rules with exactly this name.
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
- name: List all ACL Rules
  kenmoini.unifi_network.acl_rule_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_acl_rules

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List ACL Rules
      kenmoini.unifi_network.acl_rule_info:
        unifi_network_site_id: default
      register: r_acl_rules

- name: Get a single ACL Rule by UUID
  kenmoini.unifi_network.acl_rule_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a ACL Rule by name
  kenmoini.unifi_network.acl_rule_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the ACL Rule
  ansible.builtin.debug:
    msg: "{{ r_named.acl_rules[0].id }}"
  when: r_named.acl_rules | length > 0

- name: Filter ACL Rules with one condition
  kenmoini.unifi_network.acl_rule_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: enabled
      function: eq
      value: true
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.acl_rule_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: enabled
        function: eq
        value: true
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.acl_rule_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 ACL Rules
  kenmoini.unifi_network.acl_rule_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
acl_rules:
  description:
    - The matching ACL Rules, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - action: ALLOW|BLOCK
      description: string
      destinationFilter:
        ipAddressesOrSubnets:
        - string
        portFilter:
        - 1
        type: IP_ADDRESSES_OR_SUBNETS
      enabled: true
      enforcingDeviceFilter:
        deviceIds:
        - 497f6eca-6276-4993-bfeb-53cbbbba6f08
        type: DEVICES
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      index: 1
      metadata:
        origin: DERIVED
      name: string
      protocolFilter:
      - TCP
      sourceFilter:
        ipAddressesOrSubnets:
        - string
        portFilter:
        - 1
        type: IP_ADDRESSES_OR_SUBNETS
      type: IPV4
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module(
        'acl-rules',
        'acl_rules',
        id_aliases=['acl_rule_id', 'rule_id', 'unifi_network_acl_rule_id', 'unifi_network_acl_rule_uuid'],
    )


if __name__ == '__main__':
    main()
