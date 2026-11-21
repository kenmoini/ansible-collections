#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: acl_rule
short_description: Manage switch ACL rules in UniFi Network
version_added: "2.0.0"
description:
  - Creates, updates or deletes ACL rules, which UniFi switches enforce to allow or block traffic between hosts
    in the same Layer 2 domain.
  - V(ipv4) rules match IPv4 addresses, subnets, Networks and ports; V(mac) rules match MAC addresses within one Network.
  - The rule is found by O(name), or by O(id) when given (which also allows renaming it).
  - Only the options you set are managed; the module reads the rule first and only writes when something differs.
  - Rule priority is not set here; use M(kenmoini.unifi_network.acl_rule_ordering).
  - Derived rules (created by the UniFi application from other settings) are read-only.
options:
  name:
    description:
      - Name of the ACL rule. Used to find the rule when O(id) is not set.
      - Required unless O(id) is set.
    type: str
  id:
    description:
      - UUID of an existing rule to manage. When set, O(name) renames the rule.
    type: str
  state:
    description:
      - V(present) creates or updates the rule, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  type:
    description:
      - What the rule matches. Required when creating a rule.
    type: str
    choices: [ipv4, mac]
  action:
    description:
      - Whether matching traffic is allowed or blocked. Required when creating a rule.
    type: str
    choices: [allow, block]
  enabled:
    description:
      - Whether the rule is active. New rules are enabled unless this is V(false).
    type: bool
  description:
    description:
      - Free-text description. An empty string removes it.
    type: str
  enforcing_devices:
    description:
      - Switches that enforce the rule, given as names, MAC addresses or UUIDs.
      - An empty list enforces the rule on every capable switch.
    type: list
    elements: str
  protocols:
    description:
      - Protocols the rule applies to. Only for V(ipv4) rules.
      - An empty list applies the rule to all protocols.
    type: list
    elements: str
    choices: [tcp, udp]
  network:
    description:
      - The Network the rule applies to, given as its name or UUID. Only for V(mac) rules, and required when creating one.
    type: str
    aliases: [network_id]
  source:
    description:
      - Which traffic sources the rule matches. Set exactly one kind of criterion; the filter type follows from it.
      - "For V(ipv4) rules: O(source.ip_addresses) or O(source.networks), optionally with O(source.ports),
        or O(source.ports) alone."
      - "For V(mac) rules: O(source.mac_addresses), optionally with O(source.prefix_length)."
      - The filter is replaced as a whole, so criteria you leave out (for example O(source.ports)) are removed.
      - An empty dict (V({})) matches any source.
    type: dict
    suboptions: &endpoint
      ip_addresses:
        description:
          - IPv4 addresses or subnets in CIDR notation. Only for V(ipv4) rules.
        type: list
        elements: str
        aliases: [ip_addresses_or_subnets]
      networks:
        description:
          - Networks, given as names or UUIDs. Only for V(ipv4) rules.
        type: list
        elements: str
        aliases: [network_ids]
      ports:
        description:
          - Port numbers. Only for V(ipv4) rules.
        type: list
        elements: int
      mac_addresses:
        description:
          - MAC addresses. Only for V(mac) rules.
        type: list
        elements: str
      prefix_length:
        description:
          - Match only the first N bits (1 to 48) of the MAC addresses, to match a vendor prefix. Only for V(mac) rules.
        type: int
  destination:
    description:
      - Which traffic destinations the rule matches. Same structure as O(source).
      - An empty dict (V({})) matches any destination.
    type: dict
    suboptions: *endpoint
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Block IoT devices from reaching the NAS over SMB
  kenmoini.unifi_network.acl_rule:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Block IoT to NAS
    type: ipv4
    action: block
    protocols: [tcp]
    source:
      networks: [IoT]
    destination:
      ip_addresses: [192.168.1.20]
      ports: [139, 445]

- name: Only enforce on the core switch
  kenmoini.unifi_network.acl_rule:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Block IoT to NAS
    enforcing_devices: [Core Switch]

- name: Block a vendor's devices by MAC prefix on the LAN
  kenmoini.unifi_network.acl_rule:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Block cheap cameras
    type: mac
    action: block
    network: LAN
    source:
      mac_addresses: ["a4:da:32:00:00:00"]
      prefix_length: 24

- name: Disable a rule without deleting it
  kenmoini.unifi_network.acl_rule:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Block IoT to NAS
    enabled: false

- name: Delete a rule
  kenmoini.unifi_network.acl_rule:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Block cheap cameras
    state: absent
'''

RETURN = r'''
acl_rule:
  description:
    - The ACL rule as returned by the API after the change, or the predicted rule in check mode.
    - Empty when O(state=absent).
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "name": "Block IoT to NAS", "type": "IPV4", "action": "BLOCK",
           "enabled": true, "index": 3, "protocolFilter": ["TCP"],
           "sourceFilter": {"type": "NETWORKS", "networkIds": ["7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11"]},
           "destinationFilter": {"type": "IP_ADDRESSES_OR_SUBNETS", "ipAddressesOrSubnets": ["192.168.1.20"], "portFilter": [139, 445]},
           "metadata": {"origin": "USER_DEFINED"}}
'''

import ipaddress

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.convert import upper
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import (
    StateResource,
    origin_of,
    run_state_module,
)

IPV4_ENDPOINT_KEYS = ('ip_addresses', 'networks', 'ports')
MAC_ENDPOINT_KEYS = ('mac_addresses', 'prefix_length')


def canonical_ipv4(value):
    text = str(value).strip()
    try:
        if '/' in text:
            return str(ipaddress.IPv4Network(text, strict=False))
        return str(ipaddress.IPv4Address(text))
    except ValueError:
        raise UnifiNetworkError('%r is not a valid IPv4 address or subnet' % (value,))


class AclRule(StateResource):
    path = 'acl-rules'
    result_key = 'acl_rule'
    label = 'ACL rule'
    read_only_keys = ('id', 'metadata', 'index')

    def create_defaults(self):
        return {'enabled': True}

    def required_for_create(self, payload):
        required = {'name': 'name', 'type': 'type', 'action': 'action'}
        if payload.get('type') == 'MAC':
            required['networkIdFilter'] = 'network'
        return required

    def check_scope(self, rule_type):
        p = self.params
        wrong = []
        if rule_type == 'mac':
            wrong += [o for o in ('protocols',) if p[o] is not None]
        else:
            wrong += [o for o in ('network',) if p[o] is not None]
        for side in ('source', 'destination'):
            endpoint = p[side] or {}
            other = MAC_ENDPOINT_KEYS if rule_type == 'ipv4' else IPV4_ENDPOINT_KEYS
            wrong += ['%s.%s' % (side, k) for k in other if endpoint.get(k) is not None]
        if wrong:
            raise UnifiNetworkError('Option(s) %s are not valid for %s rules; %s' % (
                ', '.join(wrong), rule_type, 'use type mac' if rule_type == 'ipv4' else 'use type ipv4'))

    def endpoint(self, endpoint, rule_type, side):
        """Build an ACL endpoint filter, or None for "any"."""
        # The endpoint is rebuilt whole: criteria left out are removed (None), and empty lists mean "not set".
        if rule_type == 'mac':
            if not endpoint.get('mac_addresses'):
                return None
            return {'type': 'MAC_ADDRESSES', 'macAddresses': [m.lower() for m in endpoint['mac_addresses']],
                    'prefixLength': endpoint.get('prefix_length')}
        if endpoint.get('ip_addresses') is not None and endpoint.get('networks') is not None:
            raise UnifiNetworkError('Set only one of %s.ip_addresses and %s.networks' % (side, side))
        result = {}
        if endpoint.get('ip_addresses') is not None:
            result = {'type': 'IP_ADDRESSES_OR_SUBNETS',
                      'ipAddressesOrSubnets': [canonical_ipv4(a) for a in endpoint['ip_addresses']]}
        elif endpoint.get('networks') is not None:
            result = {'type': 'NETWORKS', 'networkIds': self.refs.resolve_many('network', endpoint['networks'])}
        if endpoint.get('ports'):
            bad = [port for port in endpoint['ports'] if not 1 <= port <= 65535]
            if bad:
                raise UnifiNetworkError('%s.ports must be between 1 and 65535, got %s' % (side, bad))
            result.setdefault('type', 'PORTS')
            result['portFilter'] = endpoint['ports']
        elif result:
            result['portFilter'] = None
        return result or None

    def to_api(self, current):
        p = self.params
        rule_type = p['type'] or ((current or {}).get('type') or '').lower()
        if rule_type:
            self.check_scope(rule_type)
        desired = {}
        for opt, key in (('name', 'name'), ('enabled', 'enabled')):
            if p[opt] is not None:
                desired[key] = p[opt]
        for opt, key in (('type', 'type'), ('action', 'action')):
            if p[opt] is not None:
                desired[key] = upper(p[opt])
        if p['description'] is not None:
            desired['description'] = p['description'] or None
        if p['enforcing_devices'] is not None:
            devices = self.refs.resolve_many('device', p['enforcing_devices'])
            desired['enforcingDeviceFilter'] = {'type': 'DEVICES', 'deviceIds': devices} if devices else None
        if p['protocols'] is not None:
            desired['protocolFilter'] = [upper(x) for x in p['protocols']] or None
        if p['network'] is not None:
            desired['networkIdFilter'] = self.refs.resolve('network', p['network'])
        for side, key in (('source', 'sourceFilter'), ('destination', 'destinationFilter')):
            if p[side] is not None:
                if not rule_type:
                    raise UnifiNetworkError('Set type so the %s filter can be built' % side)
                desired[key] = self.endpoint(p[side], rule_type, side)
        return desired

    def check_updatable(self, current, desired):
        if origin_of(current) == 'DERIVED':
            raise UnifiNetworkError('The ACL rule %r is derived from other settings and is read-only' % current.get('name'))

    def check_deletable(self, current):
        self.check_updatable(current, None)


def main():
    endpoint_spec = dict(
        ip_addresses=dict(type='list', elements='str', aliases=['ip_addresses_or_subnets']),
        networks=dict(type='list', elements='str', aliases=['network_ids']),
        ports=dict(type='list', elements='int'),
        mac_addresses=dict(type='list', elements='str'),
        prefix_length=dict(type='int'),
    )
    spec = state_argument_spec()
    spec.update(
        name=dict(type='str'),
        type=dict(type='str', choices=['ipv4', 'mac']),
        action=dict(type='str', choices=['allow', 'block']),
        enabled=dict(type='bool'),
        description=dict(type='str'),
        enforcing_devices=dict(type='list', elements='str'),
        protocols=dict(type='list', elements='str', choices=['tcp', 'udp']),
        network=dict(type='str', aliases=['network_id']),
        source=dict(type='dict', options=endpoint_spec),
        destination=dict(type='dict', options=endpoint_spec),
    )
    run_state_module(AclRule, spec, required_one_of=[('name', 'id')])


if __name__ == '__main__':
    main()
