#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: radius_profile_info
short_description: List RADIUS Profiles in UniFi Network
version_added: "1.0.0"
description:
  - "Lists RADIUS Profiles at a site of the UniFi Network application, optionally narrowed by ID, name or filters."
  - "Every page of results is fetched, so all matching items are returned (the API returns 25 per page by default)."
  - "Filterable properties for O(unifi_network_filters), with their type and allowed functions:"
  - "C(id) (uuid): eq, ne, in, notIn."
  - "C(name) (string): eq, ne, in, notIn, like."
  - "C(metadata.origin) (string): eq, ne, in, notIn."
  - "Replaces C(radius_profiles_info), which now redirects to this module."
options:
  id:
    description:
      - UUID of a single RADIUS Profile to return.
      - The result is a list with that RADIUS Profile, or an empty list when it does not exist.
      - Mutually exclusive with O(name), O(unifi_network_filters) and O(unifi_network_filters_raw).
    type: str
    aliases: [radius_profile_id]
  name:
    description:
      - Return only RADIUS Profiles with exactly this name.
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
- name: List all RADIUS Profiles
  kenmoini.unifi_network.radius_profile_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_radius_profiles

- name: Set the connection once for every module in this collection
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ unifi_api_key }}"
      unifi_network_skip_tls_verify: true
  block:
    - name: List RADIUS Profiles
      kenmoini.unifi_network.radius_profile_info:
        unifi_network_site_id: default
      register: r_radius_profiles

- name: Get a single RADIUS Profile by UUID
  kenmoini.unifi_network.radius_profile_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
  register: r_one

- name: Get a RADIUS Profile by name
  kenmoini.unifi_network.radius_profile_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Example
  register: r_named

- name: Show the UUID of the RADIUS Profile
  ansible.builtin.debug:
    msg: "{{ r_named.radius_profiles[0].id }}"
  when: r_named.radius_profiles | length > 0

- name: Filter RADIUS Profiles with one condition
  kenmoini.unifi_network.radius_profile_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters:
      property: metadata.origin
      function: eq
      value: "USER_DEFINED"
  register: r_filtered

- name: Combine conditions; filters_match any ORs them, all (default) ANDs them
  kenmoini.unifi_network.radius_profile_info:
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
  kenmoini.unifi_network.radius_profile_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    filters_raw: "not(id.eq('497f6eca-6276-4993-bfeb-53cbbbba6f08'))"
  register: r_raw

- name: Return at most 10 RADIUS Profiles
  kenmoini.unifi_network.radius_profile_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    limit: 10
  register: r_some
'''

RETURN = r'''
radius_profiles:
  description:
    - The matching RADIUS Profiles, exactly as returned by the API (camelCase keys).
  returned: always
  type: list
  elements: dict
  sample:
    - id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
      metadata:
        origin: DERIVED
      name: string
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module


def main():
    run_info_module('radius/profiles', 'radius_profiles', id_lookup='filter', id_aliases=['radius_profile_id'])


if __name__ == '__main__':
    main()
