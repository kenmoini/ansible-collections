# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for specifying the Device ID.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_port_id:
    description:
      - The Port ID to perform an action or query against.
    required: true
    aliases: ['port', 'port_id', 'unifi_network_device_port_id']
    type: int
"""