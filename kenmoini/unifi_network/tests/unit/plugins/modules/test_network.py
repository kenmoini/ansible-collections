# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import network
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module

IOT_IPV4 = {
    'host_ip_address': '10.30.0.1',
    'prefix_length': 24,
    'dhcp': {
        'mode': 'server',
        'ip_address_range': {'start': '10.30.0.100', 'stop': '10.30.0.200'},
        'lease_time_seconds': 86400,
        'dns_servers': ['10.30.0.1', '1.1.1.1'],
    },
}

IOT_IPV4_API = {
    'hostIpAddress': '10.30.0.1',
    'prefixLength': 24,
    'autoScaleEnabled': False,
    'dhcpConfiguration': {
        'mode': 'SERVER',
        'ipAddressRange': {'start': '10.30.0.100', 'stop': '10.30.0.200'},
        'leaseTimeSeconds': 86400,
        'dnsServerIpAddressesOverride': ['10.30.0.1', '1.1.1.1'],
    },
}


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.zone = f.add_site('firewall/zones', {'name': 'Internal', 'networkIds': []})
    f.wan = f.add_site('wans', {'name': 'Internet 1'})
    f.switch = f.add_site('devices', {'name': 'Core Switch', 'macAddress': 'aa:bb:cc:00:00:01'})
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(network.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def existing_iot(fake, **overrides):
    obj = {'name': 'IoT', 'management': 'GATEWAY', 'vlanId': 30, 'enabled': True, 'default': False,
           'zoneId': fake.zone['id'], 'ipv4Configuration': copy.deepcopy(IOT_IPV4_API),
           'metadata': {'origin': 'USER_DEFINED'}}
    obj.update(overrides)
    return fake.add_site('networks', obj)


def test_create_gateway_network(fake, monkeypatch):
    result = run(monkeypatch, name='IoT', management='gateway', vlan_id=30, zone='Internal',
                 isolation_enabled=True, ipv4=IOT_IPV4)
    assert result['changed'] is True
    assert fake.writes[0].method == 'POST'
    assert fake.writes[0].body == {
        'name': 'IoT', 'management': 'GATEWAY', 'vlanId': 30, 'enabled': True, 'zoneId': fake.zone['id'],
        'isolationEnabled': True, 'internetAccessEnabled': True, 'cellularBackupEnabled': False,
        'ipv4Configuration': dict(IOT_IPV4_API, dhcpConfiguration=dict(IOT_IPV4_API['dhcpConfiguration'],
                                                                       pingConflictDetectionEnabled=False)),
    }


def test_rerun_is_idempotent(fake, monkeypatch):
    existing_iot(fake)
    result = run(monkeypatch, name='IoT', management='gateway', vlan_id=30, zone='Internal', ipv4=IOT_IPV4)
    assert result['changed'] is False
    assert fake.writes == []


def test_nested_update_keeps_unmanaged_fields(fake, monkeypatch):
    existing_iot(fake)
    result = run(monkeypatch, name='IoT', ipv4={'dhcp': {'lease_time_seconds': 3600}}, diff=True)
    assert result['changed'] is True
    put = fake.writes[0]
    assert put.method == 'PUT'
    dhcp = put.body['ipv4Configuration']['dhcpConfiguration']
    assert dhcp['leaseTimeSeconds'] == 3600
    assert dhcp['ipAddressRange'] == {'start': '10.30.0.100', 'stop': '10.30.0.200'}
    assert put.body['vlanId'] == 30 and put.body['zoneId'] == fake.zone['id']
    assert 'id' not in put.body and 'metadata' not in put.body and 'default' not in put.body
    assert result['diff']['before']['ipv4Configuration']['dhcpConfiguration']['leaseTimeSeconds'] == 86400


def test_dhcp_mode_none_disables_dhcp(fake, monkeypatch):
    existing_iot(fake)
    run(monkeypatch, name='IoT', ipv4={'dhcp': {'mode': 'none'}})
    assert 'dhcpConfiguration' not in fake.writes[0].body['ipv4Configuration']
    assert run(monkeypatch, name='IoT', ipv4={'dhcp': {'mode': 'none'}})['changed'] is False


def test_switching_dhcp_to_relay_replaces_server_settings(fake, monkeypatch):
    existing_iot(fake)
    run(monkeypatch, name='IoT', ipv4={'dhcp': {'mode': 'relay', 'relay_servers': ['10.0.0.5']}})
    assert fake.writes[0].body['ipv4Configuration']['dhcpConfiguration'] == {
        'mode': 'RELAY', 'dhcpServerIpAddresses': ['10.0.0.5']}


def test_dhcp_guarding_enable_and_disable(fake, monkeypatch):
    existing_iot(fake)
    run(monkeypatch, name='IoT', dhcp_guarding={'enabled': True, 'trusted_dhcp_servers': ['10.30.0.1']})
    assert fake.writes[0].body['dhcpGuarding'] == {'trustedDhcpServerIpAddresses': ['10.30.0.1']}
    run(monkeypatch, name='IoT', dhcp_guarding={'enabled': False})
    assert 'dhcpGuarding' not in fake.writes[1].body
    assert run(monkeypatch, name='IoT', dhcp_guarding={'enabled': False})['changed'] is False


def test_dhcp_guarding_enabled_requires_servers_on_create(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='trusted_dhcp_servers'):
        run(monkeypatch, name='X', management='gateway', vlan_id=31, dhcp_guarding={'enabled': True})


def test_pxe_and_gateway_dhcp_extras(fake, monkeypatch):
    existing_iot(fake)
    run(monkeypatch, name='IoT', ipv4={'dhcp': {'pxe': {'filename': 'pxelinux.0', 'server_ip_address': '10.30.0.5'},
                                                'ntp_servers': ['10.30.0.1'], 'domain_name': 'iot.lan'}})
    dhcp = fake.writes[0].body['ipv4Configuration']['dhcpConfiguration']
    assert dhcp['pxeConfiguration'] == {'filename': 'pxelinux.0', 'serverIpAddress': '10.30.0.5'}
    assert dhcp['ntpServerIpAddresses'] == ['10.30.0.1']
    assert dhcp['domainName'] == 'iot.lan'
    assert dhcp['mode'] == 'SERVER'


def test_nat_outbound_resolves_wan_and_selectors(fake, monkeypatch):
    existing_iot(fake)
    run(monkeypatch, name='IoT', ipv4={'nat_outbound': [
        {'wan_interface': 'Internet 1', 'type': 'static', 'ip_address_selectors': ['203.0.113.5', '203.0.113.10-203.0.113.12']},
    ]})
    assert fake.writes[0].body['ipv4Configuration']['natOutboundIpAddressConfiguration'] == [
        {'type': 'STATIC', 'wanInterfaceId': fake.wan['id'], 'ipAddressSelectors': [
            {'type': 'IP_ADDRESS', 'value': '203.0.113.5'},
            {'type': 'IP_ADDRESS_RANGE', 'start': '203.0.113.10', 'stop': '203.0.113.12'}]},
    ]


def test_ipv6_prefix_delegation(fake, monkeypatch):
    existing_iot(fake)
    run(monkeypatch, name='IoT', ipv6={'interface_type': 'prefix_delegation', 'prefix_delegation_wan_interface': 'Internet 1',
                                       'slaac_enabled': True, 'router_advertisement_priority': 'high'})
    assert fake.writes[0].body['ipv6Configuration'] == {
        'interfaceType': 'PREFIX_DELEGATION', 'prefixDelegationWanInterfaceId': fake.wan['id'],
        'clientAddressAssignment': {'slaacEnabled': True}, 'routerAdvertisement': {'priority': 'HIGH'}}


def test_ipv6_disable(fake, monkeypatch):
    existing_iot(fake, ipv6Configuration={'interfaceType': 'STATIC', 'hostIpAddress': '2001:db8::1', 'prefixLength': 64,
                                          'clientAddressAssignment': {'slaacEnabled': True}})
    run(monkeypatch, name='IoT', ipv6={'enabled': False})
    assert 'ipv6Configuration' not in fake.writes[0].body


def test_switch_managed_network_with_device_by_name(fake, monkeypatch):
    run(monkeypatch, name='Lab', management='switch', vlan_id=50, device='Core Switch',
        ipv4={'host_ip_address': '10.50.0.1', 'prefix_length': 24})
    body = fake.writes[0].body
    assert body['management'] == 'SWITCH' and body['deviceId'] == fake.switch['id']


def test_gateway_only_options_rejected_for_switch(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='zone.*gateway'):
        run(monkeypatch, name='Lab', management='switch', vlan_id=50, device='Core Switch', zone='Internal')


def test_create_requires_management_and_vlan(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='requires: management, vlan_id'):
        run(monkeypatch, name='New')


def test_check_mode_create(fake, monkeypatch):
    result = run(monkeypatch, check_mode=True, name='IoT', management='gateway', vlan_id=30,
                 ipv4={'host_ip_address': '10.30.0.1', 'prefix_length': 24})
    assert result['changed'] is True
    assert fake.writes == []
    assert result['network']['vlanId'] == 30


def test_absent_with_force(fake, monkeypatch):
    existing_iot(fake)
    assert run(monkeypatch, name='IoT', state='absent', force=True)['changed'] is True
    assert fake.writes[0].method == 'DELETE' and fake.writes[0].query == {'force': 'true'}


def test_ipv6_enabled_without_settings_is_not_a_change(fake, monkeypatch):
    existing_iot(fake)
    result = run(monkeypatch, name='IoT', ipv6={'enabled': True})
    assert result['changed'] is False
    assert fake.writes == []


def test_create_gateway_requires_ipv4_address(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='requires: ipv4.host_ip_address, ipv4.prefix_length'):
        run(monkeypatch, name='New', management='gateway', vlan_id=33)


def test_create_switch_requires_device(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='requires: device'):
        run(monkeypatch, name='Lab', management='switch', vlan_id=50, ipv4={'host_ip_address': '10.50.0.1', 'prefix_length': 24})


def test_create_switch_sends_required_defaults(fake, monkeypatch):
    run(monkeypatch, name='Lab', management='switch', vlan_id=50, device='Core Switch',
        ipv4={'host_ip_address': '10.50.0.1', 'prefix_length': 24})
    body = fake.writes[0].body
    assert body['isolationEnabled'] is False and body['cellularBackupEnabled'] is False
    assert 'internetAccessEnabled' not in body


def test_create_unmanaged_is_minimal(fake, monkeypatch):
    run(monkeypatch, name='Tagged', management='unmanaged', vlan_id=60)
    assert fake.writes[0].body == {'name': 'Tagged', 'management': 'UNMANAGED', 'vlanId': 60, 'enabled': True}


def test_turning_dhcp_server_on_requires_a_range(fake, monkeypatch):
    existing_iot(fake, ipv4Configuration={'hostIpAddress': '10.30.0.1', 'prefixLength': 24, 'autoScaleEnabled': False,
                                          'dhcpConfiguration': {'mode': 'RELAY', 'dhcpServerIpAddresses': ['10.0.0.5']}})
    with pytest.raises(AnsibleFail, match='ip_address_range'):
        run(monkeypatch, name='IoT', ipv4={'dhcp': {'mode': 'server'}})
    assert fake.writes == []


def test_turning_dhcp_server_on_fills_required_defaults(fake, monkeypatch):
    existing_iot(fake, ipv4Configuration={'hostIpAddress': '10.30.0.1', 'prefixLength': 24, 'autoScaleEnabled': False,
                                          'dhcpConfiguration': {'mode': 'RELAY', 'dhcpServerIpAddresses': ['10.0.0.5']}})
    run(monkeypatch, name='IoT', ipv4={'dhcp': {'mode': 'server', 'ip_address_range': {'start': '10.30.0.10', 'stop': '10.30.0.20'}}})
    assert fake.writes[0].body['ipv4Configuration']['dhcpConfiguration'] == {
        'mode': 'SERVER', 'ipAddressRange': {'start': '10.30.0.10', 'stop': '10.30.0.20'}, 'leaseTimeSeconds': 86400,
        'pingConflictDetectionEnabled': False}


def test_turning_relay_on_requires_servers(fake, monkeypatch):
    existing_iot(fake)
    with pytest.raises(AnsibleFail, match='relay_servers'):
        run(monkeypatch, name='IoT', ipv4={'dhcp': {'mode': 'relay'}})


def test_empty_lists_remove_overrides(fake, monkeypatch):
    existing_iot(fake)
    run(monkeypatch, name='IoT', ipv4={'additional_host_ip_subnets': [], 'dhcp': {'dns_servers': []}})
    v4 = fake.writes[0].body['ipv4Configuration']
    assert 'dnsServerIpAddressesOverride' not in v4['dhcpConfiguration']
    assert 'additionalHostIpSubnets' not in v4
    assert run(monkeypatch, name='IoT', ipv4={'additional_host_ip_subnets': [], 'dhcp': {'dns_servers': []}})['changed'] is False
