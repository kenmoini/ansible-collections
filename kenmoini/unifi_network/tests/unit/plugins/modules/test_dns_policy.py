# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import dns_policy
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module


@pytest.fixture
def fake(monkeypatch):
    return FakeUnifi().install(monkeypatch)


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(dns_policy.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def test_create_a_record(fake, monkeypatch):
    result = run(monkeypatch, type='a', domain='nas.home.arpa', ipv4_address='10.0.0.20', ttl_seconds=300)
    assert result['changed'] is True
    assert fake.writes[0].body == {'type': 'A_RECORD', 'domain': 'nas.home.arpa', 'ipv4Address': '10.0.0.20',
                                   'ttlSeconds': 300, 'enabled': True}


def test_lookup_is_by_type_and_domain(fake, monkeypatch):
    fake.add_site('dns/policies', {'type': 'TXT_RECORD', 'domain': 'nas.home.arpa', 'text': 'x', 'enabled': True})
    rec = fake.add_site('dns/policies', {'type': 'A_RECORD', 'domain': 'nas.home.arpa', 'ipv4Address': '10.0.0.20',
                                         'enabled': True})
    result = run(monkeypatch, type='a', domain='NAS.home.arpa', ipv4_address='10.0.0.20')
    assert result['changed'] is False
    assert result['dns_policy']['id'] == rec['id']
    lookup = [c for c in fake.calls if c.path.endswith('/dns/policies')][0]
    assert lookup.query['filter'] == "type.eq('A_RECORD')"


def test_update_changes_address(fake, monkeypatch):
    fake.add_site('dns/policies', {'type': 'A_RECORD', 'domain': 'nas.home.arpa', 'ipv4Address': '10.0.0.20',
                                   'ttlSeconds': 300, 'enabled': True, 'metadata': {'origin': 'USER_DEFINED'}})
    result = run(monkeypatch, type='a', domain='nas.home.arpa', ipv4_address='10.0.0.21')
    assert result['changed'] is True
    assert fake.writes[0].body == {'type': 'A_RECORD', 'domain': 'nas.home.arpa', 'ipv4Address': '10.0.0.21',
                                   'ttlSeconds': 300, 'enabled': True}


def test_disable_record(fake, monkeypatch):
    fake.add_site('dns/policies', {'type': 'CNAME_RECORD', 'domain': 'www.home.arpa', 'targetDomain': 'nas.home.arpa',
                                   'enabled': True})
    assert run(monkeypatch, type='cname', domain='www.home.arpa', enabled=False)['changed'] is True
    assert fake.writes[0].body['enabled'] is False


def test_srv_record_fields(fake, monkeypatch):
    run(monkeypatch, type='srv', domain='_sip._tcp.home.arpa', server_domain='pbx.home.arpa', service='_sip',
        protocol='_tcp', port=5060, priority=10, weight=5)
    assert fake.writes[0].body == {'type': 'SRV_RECORD', 'domain': '_sip._tcp.home.arpa', 'serverDomain': 'pbx.home.arpa',
                                   'service': '_sip', 'protocol': '_tcp', 'port': 5060, 'priority': 10, 'weight': 5,
                                   'enabled': True}


def test_forward_domain(fake, monkeypatch):
    run(monkeypatch, type='forward_domain', domain='corp.example.com', ip_address='10.10.0.53')
    assert fake.writes[0].body == {'type': 'FORWARD_DOMAIN', 'domain': 'corp.example.com', 'ipAddress': '10.10.0.53',
                                   'enabled': True}


def test_options_for_other_types_are_rejected(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='text.*not valid for type a'):
        run(monkeypatch, type='a', domain='x.home.arpa', ipv4_address='10.0.0.1', text='nope')


def test_create_requires_type_specific_value(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='requires: ipv4_address'):
        run(monkeypatch, type='a', domain='x.home.arpa')
    with pytest.raises(AnsibleFail, match='requires: mail_server_domain, priority'):
        run(monkeypatch, type='mx', domain='home.arpa')


def test_requires_type_and_domain_without_id(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='type'):
        run(monkeypatch, domain='x.home.arpa', ipv4_address='10.0.0.1')


def test_id_allows_changing_type_without_stale_fields(fake, monkeypatch):
    rec = fake.add_site('dns/policies', {'type': 'A_RECORD', 'domain': 'x.home.arpa', 'ipv4Address': '10.0.0.1',
                                         'ttlSeconds': 60, 'enabled': True})
    run(monkeypatch, id=rec['id'], type='cname', target_domain='nas.home.arpa', ttl_seconds=60)
    assert fake.writes[0].body == {'type': 'CNAME_RECORD', 'domain': 'x.home.arpa', 'targetDomain': 'nas.home.arpa',
                                   'ttlSeconds': 60, 'enabled': True}


def test_absent(fake, monkeypatch):
    fake.add_site('dns/policies', {'type': 'A_RECORD', 'domain': 'x.home.arpa', 'ipv4Address': '10.0.0.1'})
    assert run(monkeypatch, type='a', domain='x.home.arpa', state='absent')['changed'] is True
    assert run(monkeypatch, type='a', domain='x.home.arpa', state='absent')['changed'] is False


def test_check_mode_prediction_drops_fields_the_update_removes(fake, monkeypatch):
    rec = fake.add_site('dns/policies', {'type': 'A_RECORD', 'domain': 'x.home.arpa', 'ipv4Address': '10.0.0.1',
                                         'enabled': True, 'metadata': {'origin': 'USER_DEFINED'}})
    result = run(monkeypatch, id=rec['id'], type='cname', target_domain='nas.home.arpa', ttl_seconds=60, check_mode=True)
    assert fake.writes == []
    assert result['dns_policy'] == {'id': rec['id'], 'metadata': {'origin': 'USER_DEFINED'}, 'type': 'CNAME_RECORD',
                                    'domain': 'x.home.arpa', 'targetDomain': 'nas.home.arpa', 'ttlSeconds': 60,
                                    'enabled': True}


def test_a_aaaa_cname_require_ttl_on_create(fake, monkeypatch):
    for rtype, opts in (('a', {'ipv4_address': '10.0.0.1'}), ('aaaa', {'ipv6_address': '2001:db8::1'}),
                        ('cname', {'target_domain': 'nas.home.arpa'})):
        with pytest.raises(AnsibleFail, match='requires: ttl_seconds'):
            run(monkeypatch, type=rtype, domain='x.home.arpa', **opts)
    assert fake.writes == []


def test_changing_type_requires_the_new_types_fields(fake, monkeypatch):
    rec = fake.add_site('dns/policies', {'type': 'A_RECORD', 'domain': 'x.home.arpa', 'ipv4Address': '10.0.0.1',
                                         'ttlSeconds': 60, 'enabled': True})
    with pytest.raises(AnsibleFail, match='ttl_seconds'):
        run(monkeypatch, id=rec['id'], type='cname', target_domain='nas.home.arpa')
    assert fake.writes == []
