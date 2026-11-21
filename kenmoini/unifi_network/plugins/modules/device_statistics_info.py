#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: device_statistics_info
short_description: Get the latest statistics of an adopted UniFi device
version_added: "1.0.0"
description:
  - Returns the latest real-time statistics (uptime, CPU and memory use, uplink rates, radio stats) of an adopted device.
  - Replaces C(device_statistics), which now redirects to this module.
options:
  device:
    description:
      - The device, given as its UUID, its name or its MAC address.
    required: true
    type: str
    aliases: [device_id, device_uuid, unifi_network_device_id, unifi_network_device_uuid]
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Get statistics for a device by name
  kenmoini.unifi_network.device_statistics_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    device: USW Pro Max 24 PoE
  register: r_stats

- name: Get statistics for a device by MAC address
  kenmoini.unifi_network.device_statistics_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    device: "f4:e2:c6:01:02:03"
  register: r_stats
'''

RETURN = r'''
statistics:
  description: The latest statistics of the device, exactly as returned by the API.
  returned: always
  type: dict
  sample: {"uptimeSec": 86400, "lastHeartbeatAt": "2025-01-01T00:00:00Z", "cpuUtilizationPct": 4.5, "memoryUtilizationPct": 38.2}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import (
    connection_argument_spec,
    site_argument_spec,
)
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_single_info_module


def resolve(module, refs):
    return {'device_id': refs.resolve('device', module.params['device'])}, None


def main():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    spec['device'] = dict(type='str', required=True,
                          aliases=['device_id', 'device_uuid', 'unifi_network_device_id', 'unifi_network_device_uuid'])
    run_single_info_module('devices/{device_id}/statistics/latest', 'statistics', spec, resolve=resolve)


if __name__ == '__main__':
    main()
