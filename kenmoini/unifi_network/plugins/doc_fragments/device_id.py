# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for specifying the Device ID.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_device_id:
    description:
      - The Device UUID to query for device information.
    required: true
    aliases: ['device_uuid', 'device', 'device_id', 'unifi_network_device_uuid']
    type: str
    env:
      - name: UNIFI_NETWORK_DEVICE_ID
      - name: UNIFI_NETWORK_DEVICE_UUID
"""