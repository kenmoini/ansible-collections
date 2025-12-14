# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for specifying the Site ID.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_site_id:
    description:
      - The Site UUID to query for networks.
    required: true
    aliases: ['site_id', 'site_uuid', 'site', 'unifi_network_site_uuid']
    type: str
    env:
      - name: UNIFI_NETWORK_SITE_ID
      - name: UNIFI_NETWORK_SITE_UUID
"""