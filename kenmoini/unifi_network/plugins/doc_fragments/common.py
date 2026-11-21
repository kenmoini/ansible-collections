# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for connecting to the UniFi Network Integration API.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_url:
    description:
      - URL of the UniFi console hosting the Network application, for example V(https://192.168.1.1).
      - Can also be set with the E(UNIFI_NETWORK_URL) or E(UNIFI_NETWORK_API) environment variables.
    required: true
    aliases: ['url']
    type: str
  unifi_network_api_key:
    description:
      - API key created in the UniFi Network application under C(Settings > Control Plane > Integrations).
      - Can also be set with the E(UNIFI_NETWORK_API_KEY) environment variable.
    required: true
    aliases: ['api_key']
    type: str
  unifi_network_skip_tls_verify:
    description:
      - Skip TLS certificate verification, for consoles using the default self-signed certificate.
      - Can also be set with the E(UNIFI_NETWORK_SKIP_TLS_VERIFY) environment variable.
    required: false
    default: false
    aliases: ['skip_tls_verify']
    type: bool
  unifi_network_api_path:
    description:
      - Path of the Network Integration API below O(unifi_network_url).
      - To go through the UniFi cloud connector, set O(unifi_network_url=https://api.ui.com) and this to
        V(/v1/connector/consoles/<console id>/proxy/network/integration).
      - Can also be set with the E(UNIFI_NETWORK_API_PATH) environment variable.
    required: false
    default: /proxy/network/integrations
    aliases: ['api_path']
    type: str
  unifi_network_timeout:
    description:
      - Timeout in seconds for each API request.
      - Can also be set with the E(UNIFI_NETWORK_TIMEOUT) environment variable.
    required: false
    default: 30
    aliases: ['request_timeout']
    type: int
"""
