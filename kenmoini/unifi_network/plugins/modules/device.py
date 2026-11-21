#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: device
short_description: Adopt or remove UniFi devices
version_added: "2.0.0"
description:
  - Adopts a device that is pending adoption into a site, or removes (unadopts) an adopted device.
  - The device is identified by its MAC address. Adoption is skipped when the device is already adopted.
  - "B(Warning:) removing an online device with O(state=absent) resets it to factory defaults."
options:
  mac_address:
    description:
      - MAC address of the device.
    type: str
    required: true
    aliases: [mac]
  id:
    description:
      - UUID of the adopted device. Not needed, because the device is found by O(mac_address); when set, it must belong to that MAC address.
    type: str
  state:
    description:
      - V(present) adopts the device, V(absent) removes it from the site (and factory-resets it if it is online).
    type: str
    choices: [present, absent]
    default: present
  ignore_device_limit:
    description:
      - Adopt the device even if the site's device limit is reached.
    type: bool
    default: false
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Find devices waiting to be adopted
  kenmoini.unifi_network.pending_device_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
  register: r_pending

- name: Adopt every pending device
  kenmoini.unifi_network.device:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    mac_address: "{{ item.macAddress }}"
  loop: "{{ r_pending.pending_devices }}"

- name: Remove a decommissioned access point (factory-resets it if online)
  kenmoini.unifi_network.device:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    mac_address: f4:e2:c6:01:02:03
    state: absent
'''

RETURN = r'''
device:
  description:
    - The adopted device as returned by the API, or the pending device in check mode.
    - Empty when O(state=absent).
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "macAddress": "f4:e2:c6:01:02:03", "name": "U7 Pro", "model": "U7PRO",
           "state": "ADOPTING"}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.filters import render_condition
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.references import MAC_RE
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import StateResource, run_state_module


class Device(StateResource):
    path = 'devices'
    result_key = 'device'
    label = 'device'

    @property
    def mac(self):
        mac = self.params['mac_address']
        if not MAC_RE.match(mac):
            raise UnifiNetworkError('%r is not a valid MAC address' % mac)
        return mac.lower().replace('-', ':')

    def lookup_filter(self):
        return render_condition({'property': 'macAddress', 'function': 'eq', 'value': self.mac})

    def lookup_match(self, item):
        return (item.get('macAddress') or '').lower() == self.mac

    def lookup_description(self):
        return 'with MAC address %s' % self.mac

    def find(self):
        current = super(Device, self).find()
        if current is not None and self.params.get('id') and not self.lookup_match(current):
            raise UnifiNetworkError('Device %s has MAC address %s, which does not match mac_address %s' % (
                self.params['id'], current.get('macAddress'), self.mac))
        return current

    def to_api(self, current):
        return {}

    def ensure_present(self, current):
        if current is not None:
            return self.finish(False, current, current)
        pending = [d for d in self.client.paginate('/v1/pending-devices', filter_expr=self.lookup_filter())
                   if self.lookup_match(d)]
        if not pending:
            raise UnifiNetworkError('Device %s is not adopted and not pending adoption' % self.mac)
        if self.module.check_mode:
            return self.finish(True, None, pending[0])
        adopted = self.client.post(self.collection_path, {
            'macAddress': self.mac, 'ignoreDeviceLimit': self.params['ignore_device_limit']})
        return self.finish(True, None, adopted)


def main():
    spec = state_argument_spec()
    spec.update(
        mac_address=dict(type='str', required=True, aliases=['mac']),
        ignore_device_limit=dict(type='bool', default=False),
    )
    run_state_module(Device, spec)


if __name__ == '__main__':
    main()
