#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: firewall_policy_info
short_description: List Firewall Policies in UniFi Network
version_added: "2.0.0"
description:
  - "Lists Firewall Policies at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(source.zoneId) (uuid): eq, ne, in, notIn."
  - "C(destination.zoneId) (uuid): eq, ne, in, notIn."
  - "C(metadata.origin) (string): eq, ne, in, notIn."
options:
  id:
    description:
      - UUID of a single Firewall Policy to return.
      - The result is a list with that Firewall Policy, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [firewall_policy_id, policy_id]
  name:
    description:
      - Return only Firewall Policies with exactly this name.
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
- name: List all Firewall Policies
  kenmoini.unifi_network.firewall_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_firewall_policies

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Firewall Policies
      kenmoini.unifi_network.firewall_policy_info:
        unifi_network_site_id: default
      register: r_firewall_policies

- name: Get a single Firewall Policy by UUID
  kenmoini.unifi_network.firewall_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a Firewall Policy by name
  kenmoini.unifi_network.firewall_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the Firewall Policy
  ansible.builtin.debug:
    msg: "{{ r_named.firewall_policies[0].id }}"
  when: r_named.firewall_policies | length > 0

- name: Filter Firewall Policies with one condition
  kenmoini.unifi_network.firewall_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: metadata.origin
      function: eq
      value: "USER_DEFINED"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.firewall_policy_info:
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
  kenmoini.unifi_network.firewall_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Firewall Policies
  kenmoini.unifi_network.firewall_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
firewall_policies:
  description:
    - The matching Firewall Policies, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - action:
        allowReturnTraffic: true
        type: ALLOW
      connectionStateFilter:
      - NEW
      description: A description for my firewall policy
      destination:
        trafficFilter:
          applicationFilter: {}
          portFilter:
            matchOpposite: true
            type: PORTS
          type: APPLICATION
        zoneId: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      enabled: true
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      index: 1
      ipProtocolScope:
        ipVersion: IPV4
        protocolFilter:
          matchOpposite: true
          protocol:
            name: AH
          type: NAMED_PROTOCOL
      ipsecFilter: MATCH_ENCRYPTED
      loggingEnabled: true
      metadata:
        origin: DERIVED
      name: My firewall policy
      reportFlowEnabled: true
      schedule:
        mode: CUSTOM
        repeatOnDays:
        - MONDAY
        startDate: '2025-12-31'
        stopDate: '2025-12-31'
        timeFilter:
          startTime: '21:37'
          stopTime: '21:37'
      source:
        trafficFilter:
          ipv6IidFilter: {}
          macAddressFilter: string
          portFilter:
            matchOpposite: true
            type: PORTS
          type: IPV6_IID
        zoneId: 497f6eca-6276-4993-bfeb-53cbbbba6f08
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('firewall/policies', 'firewall_policies', id_aliases=['firewall_policy_id', 'policy_id'])


if __name__ == '__main__':
    main()
