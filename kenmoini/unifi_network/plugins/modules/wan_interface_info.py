#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: wan_interface_info
short_description: List WAN Interfaces in UniFi Network
version_added: "1.0.0"
description:
  - "Lists WAN Interfaces at a site of the UniFi Network application, optionally narrowed by name."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "This endpoint does not support API-side filtering; O(name) is matched after listing."
  - "Replaces C(wan_interfaces_info), which now redirects to this module."
options:
  name:
    description:
      - Return only WAN Interfaces with exactly this name.
      - Matched after listing because the API cannot filter WAN Interfaces by name.
    type: str
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.filters.limit
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: List all WAN Interfaces
  kenmoini.unifi_network.wan_interface_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_wan_interfaces

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List WAN Interfaces
      kenmoini.unifi_network.wan_interface_info:
        unifi_network_site_id: default
      register: r_wan_interfaces

- name: Get a WAN Interface by name
  kenmoini.unifi_network.wan_interface_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the WAN Interface
  ansible.builtin.debug:
    msg: "{{ r_named.wan_interfaces[0].id }}"
  when: r_named.wan_interfaces | length > 0

- name: Return at most 10 WAN Interfaces
  kenmoini.unifi_network.wan_interface_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
wan_interfaces:
  description:
    - The matching WAN Interfaces, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      name: Internet 1
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('wans', 'wan_interfaces', id_lookup=None, name_lookup='client', filters=False)


if __name__ == '__main__':
    main()
