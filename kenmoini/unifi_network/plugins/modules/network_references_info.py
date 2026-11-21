#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: network_references_info
short_description: List what references a UniFi Network
version_added: "1.0.0"
description:
  - Returns the resources (clients, devices, WiFi broadcasts, NAT rules, routes...) that reference a Network.
  - Useful before deleting a Network, which fails while it is still referenced unless C(force) is used.
  - Replaces C(network_references), which now redirects to this module.
options:
  network:
    description:
      - The Network, given as its UUID or its name.
    required: true
    type: str
    aliases: [network_id, network_uuid, unifi_network_network_id, unifi_network_network_uuid]
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Check what still uses the IoT network
  kenmoini.unifi_network.network_references_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    network: IoT
  register: r_refs

- name: Fail if anything references it
  ansible.builtin.assert:
    that: r_refs.network_references.referenceResources | length == 0
'''

RETURN = r'''
network_references:
  description: The references to the Network, exactly as returned by the API.
  returned: always
  type: dict
  sample: {"referenceResources": [{"resourceType": "WIFI", "referenceCount": 1, "references": [{"referenceId": "497f6eca-6276-4993-bfeb-53cbbbba6f08"}]}]}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import (
    connection_argument_spec,
    site_argument_spec,
)
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_single_info_module


def resolve(module, refs):
    return {'network_id': refs.resolve('network', module.params['network'])}, None


def main():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    spec['network'] = dict(type='str', required=True,
                           aliases=['network_id', 'network_uuid', 'unifi_network_network_id', 'unifi_network_network_uuid'])
    run_single_info_module('networks/{network_id}/references', 'network_references', spec, resolve=resolve)


if __name__ == '__main__':
    main()
