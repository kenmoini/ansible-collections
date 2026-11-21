# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib

import pytest

from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import SITE_ID, FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module

# module name, API collection, result key, site scoped
LIST_MODULES = [
    ('site_info', '/v1/sites', 'sites', False),
    ('country_info', '/v1/countries', 'countries', False),
    ('dpi_application_info', '/v1/dpi/applications', 'dpi_applications', False),
    ('dpi_category_info', '/v1/dpi/categories', 'dpi_categories', False),
    ('pending_device_info', '/v1/pending-devices', 'pending_devices', False),
    ('device_info', 'devices', 'devices', True),
    ('device_tag_info', 'device-tags', 'device_tags', True),
    ('client_info', 'clients', 'clients', True),
    ('network_info', 'networks', 'networks', True),
    ('firewall_zone_info', 'firewall/zones', 'firewall_zones', True),
    ('firewall_policy_info', 'firewall/policies', 'firewall_policies', True),
    ('acl_rule_info', 'acl-rules', 'acl_rules', True),
    ('dns_policy_info', 'dns/policies', 'dns_policies', True),
    ('hotspot_voucher_info', 'hotspot/vouchers', 'hotspot_vouchers', True),
    ('traffic_matching_list_info', 'traffic-matching-lists', 'traffic_matching_lists', True),
    ('wifi_broadcast_info', 'wifi/broadcasts', 'wifi_broadcasts', True),
    ('radius_profile_info', 'radius/profiles', 'radius_profiles', True),
    ('vpn_server_info', 'vpn/servers', 'vpn_servers', True),
    ('site_to_site_tunnel_info', 'vpn/site-to-site-tunnels', 'site_to_site_tunnels', True),
    ('wan_interface_info', 'wans', 'wan_interfaces', True),
    ('lag_info', 'switching/lags', 'lags', True),
    ('mc_lag_domain_info', 'switching/mc-lag-domains', 'mc_lag_domains', True),
    ('switch_stack_info', 'switching/switch-stacks', 'switch_stacks', True),
]


def load(name):
    return importlib.import_module('ansible_collections.kenmoini.unifi_network.plugins.modules.%s' % name)


@pytest.fixture
def fake(monkeypatch):
    return FakeUnifi().install(monkeypatch)


@pytest.mark.parametrize('name,collection,result_key,site_scoped', LIST_MODULES)
def test_list_module_returns_items_in_check_mode(name, collection, result_key, site_scoped, fake, monkeypatch):
    if site_scoped:
        item = fake.add_site(collection, {'name': 'smoke'})
    else:
        item = fake.add(collection, {'name': 'smoke'})
    result = run_module(load(name).main, {}, monkeypatch, check_mode=True, site=site_scoped)
    assert result['changed'] is False
    assert item in result[result_key]


class TestApplicationInfo:
    def test_returns_application_info(self, fake, monkeypatch):
        fake.singletons['/v1/info'] = {'applicationVersion': '11.0.97'}
        result = run_module(load('application_info').main, {}, monkeypatch, check_mode=True, site=False)
        assert result['application'] == {'applicationVersion': '11.0.97'}


class TestDeviceStatisticsInfo:
    def test_resolves_device_by_name(self, fake, monkeypatch):
        dev = fake.add_site('devices', {'name': 'Core Switch', 'macAddress': 'aa:bb:cc:dd:ee:ff'})
        path = '/v1/sites/%s/devices/%s/statistics/latest' % (SITE_ID, dev['id'])
        fake.singletons[path] = {'uptimeSec': 42}
        result = run_module(load('device_statistics_info').main, {'device': 'Core Switch'}, monkeypatch, check_mode=True)
        assert result['statistics'] == {'uptimeSec': 42}

    def test_accepts_legacy_device_id_alias(self, fake, monkeypatch):
        dev = fake.add_site('devices', {'name': 'AP'})
        fake.singletons['/v1/sites/%s/devices/%s/statistics/latest' % (SITE_ID, dev['id'])] = {'uptimeSec': 1}
        result = run_module(load('device_statistics_info').main, {'unifi_network_device_id': dev['id']}, monkeypatch)
        assert result['statistics'] == {'uptimeSec': 1}

    def test_unknown_device_fails(self, fake, monkeypatch):
        with pytest.raises(AnsibleFail, match="No device named 'ghost'"):
            run_module(load('device_statistics_info').main, {'device': 'ghost'}, monkeypatch)


class TestNetworkReferencesInfo:
    def test_resolves_network_by_name(self, fake, monkeypatch):
        net = fake.add_site('networks', {'name': 'IoT'})
        refs = {'referenceResources': [{'resourceType': 'WIFI', 'referenceCount': 1}]}
        fake.singletons['/v1/sites/%s/networks/%s/references' % (SITE_ID, net['id'])] = refs
        result = run_module(load('network_references_info').main, {'network': 'IoT'}, monkeypatch, check_mode=True)
        assert result['network_references'] == refs


class TestAclRuleOrderingInfo:
    def test_returns_ordering(self, fake, monkeypatch):
        fake.singletons['/v1/sites/%s/acl-rules/ordering' % SITE_ID] = {'orderedAclRuleIds': ['a', 'b']}
        result = run_module(load('acl_rule_ordering_info').main, {}, monkeypatch, check_mode=True)
        assert result['ordering'] == {'orderedAclRuleIds': ['a', 'b']}


class TestFirewallPolicyOrderingInfo:
    def test_resolves_zone_names_into_query(self, fake, monkeypatch):
        internal = fake.add_site('firewall/zones', {'name': 'Internal'})
        external = fake.add_site('firewall/zones', {'name': 'External'})
        ordering = {'orderedFirewallPolicyIds': {'beforeSystemDefined': ['p1'], 'afterSystemDefined': []}}
        fake.singletons['/v1/sites/%s/firewall/policies/ordering' % SITE_ID] = ordering
        result = run_module(load('firewall_policy_ordering_info').main,
                            {'source_zone': 'Internal', 'destination_zone': 'External'}, monkeypatch, check_mode=True)
        assert result['ordering'] == ordering
        assert fake.calls[-1].query == {'sourceFirewallZoneId': internal['id'], 'destinationFirewallZoneId': external['id']}


class TestWifiBroadcastInfo:
    def test_passphrases_are_not_returned(self, fake, monkeypatch):
        fake.add_site('wifi/broadcasts', {'name': 'Home', 'securityConfiguration': {
            'type': 'WPA2_PERSONAL', 'passphrase': 'hunter22', 'presharedKeys': [{'passphrase': 'p2', 'network': {'type': 'NATIVE'}}]}})
        result = run_module(load('wifi_broadcast_info').main, {}, monkeypatch)
        assert 'hunter22' not in str(result) and "'p2'" not in str(result)
        assert result['wifi_broadcasts'][0]['securityConfiguration']['presharedKeys'] == [{'network': {'type': 'NATIVE'}}]
