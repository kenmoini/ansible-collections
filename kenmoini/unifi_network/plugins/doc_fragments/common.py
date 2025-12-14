# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for authenticating with the API.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_url:
    description:
      - This is the URL of your Unifi Network endpoint. Can also be specified via the environment variables C(UNIFI_NETWORK_URL) or C(UNIFI_NETWORK_API).
    required: true
    aliases: ['unifi_network_api', 'url']
    type: str
    env:
      - name: UNIFI_NETWORK_URL
      - name: UNIFI_NETWORK_API
  unifi_network_api_key:
    description:
      - This is the API Key for your Unifi Network endpoint. Can also be specified via the environment variable C(UNIFI_NETWORK_API_KEY).
    required: true
    aliases: ['api_key']
    type: str
    env:
      - name: UNIFI_NETWORK_API_KEY
  unifi_network_skip_tls_verify:
    description:
      - Whether or not to skip TLS verification. Can also be specified via the environment variable C(UNIFI_NETWORK_SKIP_TLS_VERIFY).
    required: false
    default: false
    aliases: ['skip_tls_verify']
    type: bool
    env:
      - name: UNIFI_NETWORK_SKIP_TLS_VERIFY
"""