#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: network
short_description: Manage Networks (VLANs) in UniFi Network
version_added: "1.0.0"
description:
  - Creates, updates or deletes Networks (VLANs) together with their IPv4, DHCP, NAT and IPv6 settings.
  - The Network is found by O(name), or by O(id) when given (which also allows renaming it).
  - Only the options you set are managed. The module reads the Network first, merges your options into it
    and only writes when something differs, so unrelated settings made in the UniFi UI are kept.
  - "Which options apply depends on O(management): V(gateway) networks are routed by the UniFi gateway,
    V(switch) networks by a Layer 3 switch (O(device)), and V(unmanaged) networks are only a VLAN tag."
options:
  name:
    description:
      - Name of the Network. Used to find the Network when O(id) is not set.
      - Required unless O(id) is set.
    type: str
  id:
    description:
      - UUID of an existing Network to manage. When set, O(name) renames the Network.
    type: str
  state:
    description:
      - V(present) creates or updates the Network, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  force:
    description:
      - With O(state=absent), delete the Network even if other resources (WiFi broadcasts, clients...) still reference it.
      - Use M(kenmoini.unifi_network.network_references_info) to see what references a Network.
    type: bool
    default: false
  management:
    description:
      - Who routes the Network. Required when creating a Network.
    type: str
    choices: [gateway, switch, unmanaged]
  vlan_id:
    description:
      - VLAN ID, 2 to 4009 (V(1) is reserved for the default Network). Required when creating a Network.
    type: int
  enabled:
    description:
      - Whether the Network is enabled. New Networks are enabled unless this is V(false).
    type: bool
  zone:
    description:
      - Firewall zone of the Network, given as its name or UUID. Only for V(gateway) networks.
    type: str
    aliases: [zone_id]
  device:
    description:
      - The Layer 3 switch that routes the Network, given as its name, MAC address or UUID. Only for V(switch) networks.
    type: str
    aliases: [device_id]
  isolation_enabled:
    description:
      - Isolate the Network from all other Networks. Only for V(gateway) and V(switch) networks.
    type: bool
  internet_access_enabled:
    description:
      - Allow devices on the Network to reach the internet. Only for V(gateway) networks.
    type: bool
  mdns_forwarding_enabled:
    description:
      - Forward mDNS traffic to and from this Network. Only for V(gateway) networks.
    type: bool
  cellular_backup_enabled:
    description:
      - Allow the Network to use cellular backup when the WAN is down. Only for V(gateway) and V(switch) networks.
    type: bool
  dhcp_guarding:
    description:
      - DHCP guarding, which only allows DHCP offers from trusted servers.
    type: dict
    suboptions:
      enabled:
        description:
          - V(false) disables DHCP guarding.
        type: bool
        default: true
      trusted_dhcp_servers:
        description:
          - IP addresses of the DHCP servers allowed on the Network. Required to turn DHCP guarding on.
        type: list
        elements: str
        aliases: [trusted_dhcp_server_ip_addresses]
  ipv4:
    description:
      - IPv4 settings. Only for V(gateway) and V(switch) networks.
    type: dict
    suboptions:
      host_ip_address:
        description:
          - The router address of the Network, for example V(10.30.0.1).
        type: str
      prefix_length:
        description:
          - Prefix length of the subnet, 8 to 30.
        type: int
      auto_scale_enabled:
        description:
          - Let the subnet grow automatically with the number of DHCP leases. Defaults to V(false) when IPv4 is first configured.
        type: bool
      additional_host_ip_subnets:
        description:
          - Additional host subnets on the VLAN, in CIDR notation.
        type: list
        elements: str
      dhcp:
        description:
          - DHCP settings. Only the suboptions you set are changed.
        type: dict
        suboptions:
          mode:
            description:
              - V(server) runs a DHCP server, V(relay) forwards requests to O(ipv4.dhcp.relay_servers), V(none) turns DHCP off.
              - Defaults to V(server) when DHCP is first configured. Changing the mode replaces the previous mode's settings.
            type: str
            choices: [server, relay, none]
          ip_address_range:
            description:
              - The address pool handed out by the DHCP server.
            type: dict
            suboptions:
              start:
                description: First address of the pool.
                type: str
                required: true
              stop:
                description: Last address of the pool.
                type: str
                required: true
          lease_time_seconds:
            description: Lease time in seconds.
            type: int
          dns_servers:
            description:
              - DNS servers given to clients, in order. When unset the gateway picks them.
            type: list
            elements: str
            aliases: [dns_server_ip_addresses_override]
          domain_name:
            description: Domain name given to clients.
            type: str
          gateway_ip_address_override:
            description: Gateway address given to clients instead of the Network's router address.
            type: str
            aliases: [gateway]
          relay_servers:
            description: DHCP servers that requests are relayed to. Only for O(ipv4.dhcp.mode=relay).
            type: list
            elements: str
            aliases: [dhcp_server_ip_addresses]
          ntp_servers:
            description: NTP servers given to clients (up to two). Only for V(gateway) networks.
            type: list
            elements: str
            aliases: [ntp_server_ip_addresses]
          wins_servers:
            description: WINS servers given to clients (up to two). Only for V(gateway) networks.
            type: list
            elements: str
            aliases: [wins_server_ip_addresses]
          option43_value:
            description: Value of DHCP option 43; it must be the UniFi Network application host IP. Only for V(gateway) networks.
            type: str
          ping_conflict_detection_enabled:
            description: Ping an address before leasing it. Only for V(gateway) networks.
            type: bool
          pxe:
            description: Network boot (PXE) settings. Only for V(gateway) networks.
            type: dict
            suboptions:
              filename:
                description: Boot file name.
                type: str
                required: true
              server_ip_address:
                description: Address of the boot server.
                type: str
                required: true
          tftp_server_address:
            description: TFTP server (hostname, URL or IP). Only for V(gateway) networks.
            type: str
          time_offset_seconds:
            description: Time offset from UTC in seconds. Only for V(gateway) networks.
            type: int
          wpad_url:
            description: Web Proxy Auto-Discovery URL. Only for V(gateway) networks.
            type: str
      nat_outbound:
        description:
          - Which WAN addresses traffic from this Network is translated to. The list is authoritative. Only for V(gateway) networks.
        type: list
        elements: dict
        suboptions:
          wan_interface:
            description: The WAN interface, given as its name or UUID.
            type: str
            required: true
          type:
            description:
              - V(auto) picks addresses automatically, V(static) uses O(ipv4.nat_outbound[].ip_address_selectors).
            type: str
            required: true
            choices: [auto, static]
          ip_address_selection_mode:
            description: For V(auto), use only the main WAN address or all of them.
            type: str
            choices: [main, all]
          ip_address_selectors:
            description:
              - For V(static), the WAN addresses to use, as addresses (V(203.0.113.5)) or inclusive ranges (V(203.0.113.10-203.0.113.12)).
            type: list
            elements: str
  ipv6:
    description:
      - IPv6 settings. Only for V(gateway) networks.
    type: dict
    suboptions:
      enabled:
        description:
          - V(false) removes the IPv6 configuration from the Network.
        type: bool
        default: true
      interface_type:
        description:
          - V(prefix_delegation) takes a prefix from a WAN, V(static) uses O(ipv6.host_ip_address).
          - Required when IPv6 is first configured.
        type: str
        choices: [prefix_delegation, static]
      prefix_delegation_wan_interface:
        description: The WAN interface that delegates the prefix, given as its name or UUID.
        type: str
      host_ip_address:
        description: Static IPv6 router address of the Network.
        type: str
      prefix_length:
        description: Static prefix length, 64 to 127.
        type: int
      additional_host_ip_subnets:
        description: Additional IPv6 host subnets (up to four).
        type: list
        elements: str
      dns_servers:
        description: IPv6 DNS servers given to clients (up to four).
        type: list
        elements: str
        aliases: [dns_server_ip_addresses_override]
      slaac_enabled:
        description: Let clients configure addresses with SLAAC. Either SLAAC or O(ipv6.dhcp) must be active.
        type: bool
      dhcp:
        description: DHCPv6 address pool.
        type: dict
        suboptions:
          enabled:
            description: V(false) turns DHCPv6 off.
            type: bool
            default: true
          suffix_start:
            description: First address suffix of the pool, for example V(::2).
            type: str
          suffix_stop:
            description: Last address suffix of the pool, for example V(::7d1).
            type: str
          lease_time_seconds:
            description: Lease time in seconds.
            type: int
      router_advertisement_priority:
        description:
          - Router advertisement priority, or V(disabled) to stop sending router advertisements.
        type: str
        choices: [low, medium, high, disabled]
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: IoT VLAN routed by the gateway, with DHCP
  kenmoini.unifi_network.network:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: IoT
    management: gateway
    vlan_id: 30
    zone: Internal
    isolation_enabled: true
    ipv4:
      host_ip_address: 10.30.0.1
      prefix_length: 24
      dhcp:
        mode: server
        ip_address_range:
          start: 10.30.0.100
          stop: 10.30.0.200
        lease_time_seconds: 86400
        dns_servers: [10.30.0.1, 1.1.1.1]

- name: Change only the lease time; every other setting is kept
  kenmoini.unifi_network.network:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: IoT
    ipv4:
      dhcp:
        lease_time_seconds: 3600

- name: Relay DHCP to a central server and enable DHCP guarding
  kenmoini.unifi_network.network:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Servers
    management: gateway
    vlan_id: 20
    ipv4:
      host_ip_address: 10.20.0.1
      prefix_length: 24
      dhcp:
        mode: relay
        relay_servers: [10.0.0.5]
    dhcp_guarding:
      trusted_dhcp_servers: [10.0.0.5]

- name: Dual-stack network using prefix delegation from the first WAN
  kenmoini.unifi_network.network:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Home
    ipv6:
      interface_type: prefix_delegation
      prefix_delegation_wan_interface: Internet 1
      slaac_enabled: true
      router_advertisement_priority: high

- name: Network routed by a Layer 3 switch
  kenmoini.unifi_network.network:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Lab
    management: switch
    vlan_id: 50
    device: USW Pro Max 24 PoE
    ipv4:
      host_ip_address: 10.50.0.1
      prefix_length: 24

- name: Preview a change (run with --check --diff)
  kenmoini.unifi_network.network:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: IoT
    vlan_id: 31
  check_mode: true
  diff: true

- name: Delete a Network even if WiFi broadcasts still use it
  kenmoini.unifi_network.network:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Lab
    state: absent
    force: true
'''

RETURN = r'''
network:
  description:
    - The Network as returned by the API after the change, or the predicted Network in check mode.
    - Empty when O(state=absent).
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "name": "IoT", "management": "GATEWAY", "vlanId": 30, "enabled": true,
           "default": false, "zoneId": "7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11", "isolationEnabled": true,
           "ipv4Configuration": {"hostIpAddress": "10.30.0.1", "prefixLength": 24, "autoScaleEnabled": false,
                                 "dhcpConfiguration": {"mode": "SERVER", "ipAddressRange": {"start": "10.30.0.100", "stop": "10.30.0.200"},
                                                       "leaseTimeSeconds": 86400}},
           "metadata": {"origin": "USER_DEFINED"}}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.convert import parse_ip_item, pick, upper
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import StateResource, run_state_module

# Options and the management modes they are valid for.
TOP_LEVEL_SCOPE = {
    'zone': ('gateway',),
    'internet_access_enabled': ('gateway',),
    'mdns_forwarding_enabled': ('gateway',),
    'ipv6': ('gateway',),
    'device': ('switch',),
    'isolation_enabled': ('gateway', 'switch'),
    'cellular_backup_enabled': ('gateway', 'switch'),
    'ipv4': ('gateway', 'switch'),
}
GATEWAY_ONLY_DHCP = ('ntp_servers', 'wins_servers', 'option43_value', 'ping_conflict_detection_enabled', 'pxe',
                     'tftp_server_address', 'time_offset_seconds', 'wpad_url')

DHCP_FIELDS = {
    'lease_time_seconds': 'leaseTimeSeconds', 'dns_servers': 'dnsServerIpAddressesOverride', 'domain_name': 'domainName',
    'gateway_ip_address_override': 'gatewayIpAddressOverride', 'relay_servers': 'dhcpServerIpAddresses',
    'ntp_servers': 'ntpServerIpAddresses', 'wins_servers': 'winsServerIpAddresses', 'option43_value': 'option43Value',
    'ping_conflict_detection_enabled': 'pingConflictDetectionEnabled', 'tftp_server_address': 'tftpServerAddress',
    'time_offset_seconds': 'timeOffsetSeconds', 'wpad_url': 'wpadUrl',
}


def empty_lists_to_none(fragment, keys):
    """An empty list for these keys means "no override": send None so the key is removed."""
    for key in keys:
        if fragment.get(key) == []:
            fragment[key] = None
    return fragment


class Network(StateResource):
    path = 'networks'
    result_key = 'network'
    label = 'network'
    read_only_keys = ('id', 'metadata', 'default')
    create_required = {'management': 'management', 'vlanId': 'vlan_id'}
    supports_force = True

    def create_defaults(self):
        # Fields the API requires on create, with the UniFi UI defaults.
        defaults = {'enabled': True}
        management = self.params['management']
        if management in ('gateway', 'switch'):
            defaults.update(isolationEnabled=False, cellularBackupEnabled=False)
        if management == 'gateway':
            defaults['internetAccessEnabled'] = True
        return defaults

    def required_for_create(self, payload):
        required = dict(self.create_required)
        if payload.get('management') in ('GATEWAY', 'SWITCH'):
            required.update({'ipv4Configuration.hostIpAddress': 'ipv4.host_ip_address',
                             'ipv4Configuration.prefixLength': 'ipv4.prefix_length'})
        if payload.get('management') == 'SWITCH':
            required['deviceId'] = 'device'
        return required

    def check_scope(self, management):
        p = self.params
        for opt, modes in TOP_LEVEL_SCOPE.items():
            if p[opt] is not None and management not in modes:
                raise UnifiNetworkError('Option %s is only valid for %s-managed networks, not %s' % (
                    opt, ' or '.join(modes), management))
        dhcp = (p['ipv4'] or {}).get('dhcp') or {}
        extras = [o for o in GATEWAY_ONLY_DHCP if dhcp.get(o) is not None]
        if p['ipv4'] and p['ipv4'].get('nat_outbound') is not None:
            extras.append('nat_outbound')
        if extras and management != 'gateway':
            raise UnifiNetworkError('Option(s) %s are only valid for gateway-managed networks' % ', '.join(extras))

    def to_api(self, current):
        p = self.params
        current = current or {}
        management = self.management = p['management'] or (current.get('management') or '').lower()
        if management:
            self.check_scope(management)

        desired = pick(p, {
            'name': 'name', 'vlan_id': 'vlanId', 'enabled': 'enabled', 'isolation_enabled': 'isolationEnabled',
            'internet_access_enabled': 'internetAccessEnabled', 'mdns_forwarding_enabled': 'mdnsForwardingEnabled',
            'cellular_backup_enabled': 'cellularBackupEnabled',
        })
        if p['management']:
            desired['management'] = upper(p['management'])
        if p['zone'] is not None:
            desired['zoneId'] = self.refs.resolve('firewall_zone', p['zone'])
        if p['device'] is not None:
            desired['deviceId'] = self.refs.resolve('device', p['device'])
        if p['dhcp_guarding'] is not None:
            self.dhcp_guarding(desired, p['dhcp_guarding'], current)
        if p['ipv4'] is not None:
            desired['ipv4Configuration'] = self.ipv4(p['ipv4'], current.get('ipv4Configuration'))
        if p['ipv6'] is not None:
            ipv6 = self.ipv6(p['ipv6'])
            if ipv6 != {}:
                desired['ipv6Configuration'] = ipv6
        return desired

    def dhcp_guarding(self, desired, guarding, current):
        if not guarding['enabled']:
            desired['dhcpGuarding'] = None
        elif guarding['trusted_dhcp_servers'] == []:
            raise UnifiNetworkError('dhcp_guarding.trusted_dhcp_servers needs at least one server; use enabled=false to turn guarding off')
        elif guarding['trusted_dhcp_servers'] is not None:
            desired['dhcpGuarding'] = {'trustedDhcpServerIpAddresses': guarding['trusted_dhcp_servers']}
        elif not current.get('dhcpGuarding'):
            raise UnifiNetworkError('dhcp_guarding.trusted_dhcp_servers is required to turn DHCP guarding on')

    def ipv4(self, ipv4, current_v4):
        v4 = pick(ipv4, {
            'host_ip_address': 'hostIpAddress', 'prefix_length': 'prefixLength',
            'auto_scale_enabled': 'autoScaleEnabled', 'additional_host_ip_subnets': 'additionalHostIpSubnets',
        })
        if not current_v4 and 'autoScaleEnabled' not in v4:
            v4['autoScaleEnabled'] = False
        dhcp = ipv4.get('dhcp')
        if dhcp is not None:
            if dhcp['mode'] == 'none':
                v4['dhcpConfiguration'] = None
            else:
                v4['dhcpConfiguration'] = self.dhcp(dhcp, ((current_v4 or {}).get('dhcpConfiguration') or {}))
        if ipv4.get('nat_outbound') is not None:
            v4['natOutboundIpAddressConfiguration'] = [self.nat_outbound(n) for n in ipv4['nat_outbound']]
        return empty_lists_to_none(v4, ('additionalHostIpSubnets',))

    def dhcp(self, dhcp, current_dhcp):
        config = empty_lists_to_none(pick(dhcp, DHCP_FIELDS), (
            'dnsServerIpAddressesOverride', 'ntpServerIpAddresses', 'winsServerIpAddresses', 'dhcpServerIpAddresses'))
        if dhcp['ip_address_range']:
            config['ipAddressRange'] = pick(dhcp['ip_address_range'], {'start': 'start', 'stop': 'stop'})
        if dhcp['pxe']:
            config['pxeConfiguration'] = pick(dhcp['pxe'], {'filename': 'filename', 'server_ip_address': 'serverIpAddress'})
        mode = upper(dhcp['mode']) or current_dhcp.get('mode') or 'SERVER'
        config['mode'] = mode
        if mode != current_dhcp.get('mode'):
            # A new DHCP configuration replaces the old one, so it must be complete.
            if mode == 'SERVER':
                if not config.get('ipAddressRange'):
                    raise UnifiNetworkError('ipv4.dhcp.ip_address_range is required to turn on the DHCP server')
                config.setdefault('leaseTimeSeconds', 86400)
                if self.management == 'gateway':
                    config.setdefault('pingConflictDetectionEnabled', False)
            elif mode == 'RELAY' and not config.get('dhcpServerIpAddresses'):
                raise UnifiNetworkError('ipv4.dhcp.relay_servers is required to turn on DHCP relay')
        return config

    def nat_outbound(self, nat):
        entry = {'type': upper(nat['type']), 'wanInterfaceId': self.refs.resolve('wan_interface', nat['wan_interface'])}
        if nat.get('ip_address_selection_mode'):
            entry['ipAddressSelectionMode'] = upper(nat['ip_address_selection_mode'])
        if nat.get('ip_address_selectors') is not None:
            entry['ipAddressSelectors'] = [parse_ip_item(s, 4, allow_subnet=False) for s in nat['ip_address_selectors']]
        return entry

    def ipv6(self, ipv6):
        if not ipv6['enabled']:
            return None
        v6 = empty_lists_to_none(pick(ipv6, {
            'host_ip_address': 'hostIpAddress', 'prefix_length': 'prefixLength',
            'additional_host_ip_subnets': 'additionalHostIpSubnets', 'dns_servers': 'dnsServerIpAddressesOverride',
        }), ('additionalHostIpSubnets', 'dnsServerIpAddressesOverride'))
        if ipv6['interface_type']:
            v6['interfaceType'] = upper(ipv6['interface_type'])
        if ipv6['prefix_delegation_wan_interface'] is not None:
            v6['prefixDelegationWanInterfaceId'] = self.refs.resolve('wan_interface', ipv6['prefix_delegation_wan_interface'])
        assignment = {}
        if ipv6['slaac_enabled'] is not None:
            assignment['slaacEnabled'] = ipv6['slaac_enabled']
        dhcp = ipv6['dhcp']
        if dhcp is not None:
            if not dhcp['enabled']:
                assignment['dhcpConfiguration'] = None
            else:
                config = pick(dhcp, {'lease_time_seconds': 'leaseTimeSeconds'})
                suffix = pick(dhcp, {'suffix_start': 'start', 'suffix_stop': 'stop'})
                if suffix:
                    config['ipAddressSuffixRange'] = suffix
                assignment['dhcpConfiguration'] = config
        if assignment:
            v6['clientAddressAssignment'] = assignment
        priority = ipv6['router_advertisement_priority']
        if priority == 'disabled':
            v6['routerAdvertisement'] = None
        elif priority:
            v6['routerAdvertisement'] = {'priority': upper(priority)}
        return v6


def argument_spec():
    range_spec = dict(start=dict(type='str', required=True), stop=dict(type='str', required=True))
    dhcp_spec = dict(
        mode=dict(type='str', choices=['server', 'relay', 'none']),
        ip_address_range=dict(type='dict', options=range_spec),
        lease_time_seconds=dict(type='int'),
        dns_servers=dict(type='list', elements='str', aliases=['dns_server_ip_addresses_override']),
        domain_name=dict(type='str'),
        gateway_ip_address_override=dict(type='str', aliases=['gateway']),
        relay_servers=dict(type='list', elements='str', aliases=['dhcp_server_ip_addresses']),
        ntp_servers=dict(type='list', elements='str', aliases=['ntp_server_ip_addresses']),
        wins_servers=dict(type='list', elements='str', aliases=['wins_server_ip_addresses']),
        option43_value=dict(type='str'),
        ping_conflict_detection_enabled=dict(type='bool'),
        pxe=dict(type='dict', options=dict(filename=dict(type='str', required=True),
                                           server_ip_address=dict(type='str', required=True))),
        tftp_server_address=dict(type='str'),
        time_offset_seconds=dict(type='int'),
        wpad_url=dict(type='str'),
    )
    nat_spec = dict(
        wan_interface=dict(type='str', required=True),
        type=dict(type='str', required=True, choices=['auto', 'static']),
        ip_address_selection_mode=dict(type='str', choices=['main', 'all']),
        ip_address_selectors=dict(type='list', elements='str'),
    )
    ipv4_spec = dict(
        host_ip_address=dict(type='str'),
        prefix_length=dict(type='int'),
        auto_scale_enabled=dict(type='bool'),
        additional_host_ip_subnets=dict(type='list', elements='str'),
        dhcp=dict(type='dict', options=dhcp_spec),
        nat_outbound=dict(type='list', elements='dict', options=nat_spec),
    )
    ipv6_spec = dict(
        enabled=dict(type='bool', default=True),
        interface_type=dict(type='str', choices=['prefix_delegation', 'static']),
        prefix_delegation_wan_interface=dict(type='str'),
        host_ip_address=dict(type='str'),
        prefix_length=dict(type='int'),
        additional_host_ip_subnets=dict(type='list', elements='str'),
        dns_servers=dict(type='list', elements='str', aliases=['dns_server_ip_addresses_override']),
        slaac_enabled=dict(type='bool'),
        dhcp=dict(type='dict', options=dict(
            enabled=dict(type='bool', default=True),
            suffix_start=dict(type='str'),
            suffix_stop=dict(type='str'),
            lease_time_seconds=dict(type='int'),
        )),
        router_advertisement_priority=dict(type='str', choices=['low', 'medium', 'high', 'disabled']),
    )
    spec = state_argument_spec()
    spec.update(
        name=dict(type='str'),
        force=dict(type='bool', default=False),
        management=dict(type='str', choices=['gateway', 'switch', 'unmanaged']),
        vlan_id=dict(type='int'),
        enabled=dict(type='bool'),
        zone=dict(type='str', aliases=['zone_id']),
        device=dict(type='str', aliases=['device_id']),
        isolation_enabled=dict(type='bool'),
        internet_access_enabled=dict(type='bool'),
        mdns_forwarding_enabled=dict(type='bool'),
        cellular_backup_enabled=dict(type='bool'),
        dhcp_guarding=dict(type='dict', options=dict(
            enabled=dict(type='bool', default=True),
            trusted_dhcp_servers=dict(type='list', elements='str', aliases=['trusted_dhcp_server_ip_addresses']),
        )),
        ipv4=dict(type='dict', options=ipv4_spec),
        ipv6=dict(type='dict', options=ipv6_spec),
    )
    return spec


def main():
    run_state_module(Network, argument_spec(), required_one_of=[('name', 'id')])


if __name__ == '__main__':
    main()
