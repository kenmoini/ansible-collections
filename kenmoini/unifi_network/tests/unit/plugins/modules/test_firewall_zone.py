# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import firewall_zone
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.iot = f.add_site('networks', {'name': 'IoT'})
    f.cams = f.add_site('networks', {'name': 'Cameras'})
    f.lan = f.add_site('networks', {'name': 'LAN'})
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(firewall_zone.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def test_create_resolves_network_names(fake, monkeypatch):
    result = run(monkeypatch, name='Untrusted', networks=['IoT', fake.cams['id']])
    assert result['changed'] is True
    assert fake.writes[0].body == {'name': 'Untrusted', 'networkIds': [fake.iot['id'], fake.cams['id']]}
    assert result['firewall_zone']['name'] == 'Untrusted'


def test_create_without_networks_sends_empty_list(fake, monkeypatch):
    run(monkeypatch, name='Empty')
    assert fake.writes[0].body == {'name': 'Empty', 'networkIds': []}


def test_rerun_is_idempotent_regardless_of_order(fake, monkeypatch):
    run(monkeypatch, name='Untrusted', networks=['IoT', 'Cameras'])
    assert run(monkeypatch, name='Untrusted', networks=['Cameras', 'IoT'])['changed'] is False
    assert len(fake.writes) == 1


def test_networks_list_is_authoritative(fake, monkeypatch):
    fake.add_site('firewall/zones', {'name': 'Untrusted', 'networkIds': [fake.iot['id'], fake.cams['id']],
                                     'metadata': {'origin': 'USER_DEFINED'}})
    result = run(monkeypatch, name='Untrusted', networks=['IoT'], diff=True)
    assert result['changed'] is True
    assert fake.writes[0].body == {'name': 'Untrusted', 'networkIds': [fake.iot['id']]}
    assert result['diff']['before']['networkIds'] == [fake.iot['id'], fake.cams['id']]


def test_append_adds_without_removing(fake, monkeypatch):
    fake.add_site('firewall/zones', {'name': 'Untrusted', 'networkIds': [fake.iot['id']]})
    result = run(monkeypatch, name='Untrusted', networks=['Cameras'], append=True)
    assert result['changed'] is True
    assert fake.writes[0].body['networkIds'] == [fake.iot['id'], fake.cams['id']]
    assert run(monkeypatch, name='Untrusted', networks=['Cameras'], append=True)['changed'] is False


def test_omitting_networks_leaves_membership_alone(fake, monkeypatch):
    fake.add_site('firewall/zones', {'name': 'Untrusted', 'networkIds': [fake.iot['id']]})
    assert run(monkeypatch, name='Untrusted')['changed'] is False


def test_system_zone_allows_network_changes(fake, monkeypatch):
    fake.add_site('firewall/zones', {'name': 'Internal', 'networkIds': [fake.lan['id']],
                                     'metadata': {'origin': 'SYSTEM_DEFINED'}})
    result = run(monkeypatch, name='Internal', networks=['LAN', 'IoT'])
    assert result['changed'] is True
    assert fake.writes[0].body == {'name': 'Internal', 'networkIds': [fake.lan['id'], fake.iot['id']]}


def test_system_zone_cannot_be_renamed(fake, monkeypatch):
    zone = fake.add_site('firewall/zones', {'name': 'Internal', 'networkIds': [],
                                            'metadata': {'origin': 'SYSTEM_DEFINED'}})
    with pytest.raises(AnsibleFail, match='system-defined'):
        run(monkeypatch, id=zone['id'], name='Renamed')
    assert fake.writes == []


def test_system_zone_cannot_be_deleted(fake, monkeypatch):
    fake.add_site('firewall/zones', {'name': 'Internal', 'networkIds': [], 'metadata': {'origin': 'SYSTEM_DEFINED'}})
    with pytest.raises(AnsibleFail, match='system-defined'):
        run(monkeypatch, name='Internal', state='absent')
    assert fake.writes == []


def test_absent_deletes_custom_zone(fake, monkeypatch):
    fake.add_site('firewall/zones', {'name': 'Untrusted', 'networkIds': []})
    assert run(monkeypatch, name='Untrusted', state='absent')['changed'] is True
    assert fake.writes[0].method == 'DELETE'


def test_unknown_network_fails_before_writing(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match="No network named 'Nope'"):
        run(monkeypatch, name='Untrusted', networks=['Nope'])
    assert fake.writes == []


def test_requires_name_or_id(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='one of the following is required'):
        run(monkeypatch, networks=['IoT'])
