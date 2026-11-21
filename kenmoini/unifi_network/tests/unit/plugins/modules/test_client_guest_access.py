# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import client_guest_access
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module


def action(fake, call, match):
    client = [c for c in fake.items('clients') if c['id'] == match.group(1)][0]
    client['access']['authorized'] = call.body['action'] == 'AUTHORIZE_GUEST_ACCESS'
    return 200, {'action': call.body['action']}


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.on('POST', r'/v1/sites/[^/]+/clients/([^/]+)/actions', action)
    f.guest = f.add_site('clients', {'name': 'Visitor phone', 'macAddress': 'aa:bb:cc:dd:ee:02', 'ipAddress': '10.40.0.20',
                                     'type': 'WIRELESS', 'access': {'type': 'GUEST', 'authorized': False}})
    f.staff = f.add_site('clients', {'name': 'Laptop', 'macAddress': 'aa:bb:cc:dd:ee:03', 'type': 'WIRED',
                                     'access': {'type': 'DEFAULT'}})
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(client_guest_access.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def test_authorizes_by_mac_with_limits(fake, monkeypatch):
    result = run(monkeypatch, client='AA:BB:CC:DD:EE:02', time_limit_minutes=60, data_usage_limit_mbytes=500)
    assert result['changed'] is True
    assert fake.writes[0].path.endswith('/clients/%s/actions' % fake.guest['id'])
    assert fake.writes[0].body == {'action': 'AUTHORIZE_GUEST_ACCESS', 'timeLimitMinutes': 60, 'dataUsageLimitMBytes': 500}
    assert result['client']['access']['authorized'] is True


def test_already_authorized_is_a_no_op(fake, monkeypatch):
    fake.guest['access']['authorized'] = True
    fake.items('clients')[0]['access']['authorized'] = True
    assert run(monkeypatch, client='Visitor phone')['changed'] is False
    assert fake.writes == []


def test_unauthorize_by_ip(fake, monkeypatch):
    fake.items('clients')[0]['access']['authorized'] = True
    result = run(monkeypatch, client='10.40.0.20', state='unauthorized')
    assert result['changed'] is True
    assert fake.writes[0].body == {'action': 'UNAUTHORIZE_GUEST_ACCESS'}


def test_limits_rejected_when_unauthorizing(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='time_limit_minutes'):
        run(monkeypatch, client='Visitor phone', state='unauthorized', time_limit_minutes=5)


def test_non_guest_client_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='not a guest'):
        run(monkeypatch, client='Laptop')


def test_check_mode(fake, monkeypatch):
    result = run(monkeypatch, client='Visitor phone', check_mode=True)
    assert result['changed'] is True
    assert fake.writes == []
