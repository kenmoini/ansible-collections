# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import functools

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_info_module
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module

networks_main = functools.partial(run_info_module, 'networks', 'networks', id_aliases=['network_id'])
wans_main = functools.partial(run_info_module, 'wans', 'wan_interfaces', id_lookup=None, name_lookup='client', filters=False)
tags_main = functools.partial(run_info_module, 'device-tags', 'device_tags', id_lookup='filter')
countries_main = functools.partial(run_info_module, 'countries', 'countries', site_scoped=False, id_lookup=None)


@pytest.fixture
def fake(monkeypatch):
    return FakeUnifi().install(monkeypatch)


def test_lists_every_page(fake, monkeypatch):
    for i in range(230):
        fake.add_site('networks', {'name': 'net%03d' % i})
    result = run_module(networks_main, {}, monkeypatch)
    assert result['changed'] is False
    assert len(result['networks']) == 230


def test_runs_in_check_mode(fake, monkeypatch):
    fake.add_site('networks', {'name': 'IoT'})
    result = run_module(networks_main, {}, monkeypatch, check_mode=True)
    assert [n['name'] for n in result['networks']] == ['IoT']


def test_limit_caps_results(fake, monkeypatch):
    for i in range(10):
        fake.add_site('networks', {'name': 'net%d' % i})
    assert len(run_module(networks_main, {'limit': 3}, monkeypatch)['networks']) == 3


def test_name_shorthand_filters_server_side(fake, monkeypatch):
    fake.add_site('networks', {'name': 'IoT'})
    fake.add_site('networks', {'name': 'LAN'})
    result = run_module(networks_main, {'name': 'IoT'}, monkeypatch)
    assert [n['name'] for n in result['networks']] == ['IoT']
    assert fake.calls[-1].query['filter'] == "name.eq('IoT')"


def test_structured_filters_dict_and_list(fake, monkeypatch):
    fake.add_site('networks', {'name': 'IoT', 'vlanId': 30, 'enabled': True})
    fake.add_site('networks', {'name': 'Cams', 'vlanId': 40, 'enabled': False})
    one = run_module(networks_main, {'filters': {'property': 'vlanId', 'function': 'eq', 'value': 40}}, monkeypatch)
    assert [n['name'] for n in one['networks']] == ['Cams']
    both = run_module(networks_main, {'filters_match': 'any', 'filters': [
        {'property': 'vlanId', 'function': 'eq', 'value': 30},
        {'property': 'enabled', 'function': 'eq', 'value': False}]}, monkeypatch)
    assert sorted(n['name'] for n in both['networks']) == ['Cams', 'IoT']
    assert fake.calls[-1].query['filter'] == 'or(vlanId.eq(30),enabled.eq(false))'


def test_raw_filter(fake, monkeypatch):
    fake.add_site('networks', {'name': 'IoT'})
    fake.add_site('networks', {'name': 'LAN'})
    result = run_module(networks_main, {'filters_raw': "not(name.eq('IoT'))"}, monkeypatch)
    assert [n['name'] for n in result['networks']] == ['LAN']


def test_invalid_filter_fails_before_calling_api(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='requires a value'):
        run_module(networks_main, {'filters': {'property': 'name', 'function': 'eq'}}, monkeypatch)
    assert not any('networks' in c.path for c in fake.calls)


def test_id_uses_item_endpoint_and_alias(fake, monkeypatch):
    net = fake.add_site('networks', {'name': 'IoT'})
    result = run_module(networks_main, {'network_id': net['id']}, monkeypatch)
    assert result['networks'] == [net]
    assert fake.calls[-1].path.endswith('/networks/' + net['id'])


def test_missing_id_returns_empty_list(fake, monkeypatch):
    result = run_module(networks_main, {'id': '11111111-2222-4333-8444-555555555555'}, monkeypatch)
    assert result['networks'] == []


def test_id_and_name_are_mutually_exclusive(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='mutually exclusive'):
        run_module(networks_main, {'id': 'x', 'name': 'y'}, monkeypatch)


def test_id_filter_lookup_for_endpoints_without_item_route(fake, monkeypatch):
    tag = fake.add_site('device-tags', {'name': 'APs'})
    fake.add_site('device-tags', {'name': 'Switches'})
    result = run_module(tags_main, {'id': tag['id']}, monkeypatch)
    assert result['device_tags'] == [tag]
    assert fake.calls[-1].query['filter'] == "id.eq('%s')" % tag['id']


def test_client_side_name_for_unfilterable_endpoint(fake, monkeypatch):
    fake.add_site('wans', {'name': 'Internet 1'})
    fake.add_site('wans', {'name': 'Internet 2'})
    result = run_module(wans_main, {'name': 'Internet 2'}, monkeypatch)
    assert [w['name'] for w in result['wan_interfaces']] == ['Internet 2']
    assert 'filter' not in fake.calls[-1].query


def test_global_endpoint_needs_no_site(fake, monkeypatch):
    fake.add('/v1/countries', {'code': 'US', 'name': 'United States'})
    result = run_module(countries_main, {}, monkeypatch, site=False)
    assert result['countries'][0]['code'] == 'US'
    assert all('/sites' not in c.path for c in fake.calls)


SECRETS = [('securityConfiguration', 'passphrase'), ('securityConfiguration', 'presharedKeys', '*', 'passphrase')]
wifi_main = functools.partial(run_info_module, 'wifi/broadcasts', 'wifi_broadcasts', secret_paths=SECRETS)


def test_secret_paths_are_masked(fake, monkeypatch):
    wifi = fake.add_site('wifi/broadcasts', {'name': 'Home', 'securityConfiguration': {
        'type': 'WPA2_PERSONAL', 'passphrase': 'hunter22', 'presharedKeys': [{'network': {'type': 'NATIVE'}, 'passphrase': 'p2'}]}})
    for args in ({}, {'id': wifi['id']}):
        result = run_module(wifi_main, args, monkeypatch)
        sec = result['wifi_broadcasts'][0]['securityConfiguration']
        assert 'passphrase' not in sec
        assert sec['presharedKeys'] == [{'network': {'type': 'NATIVE'}}]
