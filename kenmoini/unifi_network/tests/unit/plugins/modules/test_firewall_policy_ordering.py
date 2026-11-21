# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import firewall_policy_ordering
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import SITE_ID, FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module

ORDERING_PATH = '/v1/sites/%s/firewall/policies/ordering' % SITE_ID


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.internal = f.add_site('firewall/zones', {'name': 'Internal', 'networkIds': []})
    f.external = f.add_site('firewall/zones', {'name': 'External', 'networkIds': []})
    f.p = {}
    for name in ('A', 'B', 'C', 'D'):
        policy = {'name': name, 'source': {'zoneId': f.internal['id']}, 'destination': {'zoneId': f.external['id']}}
        f.p[name] = f.add_site('firewall/policies', policy)['id']
    # A policy between another zone pair, and a namesake of A there.
    f.p['other'] = f.add_site('firewall/policies', {'name': 'Elsewhere'})['id']
    f.p['A2'] = f.add_site('firewall/policies', {'name': 'A'})['id']
    set_ordering(f, ['A', 'B'], ['C', 'D'])
    return f


def set_ordering(fake, before, after):
    fake.singletons[ORDERING_PATH] = ordering(fake, before, after)


def ordering(fake, before, after):
    return {'orderedFirewallPolicyIds': {'beforeSystemDefined': [fake.p[n] for n in before],
                                         'afterSystemDefined': [fake.p[n] for n in after]}}


def run(monkeypatch, check_mode=False, diff=False, **args):
    args.setdefault('source_zone', 'Internal')
    args.setdefault('destination_zone', 'External')
    return run_module(firewall_policy_ordering.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def test_pin_policy_to_top_of_before_list(fake, monkeypatch):
    result = run(monkeypatch, before_system_defined=['B'])
    assert result['changed'] is True
    put = fake.writes[0]
    assert put.method == 'PUT' and put.path == ORDERING_PATH
    assert put.query == {'sourceFirewallZoneId': fake.internal['id'], 'destinationFirewallZoneId': fake.external['id']}
    assert put.body == ordering(fake, ['B', 'A'], ['C', 'D'])
    assert result['ordering'] == ordering(fake, ['B', 'A'], ['C', 'D'])
    get = [c for c in fake.calls if c.path == ORDERING_PATH][0]
    assert get.method == 'GET' and get.query == put.query


def test_same_order_is_idempotent(fake, monkeypatch):
    result = run(monkeypatch, before_system_defined=['A', 'B'], after_system_defined=['C', 'D'])
    assert result['changed'] is False
    assert fake.writes == []
    assert result['ordering'] == ordering(fake, ['A', 'B'], ['C', 'D'])


def test_partial_list_already_on_top_is_idempotent(fake, monkeypatch):
    assert run(monkeypatch, before_system_defined=['A'])['changed'] is False
    assert run(monkeypatch, after_system_defined=['D'], position='bottom')['changed'] is False
    assert fake.writes == []


def test_position_bottom(fake, monkeypatch):
    run(monkeypatch, before_system_defined=['A'], position='bottom')
    assert fake.writes[0].body == ordering(fake, ['B', 'A'], ['C', 'D'])


def test_moving_policy_to_other_list(fake, monkeypatch):
    run(monkeypatch, after_system_defined=['A'])
    assert fake.writes[0].body == ordering(fake, ['B'], ['A', 'C', 'D'])


def test_both_lists(fake, monkeypatch):
    run(monkeypatch, before_system_defined=['D', 'C'], after_system_defined=['A'], position='bottom')
    assert fake.writes[0].body == ordering(fake, ['B', 'D', 'C'], ['A'])


def test_uuid_references_pass_through(fake, monkeypatch):
    run(monkeypatch, before_system_defined=[fake.p['C']], source_zone=fake.internal['id'],
        destination_zone=fake.external['id'])
    assert fake.writes[0].body == ordering(fake, ['C', 'A', 'B'], ['D'])


def test_namesake_in_other_zone_pair_is_ignored(fake, monkeypatch):
    # Two policies are named 'A'; only one is ordered between Internal and External.
    run(monkeypatch, after_system_defined=['A'], position='bottom')
    assert fake.writes[0].body == ordering(fake, ['B'], ['C', 'D', 'A'])


def test_unknown_policy_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match="No firewall policy named 'Nope'"):
        run(monkeypatch, before_system_defined=['Nope'])
    assert fake.writes == []


def test_policy_from_other_zone_pair_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match="'Elsewhere' is not a user-defined policy from zone 'Internal' to zone 'External'"):
        run(monkeypatch, before_system_defined=['Elsewhere'])
    with pytest.raises(AnsibleFail, match='is not a user-defined policy'):
        run(monkeypatch, before_system_defined=[fake.p['other']])
    assert fake.writes == []


def test_policy_in_both_lists_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match="'A'.*both before_system_defined and after_system_defined"):
        run(monkeypatch, before_system_defined=['A'], after_system_defined=['A'])


def test_duplicate_in_list_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='more than once'):
        run(monkeypatch, before_system_defined=['A', fake.p['A']])


def test_unknown_zone_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match="No firewall zone named 'Nowhere'"):
        run(monkeypatch, source_zone='Nowhere', before_system_defined=['A'])


def test_requires_a_list(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='one of the following is required'):
        run(monkeypatch)


def test_check_mode_and_diff(fake, monkeypatch):
    result = run(monkeypatch, check_mode=True, diff=True, after_system_defined=['B'])
    assert result['changed'] is True
    assert fake.writes == []
    assert result['ordering'] == ordering(fake, ['A'], ['B', 'C', 'D'])
    assert result['diff'] == {'before': ordering(fake, ['A', 'B'], ['C', 'D']),
                              'after': ordering(fake, ['A'], ['B', 'C', 'D'])}


def test_empty_current_ordering(fake, monkeypatch):
    fake.singletons[ORDERING_PATH] = {'orderedFirewallPolicyIds': {'beforeSystemDefined': [], 'afterSystemDefined': []}}
    with pytest.raises(AnsibleFail, match='is not a user-defined policy'):
        run(monkeypatch, before_system_defined=['B'])
