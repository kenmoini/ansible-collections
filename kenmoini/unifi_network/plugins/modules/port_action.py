#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: port_action
short_description: Run an action, such as a PoE power cycle, on a port of a UniFi device
version_added: "1.0.0"
description:
  - Runs an action on one port of an adopted device. The only action the API offers today is V(power_cycle),
    which turns PoE off and on again to reboot the powered device.
  - This is an imperative operation, so the module always reports a change.
    In check mode it only verifies that the device and port exist.
options:
  device:
    description:
      - The device, given as its name, MAC address or UUID.
    type: str
    required: true
    aliases: [device_id, device_uuid, unifi_network_device_id, unifi_network_device_uuid]
  port:
    description:
      - The port index, as numbered on the device.
    type: int
    required: true
    aliases: [port_id, port_idx, unifi_network_port_id, unifi_network_device_port_id]
  action:
    description:
      - The action to run.
    type: str
    required: true
    choices: [power_cycle]
    aliases: [port_action]
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.action
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Reboot the camera on port 7 by power cycling PoE
  kenmoini.unifi_network.port_action:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    device: USW Pro Max 24 PoE
    port: 7
    action: power_cycle
'''

RETURN = r'''
port:
  description: The port the action ran on, from the device's interface list before the action.
  returned: always
  type: dict
  sample: {"idx": 7, "state": "UP", "poe": {"enabled": true, "state": "UP"}}
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkClient, UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import connection_argument_spec, site_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import fail_from_exception, resolve_site


def main():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    spec.update(
        device=dict(type='str', required=True,
                    aliases=['device_id', 'device_uuid', 'unifi_network_device_id', 'unifi_network_device_uuid']),
        port=dict(type='int', required=True, aliases=['port_id', 'port_idx', 'unifi_network_port_id', 'unifi_network_device_port_id']),
        action=dict(type='str', required=True, choices=['power_cycle'], aliases=['port_action']),
    )
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    p = module.params
    try:
        client = UnifiNetworkClient.from_module(module)
        refs = resolve_site(module, client)
        path = '/v1/sites/%s/devices/%s' % (refs.site_id, refs.resolve('device', p['device']))
        device = client.get(path)
        ports = ((device or {}).get('interfaces') or {}).get('ports') or []
        port = [x for x in ports if x.get('idx') == p['port']]
        if not port:
            raise UnifiNetworkError('Device %r has no port %d' % (p['device'], p['port']))
        if not module.check_mode:
            client.post('%s/interfaces/ports/%d/actions' % (path, p['port']), {'action': p['action'].upper()})
    except UnifiNetworkError as exc:
        fail_from_exception(module, exc)
    module.exit_json(changed=True, port=port[0])


if __name__ == '__main__':
    main()
