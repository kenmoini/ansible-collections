#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: firewall_policy_ordering_info
short_description: Get the order of user-defined firewall policies between two zones
version_added: "2.0.0"
description:
  - Returns the evaluation order of the user-defined firewall policies for one source/destination firewall zone pair,
    split into the policies evaluated before and after the system-defined ones.
  - Use M(kenmoini.unifi_network.firewall_policy_ordering) to change the order.
options:
  source_zone:
    description:
      - Source firewall zone, given as its UUID or its name.
    required: true
    type: str
    aliases: [source_firewall_zone_id]
  destination_zone:
    description:
      - Destination firewall zone, given as its UUID or its name.
    required: true
    type: str
    aliases: [destination_firewall_zone_id]
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Get the order of policies from the Internal zone to the External zone
  kenmoini.unifi_network.firewall_policy_ordering_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    source_zone: Internal
    destination_zone: External
  register: r_order
'''

RETURN = r'''
ordering:
  description: The firewall policy ordering, exactly as returned by the API.
  returned: always
  type: dict
  sample: {"orderedFirewallPolicyIds": {"beforeSystemDefined": ["497f6eca-6276-4993-bfeb-53cbbbba6f08"], "afterSystemDefined": []}}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import (
    connection_argument_spec,
    site_argument_spec,
)
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_single_info_module


def resolve(module, refs):
    return {}, {
        'sourceFirewallZoneId': refs.resolve('firewall_zone', module.params['source_zone']),
        'destinationFirewallZoneId': refs.resolve('firewall_zone', module.params['destination_zone']),
    }


def main():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    spec['source_zone'] = dict(type='str', required=True, aliases=['source_firewall_zone_id'])
    spec['destination_zone'] = dict(type='str', required=True, aliases=['destination_firewall_zone_id'])
    run_single_info_module('firewall/policies/ordering', 'ordering', spec, resolve=resolve)


if __name__ == '__main__':
    main()
