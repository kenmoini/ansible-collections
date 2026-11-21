# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import acl_rule
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.iot = f.add_site('networks', {'name': 'IoT'})
    f.lan = f.add_site('networks', {'name': 'LAN'})
    f.switch = f.add_site('devices', {'name': 'Core Switch', 'macAddress': 'aa:bb:cc:00:00:01'})
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(acl_rule.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def ipv4_rule(fake, **overrides):
    obj = {'name': 'Block IoT to NAS', 'type': 'IPV4', 'action': 'BLOCK', 'enabled': True, 'index': 0,
           'sourceFilter': {'type': 'NETWORKS', 'networkIds': [fake.iot['id']]},
           'destinationFilter': {'type': 'IP_ADDRESSES_OR_SUBNETS', 'ipAddressesOrSubnets': ['10.0.0.20'], 'portFilter': [445]},
           'protocolFilter': ['TCP'], 'metadata': {'origin': 'USER_DEFINED'}}
    obj.update(overrides)
    return fake.add_site('acl-rules', obj)


def test_create_ipv4_rule(fake, monkeypatch):
    result = run(monkeypatch, name='Block IoT to NAS', type='ipv4', action='block',
                 source={'networks': ['IoT']}, destination={'ip_addresses': ['10.0.0.20'], 'ports': [445]},
                 protocols=['tcp'], enforcing_devices=['Core Switch'])
    assert result['changed'] is True
    assert fake.writes[0].body == {
        'name': 'Block IoT to NAS', 'type': 'IPV4', 'action': 'BLOCK', 'enabled': True,
        'sourceFilter': {'type': 'NETWORKS', 'networkIds': [fake.iot['id']]},
        'destinationFilter': {'type': 'IP_ADDRESSES_OR_SUBNETS', 'ipAddressesOrSubnets': ['10.0.0.20'], 'portFilter': [445]},
        'protocolFilter': ['TCP'],
        'enforcingDeviceFilter': {'type': 'DEVICES', 'deviceIds': [fake.switch['id']]},
    }


def test_rerun_is_idempotent(fake, monkeypatch):
    ipv4_rule(fake)
    result = run(monkeypatch, name='Block IoT to NAS', type='ipv4', action='block', source={'networks': ['IoT']},
                 destination={'ip_addresses': ['10.0.0.20'], 'ports': [445]}, protocols=['tcp'])
    assert result['changed'] is False


def test_ports_only_filter(fake, monkeypatch):
    ipv4_rule(fake)
    run(monkeypatch, name='Block IoT to NAS', destination={'ports': [22, 23]})
    assert fake.writes[0].body['destinationFilter'] == {'type': 'PORTS', 'portFilter': [22, 23]}


def test_changing_filter_kind_replaces_it(fake, monkeypatch):
    ipv4_rule(fake)
    run(monkeypatch, name='Block IoT to NAS', source={'ip_addresses': ['10.30.0.0/24']})
    assert fake.writes[0].body['sourceFilter'] == {'type': 'IP_ADDRESSES_OR_SUBNETS', 'ipAddressesOrSubnets': ['10.30.0.0/24']}


def test_empty_filter_means_any(fake, monkeypatch):
    ipv4_rule(fake)
    run(monkeypatch, name='Block IoT to NAS', destination={}, protocols=[])
    body = fake.writes[0].body
    assert 'destinationFilter' not in body and 'protocolFilter' not in body


def test_ip_and_networks_are_mutually_exclusive(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='only one of'):
        run(monkeypatch, name='x', type='ipv4', action='allow', source={'networks': ['IoT'], 'ip_addresses': ['10.0.0.1']})


def test_mac_rule(fake, monkeypatch):
    run(monkeypatch, name='Block printer', type='mac', action='block', network='LAN',
        source={'mac_addresses': ['AA:BB:CC:DD:EE:FF'], 'prefix_length': 24})
    assert fake.writes[0].body == {
        'name': 'Block printer', 'type': 'MAC', 'action': 'BLOCK', 'enabled': True, 'networkIdFilter': fake.lan['id'],
        'sourceFilter': {'type': 'MAC_ADDRESSES', 'macAddresses': ['aa:bb:cc:dd:ee:ff'], 'prefixLength': 24},
    }


def test_mac_rule_requires_network_on_create(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='requires: network'):
        run(monkeypatch, name='Block printer', type='mac', action='block', source={'mac_addresses': ['aa:bb:cc:dd:ee:ff']})


def test_options_for_the_other_type_are_rejected(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='mac_addresses.*mac'):
        run(monkeypatch, name='x', type='ipv4', action='block', source={'mac_addresses': ['aa:bb:cc:dd:ee:ff']})
    with pytest.raises(AnsibleFail, match='protocols.*ipv4'):
        run(monkeypatch, name='x', type='mac', action='block', network='LAN', protocols=['tcp'])


def test_invalid_address_rejected(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='not a valid IPv4'):
        run(monkeypatch, name='x', type='ipv4', action='block', source={'ip_addresses': ['300.1.1.1']})


def test_derived_rule_is_read_only(fake, monkeypatch):
    ipv4_rule(fake, metadata={'origin': 'DERIVED'})
    with pytest.raises(AnsibleFail, match='derived'):
        run(monkeypatch, name='Block IoT to NAS', enabled=False)
    with pytest.raises(AnsibleFail, match='derived'):
        run(monkeypatch, name='Block IoT to NAS', state='absent')
    assert fake.writes == []


def test_absent(fake, monkeypatch):
    ipv4_rule(fake)
    assert run(monkeypatch, name='Block IoT to NAS', state='absent')['changed'] is True
    assert run(monkeypatch, name='Block IoT to NAS', state='absent')['changed'] is False


def test_omitting_ports_removes_them(fake, monkeypatch):
    ipv4_rule(fake)
    result = run(monkeypatch, name='Block IoT to NAS', destination={'ip_addresses': ['10.0.0.20']})
    assert result['changed'] is True
    assert fake.writes[0].body['destinationFilter'] == {'type': 'IP_ADDRESSES_OR_SUBNETS', 'ipAddressesOrSubnets': ['10.0.0.20']}
    assert run(monkeypatch, name='Block IoT to NAS', destination={'ip_addresses': ['10.0.0.20']})['changed'] is False


def test_empty_ports_list_is_not_sent(fake, monkeypatch):
    ipv4_rule(fake)
    run(monkeypatch, name='Block IoT to NAS', destination={'ip_addresses': ['10.0.0.20'], 'ports': []})
    assert 'portFilter' not in fake.writes[0].body['destinationFilter']


def test_omitting_mac_prefix_length_removes_it(fake, monkeypatch):
    fake.add_site('acl-rules', {'name': 'Block printer', 'type': 'MAC', 'action': 'BLOCK', 'enabled': True,
                                'networkIdFilter': fake.lan['id'],
                                'sourceFilter': {'type': 'MAC_ADDRESSES', 'macAddresses': ['aa:bb:cc:dd:ee:ff'], 'prefixLength': 24}})
    run(monkeypatch, name='Block printer', source={'mac_addresses': ['aa:bb:cc:dd:ee:ff']})
    assert fake.writes[0].body['sourceFilter'] == {'type': 'MAC_ADDRESSES', 'macAddresses': ['aa:bb:cc:dd:ee:ff']}
