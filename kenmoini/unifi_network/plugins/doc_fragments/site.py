# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Option for selecting the UniFi site.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_site_id:
    description:
      - The site to work in, given as its UUID, its name, or its internal reference (V(default) for the default site).
      - Names are resolved to a UUID with one extra API call.
      - Can also be set with the E(UNIFI_NETWORK_SITE_ID), E(UNIFI_NETWORK_SITE_UUID) or E(UNIFI_NETWORK_SITE) environment variables.
    required: true
    aliases: ['site', 'site_id', 'site_uuid', 'unifi_network_site', 'unifi_network_site_uuid']
    type: str
"""
