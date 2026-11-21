# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import hotspot_voucher
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi, compile_filter
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module

VOUCHERS = r'/v1/sites/[^/]+/hotspot/vouchers'


def generate(fake, call, match):
    body = dict(call.body)
    count = body.pop('count', 1)
    created = [fake.add_site('hotspot/vouchers', dict(body, code='%05d' % i, expired=False, authorizedGuestCount=0))
               for i in range(count)]
    return 201, {'vouchers': created}


def bulk_delete(fake, call, match):
    pred = compile_filter(call.query.get('filter'))
    items = fake.items('hotspot/vouchers')
    doomed = [v for v in items if pred(v)]
    for v in doomed:
        items.remove(v)
    return 200, {'vouchersDeleted': len(doomed)}


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.on('POST', VOUCHERS, generate)
    f.on('DELETE', VOUCHERS, bulk_delete)
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(hotspot_voucher.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def voucher(fake, **kw):
    obj = {'name': 'Conference', 'timeLimitMinutes': 480, 'expired': False, 'code': 'x', 'authorizedGuestCount': 0}
    obj.update(kw)
    return fake.add_site('hotspot/vouchers', obj)


def test_generates_requested_count(fake, monkeypatch):
    result = run(monkeypatch, name='Conference', count=3, time_limit_minutes=480, data_usage_limit_mbytes=1024)
    assert result['changed'] is True
    assert fake.writes[0].body == {'name': 'Conference', 'count': 3, 'timeLimitMinutes': 480, 'dataUsageLimitMBytes': 1024}
    assert len(result['hotspot_vouchers']) == 3
    assert result['created_count'] == 3


def test_only_generates_the_shortfall(fake, monkeypatch):
    voucher(fake)
    voucher(fake)
    result = run(monkeypatch, name='Conference', count=5, time_limit_minutes=480)
    assert fake.writes[0].body['count'] == 3
    assert len(result['hotspot_vouchers']) == 5


def test_enough_vouchers_is_a_no_op(fake, monkeypatch):
    voucher(fake)
    voucher(fake)
    result = run(monkeypatch, name='Conference', count=2, time_limit_minutes=480)
    assert result['changed'] is False
    assert fake.writes == []
    assert result['created_count'] == 0


def test_expired_or_different_vouchers_do_not_count(fake, monkeypatch):
    voucher(fake, expired=True)
    voucher(fake, timeLimitMinutes=60)
    result = run(monkeypatch, name='Conference', count=1, time_limit_minutes=480)
    assert result['changed'] is True
    assert fake.writes[0].body['count'] == 1


def test_check_mode_generates_nothing(fake, monkeypatch):
    result = run(monkeypatch, name='Conference', count=2, time_limit_minutes=480, check_mode=True)
    assert result['changed'] is True
    assert result['created_count'] == 2
    assert fake.writes == []


def test_present_requires_time_limit(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='time_limit_minutes'):
        run(monkeypatch, name='Conference', count=1)


def test_absent_by_name_bulk_deletes(fake, monkeypatch):
    voucher(fake)
    voucher(fake)
    voucher(fake, name='Other')
    result = run(monkeypatch, name='Conference', state='absent')
    assert result['changed'] is True
    assert result['deleted_count'] == 2
    deleted = sorted(v['id'] for v in result['hotspot_vouchers'])
    assert fake.writes[0].method == 'DELETE'
    assert fake.writes[0].query['filter'] == 'id.in(%s)' % ','.join("'%s'" % i for i in deleted)
    assert run(monkeypatch, name='Conference', state='absent')['changed'] is False


def test_absent_only_expired(fake, monkeypatch):
    voucher(fake)
    voucher(fake, expired=True)
    result = run(monkeypatch, name='Conference', state='absent', only_expired=True)
    assert result['deleted_count'] == 1
    assert fake.writes[0].query['filter'].startswith('id.in(')
    assert len(fake.items('hotspot/vouchers')) == 1


def test_absent_by_id(fake, monkeypatch):
    v = voucher(fake)
    result = run(monkeypatch, id=v['id'], state='absent')
    assert result['changed'] is True
    assert fake.writes[0].path.endswith('/hotspot/vouchers/' + v['id'])
    assert run(monkeypatch, id=v['id'], state='absent')['changed'] is False


def test_absent_check_mode(fake, monkeypatch):
    voucher(fake)
    result = run(monkeypatch, name='Conference', state='absent', check_mode=True)
    assert result['changed'] is True and result['deleted_count'] == 1
    assert fake.writes == []


def test_names_with_quotes_are_matched_client_side(fake, monkeypatch):
    voucher(fake, name="Ken's party")
    result = run(monkeypatch, name="Ken's party", count=1, time_limit_minutes=480)
    assert result['changed'] is False
    assert all("Ken" not in (c.query.get('filter') or '') for c in fake.calls)
