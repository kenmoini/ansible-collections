#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: device_action
short_description: Run an action, such as a restart, on an adopted UniFi device
version_added: "1.0.0"
description:
  - Runs an action on an adopted device. The only action the API offers today is V(restart).
  - This is an imperative operation, so the module always reports a change.
    In check mode it only verifies that the device exists.
options:
  device:
    description:
      - The device, given as its name, MAC address or UUID.
    type: str
    required: true
    aliases: [device_id, device_uuid, unifi_network_device_id, unifi_network_device_uuid]
  action:
    description:
      - The action to run.
    type: str
    required: true
    choices: [restart]
    aliases: [device_action]
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.action
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Restart an access point
  kenmoini.unifi_network.device_action:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    device: Living Room AP
    action: restart
'''

RETURN = r'''
device:
  description: The device the action ran on, as returned by the API before the action.
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "name": "Living Room AP", "macAddress": "f4:e2:c6:01:02:03", "state": "ONLINE"}
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
        action=dict(type='str', required=True, choices=['restart'], aliases=['device_action']),
    )
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    try:
        client = UnifiNetworkClient.from_module(module)
        refs = resolve_site(module, client)
        path = '/v1/sites/%s/devices/%s' % (refs.site_id, refs.resolve('device', module.params['device']))
        device = client.get(path)
        if not module.check_mode:
            client.post(path + '/actions', {'action': module.params['action'].upper()})
    except UnifiNetworkError as exc:
        fail_from_exception(module, exc)
    module.exit_json(changed=True, device=device)


if __name__ == '__main__':
    main()
