# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkClient, UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.references import ReferenceResolver, is_uuid
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import BASE, SITE_ID, FakeUnifi


@pytest.fixture
def fake(monkeypatch):
    return FakeUnifi().install(monkeypatch)


@pytest.fixture
def refs(fake):
    client = UnifiNetworkClient(url=BASE, api_key='k', api_path='')
    return ReferenceResolver(client, site_id=SITE_ID)


def test_is_uuid():
    assert is_uuid(SITE_ID)
    assert not is_uuid('default')


def test_uuid_passes_through_without_api_calls(fake, refs):
    assert refs.resolve('network', '11111111-2222-4333-8444-555555555555') == '11111111-2222-4333-8444-555555555555'
    assert fake.calls == []


def test_site_resolves_by_internal_reference_or_name(fake, refs):
    assert refs.resolve('site', 'default') == SITE_ID
    assert refs.resolve('site', 'Default') == SITE_ID


def test_name_lookup_uses_server_filter_and_exact_match(fake, refs):
    iot = fake.add_site('networks', {'name': 'IoT'})
    fake.add_site('networks', {'name': 'iot'})  # fake filter is case-insensitive like a lenient server
    assert refs.resolve('network', 'IoT') == iot['id']
    assert fake.calls[0].query['filter'] == "name.eq('IoT')"


def test_lookups_are_cached(fake, refs):
    fake.add_site('firewall/zones', {'name': 'Internal'})
    refs.resolve('firewall_zone', 'Internal')
    refs.resolve('firewall_zone', 'Internal')
    assert len(fake.calls) == 1


def test_missing_reference_fails_with_clear_message(fake, refs):
    with pytest.raises(UnifiNetworkError, match="No network named 'Nope'"):
        refs.resolve('network', 'Nope')


def test_ambiguous_reference_lists_ids(fake, refs):
    a = fake.add_site('acl-rules', {'name': 'dup'})
    b = fake.add_site('acl-rules', {'name': 'dup'})
    with pytest.raises(UnifiNetworkError) as exc:
        refs.resolve('acl_rule', 'dup')
    assert a['id'] in str(exc.value) and b['id'] in str(exc.value)
    assert 'UUID' in str(exc.value)


def test_device_resolves_by_mac(fake, refs):
    dev = fake.add_site('devices', {'name': 'Core Switch', 'macAddress': 'aa:bb:cc:dd:ee:ff'})
    assert refs.resolve('device', 'AA:BB:CC:DD:EE:FF') == dev['id']
    assert fake.calls[0].query['filter'] == "macAddress.eq('aa:bb:cc:dd:ee:ff')"


def test_unfilterable_kind_matches_client_side(fake, refs):
    wan = fake.add_site('wans', {'name': 'Internet 1'})
    fake.add_site('wans', {'name': 'Internet 2'})
    assert refs.resolve('wan_interface', 'Internet 1') == wan['id']
    assert 'filter' not in fake.calls[0].query


def test_resolve_many_preserves_order(fake, refs):
    a = fake.add_site('networks', {'name': 'A'})
    b = fake.add_site('networks', {'name': 'B'})
    assert refs.resolve_many('network', ['B', a['id']]) == [b['id'], a['id']]


def test_resolve_many_none_is_none(refs):
    assert refs.resolve_many('network', None) is None


def test_names_with_quotes_are_matched_client_side(fake, refs):
    net = fake.add_site('networks', {'name': "Ken's LAN"})
    assert refs.resolve('network', "Ken's LAN") == net['id']
    assert 'filter' not in fake.calls[-1].query
