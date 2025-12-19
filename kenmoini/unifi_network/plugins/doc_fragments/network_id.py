# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for specifying the Network ID.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_network_id:
    description:
      - The Network UUID to query for additional information.
    required: false
    aliases: ['network_uuid', 'network', 'unifi_network_network_uuid']
    type: str
    env:
      - name: UNIFI_NETWORK_NETWORK_ID
      - name: UNIFI_NETWORK_NETWORK_UUID
"""