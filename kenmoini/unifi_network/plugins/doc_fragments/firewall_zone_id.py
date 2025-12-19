# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for specifying the Zone ID.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_firewall_zone_id:
    description:
      - The Firewall Zone UUID to query for information.
    required: true
    aliases: ['firewall_zone_uuid', 'firewall_zone_id', 'zone', 'zone_id', 'zone_uuid', 'unifi_network_firewall_zone_uuid']
    type: str
    env:
      - name: UNIFI_NETWORK_FIREWALL_ZONE_ID
      - name: UNIFI_NETWORK_FIREWALL_ZONE_UUID
"""