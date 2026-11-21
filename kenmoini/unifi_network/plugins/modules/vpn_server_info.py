#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: vpn_server_info
short_description: List VPN Servers in UniFi Network
version_added: "1.0.0"
description:
  - "Lists VPN Servers at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(type) (string): eq, ne, in, notIn."
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(enabled) (boolean): eq, ne."
  - "C(metadata.origin) (string): eq, ne, in, notIn."
  - "Replaces C(vpn_servers_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single VPN Server to return.
      - The result is a list with that VPN Server, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [vpn_server_id]
  name:
    description:
      - Return only VPN Servers with exactly this name.
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
- name: List all VPN Servers
  kenmoini.unifi_network.vpn_server_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_vpn_servers

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List VPN Servers
      kenmoini.unifi_network.vpn_server_info:
        unifi_network_site_id: default
      register: r_vpn_servers

- name: Get a single VPN Server by UUID
  kenmoini.unifi_network.vpn_server_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a VPN Server by name
  kenmoini.unifi_network.vpn_server_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the VPN Server
  ansible.builtin.debug:
    msg: "{{ r_named.vpn_servers[0].id }}"
  when: r_named.vpn_servers | length > 0

- name: Filter VPN Servers with one condition
  kenmoini.unifi_network.vpn_server_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: enabled
      function: eq
      value: true
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.vpn_server_info:
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
  kenmoini.unifi_network.vpn_server_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 VPN Servers
  kenmoini.unifi_network.vpn_server_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
vpn_servers:
  description:
    - The matching VPN Servers, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - enabled: true
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      metadata:
        origin: DERIVED
      name: string
      type: L2TP
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('vpn/servers', 'vpn_servers', id_lookup='filter', id_aliases=['vpn_server_id'])


if __name__ == '__main__':
    main()
