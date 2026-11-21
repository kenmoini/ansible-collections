#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: client_info
short_description: List connected Clients in UniFi Network
version_added: "1.0.0"
description:
  - "Lists connected Clients at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(type) (string): eq, ne, in, notIn."
  - "C(macAddress) (string): isNull, isNotNull, eq, ne, in, notIn."
  - "C(ipAddress) (string): isNull, isNotNull, eq, ne, in, notIn."
  - "C(connectedAt) (timestamp): isNull, isNotNull, eq, ne, gt, ge, lt, le."
  - "C(access.type) (string): eq, ne, in, notIn."
  - "C(access.authorized) (boolean): isNull, isNotNull, eq, ne."
  - "Replaces C(clients_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single connected Client to return.
      - The result is a list with that connected Client, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [client_id, client_uuid, unifi_network_client_id, unifi_network_client_uuid]
  name:
    description:
      - Return only connected Clients with exactly this name.
      - Matched after listing because the API cannot filter connected Clients by name.
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
- name: List all connected Clients
  kenmoini.unifi_network.client_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_clients

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List connected Clients
      kenmoini.unifi_network.client_info:
        unifi_network_site_id: default
      register: r_clients

- name: Get a single connected Client by UUID
  kenmoini.unifi_network.client_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a connected Client by name
  kenmoini.unifi_network.client_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the connected Client
  ansible.builtin.debug:
    msg: "{{ r_named.clients[0].id }}"
  when: r_named.clients | length > 0

- name: Filter connected Clients with one condition
  kenmoini.unifi_network.client_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: type
      function: eq
      value: "WIRELESS"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.client_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: type
        function: eq
        value: "WIRELESS"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.client_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 connected Clients
  kenmoini.unifi_network.client_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
clients:
  description:
    - The matching connected Clients, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - access:
        type: DEFAULT
      connectedAt: '2025-01-01T00:00:00Z'
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      ipAddress: string
      name: string
      type: TELEPORT
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module(
        'clients',
        'clients',
        id_aliases=['client_id', 'client_uuid', 'unifi_network_client_id', 'unifi_network_client_uuid'],
        name_lookup='client',
    )


if __name__ == '__main__':
    main()
