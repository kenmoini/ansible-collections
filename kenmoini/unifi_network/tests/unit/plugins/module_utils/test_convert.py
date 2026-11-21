# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.convert import parse_ip_item, parse_port_item, pick


def test_pick_skips_unset_options():
    assert pick({'a': 1, 'b': None, 'c': False}, {'a': 'A', 'b': 'B', 'c': 'C'}) == {'A': 1, 'C': False}
    assert pick(None, {'a': 'A'}) == {}


def test_any_version_accepts_ipv4_and_ipv6():
    assert parse_ip_item('10.0.0.1', None) == {'type': 'IP_ADDRESS', 'value': '10.0.0.1'}
    assert parse_ip_item('2001:DB8::1', None) == {'type': 'IP_ADDRESS', 'value': '2001:db8::1'}
    assert parse_ip_item('2001:db8::/32', None) == {'type': 'SUBNET', 'value': '2001:db8::/32'}
    assert parse_ip_item('10.0.0.1-10.0.0.9', None) == {'type': 'IP_ADDRESS_RANGE', 'start': '10.0.0.1', 'stop': '10.0.0.9'}
    assert parse_ip_item('2001:db8::1-2001:db8::9', None) == {
        'type': 'IP_ADDRESS_RANGE', 'start': '2001:db8::1', 'stop': '2001:db8::9'}


def test_any_version_rejects_garbage_and_mixed_ranges():
    with pytest.raises(UnifiNetworkError, match='not a valid IP'):
        parse_ip_item('nope', None)
    with pytest.raises(UnifiNetworkError):
        parse_ip_item('10.0.0.1-2001:db8::1', None)


def test_port_items():
    assert parse_port_item(22) == {'type': 'PORT_NUMBER', 'value': 22}
    assert parse_port_item('1000-2000') == {'type': 'PORT_NUMBER_RANGE', 'start': 1000, 'stop': 2000}
    with pytest.raises(UnifiNetworkError):
        parse_port_item('2000-1000')
