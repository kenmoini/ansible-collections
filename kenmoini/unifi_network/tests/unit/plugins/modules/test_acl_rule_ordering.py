# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import acl_rule_ordering
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import SITE_ID, FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module

ORDERING = '/v1/sites/%s/acl-rules/ordering' % SITE_ID


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.a = f.add_site('acl-rules', {'name': 'A'})
    f.b = f.add_site('acl-rules', {'name': 'B'})
    f.c = f.add_site('acl-rules', {'name': 'C'})
    f.singletons[ORDERING] = {'orderedAclRuleIds': [f.a['id'], f.b['id'], f.c['id']]}
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(acl_rule_ordering.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def test_listed_rules_move_to_the_top(fake, monkeypatch):
    result = run(monkeypatch, rules=['C'])
    assert result['changed'] is True
    assert fake.writes[0].method == 'PUT'
    assert fake.writes[0].body == {'orderedAclRuleIds': [fake.c['id'], fake.a['id'], fake.b['id']]}
    assert result['ordering'] == fake.writes[0].body


def test_bottom_position(fake, monkeypatch):
    run(monkeypatch, rules=['A'], position='bottom')
    assert fake.writes[0].body == {'orderedAclRuleIds': [fake.b['id'], fake.c['id'], fake.a['id']]}


def test_full_list_in_order(fake, monkeypatch):
    run(monkeypatch, rules=['B', 'C', 'A'])
    assert fake.writes[0].body == {'orderedAclRuleIds': [fake.b['id'], fake.c['id'], fake.a['id']]}


def test_already_ordered_is_a_no_op(fake, monkeypatch):
    result = run(monkeypatch, rules=['A', 'B'])
    assert result['changed'] is False
    assert fake.writes == []


def test_check_mode_and_diff(fake, monkeypatch):
    result = run(monkeypatch, rules=[fake.c['id']], check_mode=True, diff=True)
    assert result['changed'] is True
    assert fake.writes == []
    assert result['diff']['before'] == {'orderedAclRuleIds': [fake.a['id'], fake.b['id'], fake.c['id']]}
    assert result['diff']['after'] == {'orderedAclRuleIds': [fake.c['id'], fake.a['id'], fake.b['id']]}


def test_unknown_rule_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match="No ACL rule named 'Z'"):
        run(monkeypatch, rules=['Z'])


def test_rule_outside_user_defined_ordering_fails(fake, monkeypatch):
    other = fake.add_site('acl-rules', {'name': 'Derived'})
    with pytest.raises(AnsibleFail, match='not a user-defined'):
        run(monkeypatch, rules=[other['id']])
