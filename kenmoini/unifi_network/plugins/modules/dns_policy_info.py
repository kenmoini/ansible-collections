#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: dns_policy_info
short_description: List DNS Policies in UniFi Network
version_added: "2.0.0"
description:
  - "Lists DNS Policies at a site of the UniFi Network application, optionally narrowed by ID or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(type) (string): eq, ne, in, notIn."
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(enabled) (boolean): eq, ne."
  - "C(domain) (string): eq, ne, in, notIn, like."
  - "C(ipv4Address) (string): eq, ne, in, notIn, like."
  - "C(ipv6Address) (string): eq, ne, in, notIn, like."
  - "C(targetDomain) (string): eq, ne, in, notIn, like."
  - "C(mailServerDomain) (string): eq, ne, in, notIn, like."
  - "C(text) (string): eq, ne, in, notIn, like."
  - "C(serverDomain) (string): eq, ne, in, notIn, like."
  - "C(ipAddress) (string): eq, ne, in, notIn, like."
  - "C(ttlSeconds) (integer): eq, ne, gt, ge, lt, le, in, notIn."
  - "C(priority) (integer): eq, ne, gt, ge, lt, le, in, notIn."
  - "C(service) (string): eq, ne, in, notIn."
  - "C(protocol) (string): eq, ne, in, notIn."
  - "C(port) (integer): eq, ne, gt, ge, lt, le, in, notIn."
  - "C(weight) (integer): eq, ne, gt, ge, lt, le, in, notIn."
options:
  id:
    description:
      - UUID of a single DNS Policy to return.
      - The result is a list with that DNS Policy, or an empty list when it does not exist.
      - Mutually exclusive with O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [dns_policy_id, policy_id]
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
- name: List all DNS Policies
  kenmoini.unifi_network.dns_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_dns_policies

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List DNS Policies
      kenmoini.unifi_network.dns_policy_info:
        unifi_network_site_id: default
      register: r_dns_policies

- name: Get a single DNS Policy by UUID
  kenmoini.unifi_network.dns_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Filter DNS Policies with one condition
  kenmoini.unifi_network.dns_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: domain
      function: eq
      value: "nas.home.arpa"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.dns_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: domain
        function: eq
        value: "nas.home.arpa"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.dns_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 DNS Policies
  kenmoini.unifi_network.dns_policy_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
dns_policies:
  description:
    - The matching DNS Policies, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - domain: example.com
      enabled: true
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      ipv6Address: cafe::babe
      metadata:
        origin: DERIVED
        source: SDWAN
      ttlSeconds: 14400
      type: AAAA_RECORD
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('dns/policies', 'dns_policies', id_aliases=['dns_policy_id', 'policy_id'], name_lookup=None)


if __name__ == '__main__':
    main()
