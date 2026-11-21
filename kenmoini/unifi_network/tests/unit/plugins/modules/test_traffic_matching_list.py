# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import traffic_matching_list
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module


@pytest.fixture
def fake(monkeypatch):
    return FakeUnifi().install(monkeypatch)


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(traffic_matching_list.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def test_ipv4_items_are_typed_from_their_shape(fake, monkeypatch):
    run(monkeypatch, name='Blocked', type='ipv4_addresses',
        items=['192.168.1.10', '10.0.0.5/24', '172.16.0.1-172.16.0.20'])
    assert fake.writes[0].body == {'name': 'Blocked', 'type': 'IPV4_ADDRESSES', 'items': [
        {'type': 'IP_ADDRESS', 'value': '192.168.1.10'},
        {'type': 'SUBNET', 'value': '10.0.0.0/24'},
        {'type': 'IP_ADDRESS_RANGE', 'start': '172.16.0.1', 'stop': '172.16.0.20'},
    ]}


def test_ipv6_items(fake, monkeypatch):
    run(monkeypatch, name='v6', type='ipv6_addresses', items=['2001:db8::1', '2001:DB8:0:1::/64'])
    assert fake.writes[0].body['items'] == [
        {'type': 'IP_ADDRESS', 'value': '2001:db8::1'},
        {'type': 'SUBNET', 'value': '2001:db8:0:1::/64'},
    ]


def test_port_items_accept_numbers_and_ranges(fake, monkeypatch):
    run(monkeypatch, name='Web', type='ports', items=[443, '80', '8000-8100'])
    assert fake.writes[0].body['items'] == [
        {'type': 'PORT_NUMBER', 'value': 443},
        {'type': 'PORT_NUMBER', 'value': 80},
        {'type': 'PORT_NUMBER_RANGE', 'start': 8000, 'stop': 8100},
    ]


def test_rerun_is_idempotent_in_any_order(fake, monkeypatch):
    run(monkeypatch, name='Web', type='ports', items=[443, 80])
    assert run(monkeypatch, name='Web', type='ports', items=['80', 443])['changed'] is False
    assert len(fake.writes) == 1


def test_update_items_uses_existing_type(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'Web', 'type': 'PORTS',
                                             'items': [{'type': 'PORT_NUMBER', 'value': 80}]})
    result = run(monkeypatch, name='Web', items=[80, 443], diff=True)
    assert result['changed'] is True
    assert fake.writes[0].body == {'name': 'Web', 'type': 'PORTS', 'items': [
        {'type': 'PORT_NUMBER', 'value': 80}, {'type': 'PORT_NUMBER', 'value': 443}]}


def test_invalid_item_for_type_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match="'not-an-ip' is not a valid IPv4"):
        run(monkeypatch, name='Bad', type='ipv4_addresses', items=['not-an-ip'])
    with pytest.raises(AnsibleFail, match='port'):
        run(monkeypatch, name='Bad', type='ports', items=['70000'])
    with pytest.raises(AnsibleFail, match='IPv6'):
        run(monkeypatch, name='Bad', type='ipv6_addresses', items=['10.0.0.1'])
    assert fake.writes == []


def test_create_requires_type_and_items(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='requires: items, type'):
        run(monkeypatch, name='Nothing')


def test_absent(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'Web', 'type': 'PORTS', 'items': []})
    assert run(monkeypatch, name='Web', state='absent')['changed'] is True
    assert run(monkeypatch, name='Web', state='absent')['changed'] is False
