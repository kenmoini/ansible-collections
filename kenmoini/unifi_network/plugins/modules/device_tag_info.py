#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: device_tag_info
short_description: List Device Tags in UniFi Network
version_added: "1.0.0"
description:
  - "Lists Device Tags at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(deviceIds) (set(uuid)): contains, containsAny, containsAll, containsExactly."
  - "Replaces C(device_tags_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single Device Tag to return.
      - The result is a list with that Device Tag, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [device_tag_id]
  name:
    description:
      - Return only Device Tags with exactly this name.
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
- name: List all Device Tags
  kenmoini.unifi_network.device_tag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_device_tags

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List Device Tags
      kenmoini.unifi_network.device_tag_info:
        unifi_network_site_id: default
      register: r_device_tags

- name: Get a single Device Tag by UUID
  kenmoini.unifi_network.device_tag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a Device Tag by name
  kenmoini.unifi_network.device_tag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the Device Tag
  ansible.builtin.debug:
    msg: "{{ r_named.device_tags[0].id }}"
  when: r_named.device_tags | length > 0

- name: Filter Device Tags with one condition
  kenmoini.unifi_network.device_tag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: name
      function: like
      value: "AP*"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.device_tag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_match: any
    filters:
      - property: name
        function: like
        value: "AP*"
      - property: id
        function: in
        value:
          - 497f6eca-6276-4993-bfeb-53cbbbba6f08
          - 7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11
  register: r_any

- name: Use a raw filter expression for NOT or nested logic
  kenmoini.unifi_network.device_tag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 Device Tags
  kenmoini.unifi_network.device_tag_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
device_tags:
  description:
    - The matching Device Tags, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - deviceIds:
      - 497f6eca-6276-4993-bfeb-53cbbbba6f08
      id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      metadata:
        origin: ORCHESTRATED
      name: string
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('device-tags', 'device_tags', id_lookup='filter', id_aliases=['device_tag_id'])


if __name__ == '__main__':
    main()
