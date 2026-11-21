# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import device_action, port_action
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.on('POST', r'/v1/sites/[^/]+/devices/[^/]+/actions', lambda fk, call, m: (200, {}))
    f.on('POST', r'/v1/sites/[^/]+/devices/[^/]+/interfaces/ports/\d+/actions', lambda fk, call, m: (200, {}))
    f.switch = f.add_site('devices', {'name': 'Core Switch', 'macAddress': 'aa:bb:cc:00:00:01',
                                      'interfaces': {'ports': [{'idx': 1, 'state': 'UP'}, {'idx': 2, 'state': 'UP'}]}})
    return f


def test_restart_device_by_name(fake, monkeypatch):
    result = run_module(device_action.main, {'device': 'Core Switch', 'action': 'restart'}, monkeypatch)
    assert result['changed'] is True
    assert fake.writes[0].path.endswith('/devices/%s/actions' % fake.switch['id'])
    assert fake.writes[0].body == {'action': 'RESTART'}


def test_restart_accepts_legacy_option_names(fake, monkeypatch):
    run_module(device_action.main, {'unifi_network_device_id': fake.switch['id'], 'device_action': 'restart'}, monkeypatch)
    assert fake.writes[0].body == {'action': 'RESTART'}


def test_restart_check_mode_verifies_device_only(fake, monkeypatch):
    result = run_module(device_action.main, {'device': 'Core Switch', 'action': 'restart'}, monkeypatch, check_mode=True)
    assert result['changed'] is True
    assert fake.writes == []


def test_restart_unknown_device_fails(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='No device'):
        run_module(device_action.main, {'device': 'Nope', 'action': 'restart'}, monkeypatch, check_mode=True)


def test_power_cycle_port(fake, monkeypatch):
    result = run_module(port_action.main, {'device': 'aa:bb:cc:00:00:01', 'port': 2, 'action': 'power_cycle'}, monkeypatch)
    assert result['changed'] is True
    assert fake.writes[0].path.endswith('/devices/%s/interfaces/ports/2/actions' % fake.switch['id'])
    assert fake.writes[0].body == {'action': 'POWER_CYCLE'}


def test_power_cycle_check_mode_verifies_port(fake, monkeypatch):
    result = run_module(port_action.main, {'device': 'Core Switch', 'port': 1, 'port_action': 'power_cycle'}, monkeypatch,
                        check_mode=True)
    assert result['changed'] is True
    assert fake.writes == []
    with pytest.raises(AnsibleFail, match='has no port 9'):
        run_module(port_action.main, {'device': 'Core Switch', 'port': 9, 'action': 'power_cycle'}, monkeypatch, check_mode=True)
