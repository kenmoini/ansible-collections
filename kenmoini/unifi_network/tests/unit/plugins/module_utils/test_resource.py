# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import StateResource, run_state_module
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module


class Widget(StateResource):
    path = 'traffic-matching-lists'
    result_key = 'widget'
    label = 'widget'
    create_required = {'type': 'type'}
    secret_paths = (('secret',),)
    secret_update_param = 'update_secret'
    supports_force = True

    def to_api(self, current):
        p = self.params
        desired = {}
        for opt in ('name', 'type', 'items', 'secret'):
            if p.get(opt) is not None:
                desired[opt] = p[opt]
        if p.get('note') is not None:
            desired['note'] = p['note'] or None
        return desired


def main():
    spec = state_argument_spec()
    spec.update(
        name=dict(type='str'),
        type=dict(type='str'),
        items=dict(type='list', elements='raw'),
        secret=dict(type='str', no_log=True),
        update_secret=dict(type='str', default='on_create', choices=['on_create', 'always']),
        force=dict(type='bool', default=False),
        note=dict(type='str'),
    )
    run_state_module(Widget, spec, required_one_of=[('name', 'id')])


@pytest.fixture
def fake(monkeypatch):
    return FakeUnifi().install(monkeypatch)


def run(monkeypatch, **kwargs):
    check_mode = kwargs.pop('check_mode', False)
    diff = kwargs.pop('diff', False)
    return run_module(main, kwargs, monkeypatch, check_mode=check_mode, diff=diff)


def test_creates_when_missing(fake, monkeypatch):
    result = run(monkeypatch, name='w1', type='PORTS', items=[22])
    assert result['changed'] is True
    assert result['widget']['name'] == 'w1'
    assert result['widget']['id']
    assert [c.method for c in fake.writes] == ['POST']
    assert fake.writes[0].body == {'name': 'w1', 'type': 'PORTS', 'items': [22]}


def test_second_run_is_idempotent(fake, monkeypatch):
    run(monkeypatch, name='w1', type='PORTS', items=[22, 443])
    result = run(monkeypatch, name='w1', type='PORTS', items=[443, 22])
    assert result['changed'] is False
    assert len(fake.writes) == 1


def test_update_puts_full_object_keeping_unmanaged_fields(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'w1', 'type': 'PORTS', 'items': [22], 'note': 'keep',
                                             'metadata': {'origin': 'USER_DEFINED'}})
    result = run(monkeypatch, name='w1', items=[22, 80])
    assert result['changed'] is True
    put = fake.writes[0]
    assert put.method == 'PUT'
    assert put.body == {'name': 'w1', 'type': 'PORTS', 'items': [22, 80], 'note': 'keep'}


def test_none_value_removes_feature(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'w1', 'type': 'PORTS', 'items': [22], 'note': 'drop'})
    result = run(monkeypatch, name='w1', note='')
    assert result['changed'] is True
    assert 'note' not in fake.writes[0].body
    assert run(monkeypatch, name='w1', note='')['changed'] is False


def test_check_mode_create_makes_no_writes(fake, monkeypatch):
    result = run(monkeypatch, name='w1', type='PORTS', items=[22], check_mode=True, diff=True)
    assert result['changed'] is True
    assert fake.writes == []
    assert result['diff'] == {'before': {}, 'after': {'name': 'w1', 'type': 'PORTS', 'items': [22]}}


def test_check_mode_update_predicts_and_diffs(fake, monkeypatch):
    obj = fake.add_site('traffic-matching-lists', {'name': 'w1', 'type': 'PORTS', 'items': [22]})
    result = run(monkeypatch, name='w1', items=[80], check_mode=True, diff=True)
    assert result['changed'] is True
    assert fake.writes == []
    assert result['widget'] == dict(obj, items=[80])
    assert result['diff']['before']['items'] == [22]
    assert result['diff']['after']['items'] == [80]


def test_id_lookup_allows_rename(fake, monkeypatch):
    obj = fake.add_site('traffic-matching-lists', {'name': 'old', 'type': 'PORTS', 'items': [22]})
    result = run(monkeypatch, id=obj['id'], name='new')
    assert result['changed'] is True
    assert fake.writes[0].body['name'] == 'new'


def test_unknown_id_fails_instead_of_creating(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='No widget with id'):
        run(monkeypatch, id='11111111-2222-4333-8444-555555555555', name='x', type='PORTS')
    assert fake.writes == []


def test_ambiguous_name_fails_listing_ids(fake, monkeypatch):
    a = fake.add_site('traffic-matching-lists', {'name': 'dup', 'type': 'PORTS'})
    fake.add_site('traffic-matching-lists', {'name': 'dup', 'type': 'PORTS'})
    with pytest.raises(AnsibleFail) as exc:
        run(monkeypatch, name='dup', items=[1])
    assert a['id'] in exc.value.result['msg']
    assert 'id' in exc.value.result['msg']


def test_create_requires_fields(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='requires: type'):
        run(monkeypatch, name='w1', items=[22])


def test_absent_deletes_then_is_noop(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'w1', 'type': 'PORTS'})
    assert run(monkeypatch, name='w1', state='absent')['changed'] is True
    assert fake.writes[0].method == 'DELETE'
    assert 'force' not in fake.writes[0].query
    assert run(monkeypatch, name='w1', state='absent')['changed'] is False
    assert len(fake.writes) == 1


def test_absent_passes_force(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'w1', 'type': 'PORTS'})
    run(monkeypatch, name='w1', state='absent', force=True)
    assert fake.writes[0].query == {'force': 'true'}


def test_absent_check_mode_makes_no_writes(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'w1', 'type': 'PORTS'})
    result = run(monkeypatch, name='w1', state='absent', check_mode=True, diff=True)
    assert result['changed'] is True
    assert fake.writes == []
    assert result['diff']['after'] == {}


def test_secret_is_ignored_for_comparison_on_create_policy(fake, monkeypatch):
    run(monkeypatch, name='w1', type='PORTS', secret='hunter22')
    result = run(monkeypatch, name='w1', type='PORTS', secret='other-secret')
    assert result['changed'] is False
    assert 'secret' not in result['widget']


def test_secret_always_forces_update_and_is_sent(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'w1', 'type': 'PORTS'})
    result = run(monkeypatch, name='w1', secret='hunter22', update_secret='always', diff=True)
    assert result['changed'] is True
    assert fake.writes[0].body['secret'] == 'hunter22'
    assert 'secret' not in result['diff']['after']


def test_secret_rides_along_on_other_updates(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': 'w1', 'type': 'PORTS', 'items': [1]})
    run(monkeypatch, name='w1', items=[2], secret='hunter22')
    assert fake.writes[0].body['secret'] == 'hunter22'


def test_api_errors_become_module_failures(fake, monkeypatch):
    with pytest.raises(AnsibleFail) as exc:
        run(monkeypatch, name='w1', type='PORTS', unifi_network_site_id='nosuchsite')
    assert "No site named 'nosuchsite'" in exc.value.result['msg']


def test_names_with_quotes_are_found_client_side(fake, monkeypatch):
    fake.add_site('traffic-matching-lists', {'name': "Ken's list", 'type': 'PORTS', 'items': [22]})
    assert run(monkeypatch, name="Ken's list", items=[22])['changed'] is False
    lookups = [c for c in fake.calls if c.path.endswith('/traffic-matching-lists')]
    assert lookups and all('filter' not in c.query for c in lookups)
