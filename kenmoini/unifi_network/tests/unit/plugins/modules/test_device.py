# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import device
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module

MAC = 'aa:bb:cc:dd:ee:01'


def adopt(fake, call, match):
    pending = [d for d in fake.collections['/v1/pending-devices'] if d['macAddress'] == call.body['macAddress']]
    fake.collections['/v1/pending-devices'].remove(pending[0])
    return 200, fake.add_site('devices', {'macAddress': call.body['macAddress'], 'name': 'U7 Pro', 'state': 'ADOPTING'})


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.on('POST', r'/v1/sites/[^/]+/devices', adopt)
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(device.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def test_adopts_pending_device(fake, monkeypatch):
    fake.add('/v1/pending-devices', {'macAddress': MAC, 'model': 'U7PRO'})
    result = run(monkeypatch, mac_address='AA:BB:CC:DD:EE:01')
    assert result['changed'] is True
    assert fake.writes[0].body == {'macAddress': MAC, 'ignoreDeviceLimit': False}
    assert result['device']['macAddress'] == MAC


def test_already_adopted_is_a_no_op(fake, monkeypatch):
    fake.add_site('devices', {'macAddress': MAC, 'name': 'AP'})
    result = run(monkeypatch, mac_address=MAC)
    assert result['changed'] is False
    assert fake.writes == []


def test_unknown_device_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='not pending adoption'):
        run(monkeypatch, mac_address=MAC)


def test_check_mode_does_not_adopt(fake, monkeypatch):
    fake.add('/v1/pending-devices', {'macAddress': MAC, 'model': 'U7PRO'})
    result = run(monkeypatch, mac_address=MAC, check_mode=True)
    assert result['changed'] is True
    assert fake.writes == []


def test_absent_unadopts(fake, monkeypatch):
    fake.add_site('devices', {'macAddress': MAC, 'name': 'AP'})
    assert run(monkeypatch, mac_address=MAC, state='absent')['changed'] is True
    assert fake.writes[0].method == 'DELETE'
    assert run(monkeypatch, mac_address=MAC, state='absent')['changed'] is False


def test_invalid_mac_rejected(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='MAC address'):
        run(monkeypatch, mac_address='not-a-mac')


def test_id_must_match_mac_address(fake, monkeypatch):
    other = fake.add_site('devices', {'macAddress': 'aa:bb:cc:dd:ee:99', 'name': 'Other AP'})
    with pytest.raises(AnsibleFail, match='does not match'):
        run(monkeypatch, mac_address=MAC, id=other['id'], state='absent')
    assert fake.writes == []
