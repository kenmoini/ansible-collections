# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import wifi_broadcast
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import SITE_ID, FakeUnifi, compile_filter
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module

COLLECTION = 'wifi/broadcasts'
PASSPHRASE = 'correct horse battery'

# Keys required on create that the module fills in when the user does not set them.
COMMON_DEFAULTS = {
    'enabled': True, 'hideName': False, 'clientIsolationEnabled': False, 'multicastToUnicastConversionEnabled': False,
    'uapsdEnabled': False, 'channel2gLockedTo6': False, 'dtimPeriod2gLockedTo3': False,
}
STANDARD_DEFAULTS = dict(COMMON_DEFAULTS, type='STANDARD', advertiseDeviceName=False, arpProxyEnabled=False,
                         bssTransitionEnabled=True, broadcastingFrequenciesGHz=[2.4, 5])

OVERVIEW_KEYS = ('id', 'name', 'type', 'enabled', 'metadata', 'network', 'broadcastingDeviceFilter', 'broadcastingFrequenciesGHz')


def _without_secrets(obj):
    obj = copy.deepcopy(obj)
    sec = obj.get('securityConfiguration') or {}
    sec.pop('passphrase', None)
    for psk in sec.get('presharedKeys') or []:
        psk.pop('passphrase', None)
    return obj


def _get_item(fake, call, match):
    for obj in fake.items(COLLECTION):
        if obj['id'] == match.group('id'):
            return 200, _without_secrets(obj)
    return 404, 'not found'


def _list(fake, call, match):
    """Like the real API, the list returns an overview without most settings."""
    pred = compile_filter(call.query.get('filter'))
    data = []
    for obj in fake.items(COLLECTION):
        if pred(obj):
            item = dict((k, copy.deepcopy(obj[k])) for k in OVERVIEW_KEYS if k in obj)
            item['securityConfiguration'] = {'type': obj['securityConfiguration']['type']}
            data.append(item)
    return 200, {'offset': 0, 'limit': 25, 'count': len(data), 'totalCount': len(data), 'data': data}


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    base = '/v1/sites/%s/wifi/broadcasts' % SITE_ID
    f.on('GET', base, _list)
    f.on('GET', base + '/(?P<id>[^/]+)', _get_item)
    f.iot = f.add_site('networks', {'name': 'IoT', 'vlanId': 30})
    f.guest = f.add_site('networks', {'name': 'Guest', 'vlanId': 40})
    f.ap = f.add_site('devices', {'name': 'Office AP', 'macAddress': 'aa:bb:cc:00:00:01'})
    f.ap2 = f.add_site('devices', {'name': 'Garage AP', 'macAddress': 'aa:bb:cc:00:00:02'})
    f.tag = f.add_site('device-tags', {'name': 'Upstairs'})
    f.radius = f.add_site('radius/profiles', {'name': 'Corp RADIUS'})
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(wifi_broadcast.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def update(monkeypatch, **args):
    """Update an existing personal-security broadcast.

    The API never returns the passphrase and an update replaces the whole object, so (like a real playbook)
    the passphrase is sent along unless the call explicitly switches the security type.
    """
    sec = dict(args.get('security') or {})
    if 'type' not in sec:
        sec.setdefault('passphrase', PASSPHRASE)
        args['security'] = sec
    return run(monkeypatch, **args)


def existing(fake, **overrides):
    obj = copy.deepcopy(STANDARD_DEFAULTS)
    obj.update(name='Home', securityConfiguration={'type': 'WPA2_PERSONAL', 'passphrase': PASSPHRASE, 'pmfMode': 'OPTIONAL'},
               metadata={'origin': 'USER_DEFINED'})
    obj.update(overrides)
    return fake.add_site(COLLECTION, obj)


def wpa2(passphrase=PASSPHRASE, **extra):
    return dict(type='wpa2_personal', passphrase=passphrase, **extra)


def assert_no_secret(value):
    assert PASSPHRASE not in json.dumps(value)


# ---- create ---------------------------------------------------------------

def test_create_wpa2_personal_sends_defaults_and_passphrase(fake, monkeypatch):
    result = run(monkeypatch, name='Home', security=wpa2(), diff=True)
    assert result['changed'] is True
    assert [c.method for c in fake.writes] == ['POST']
    assert fake.writes[0].body == dict(STANDARD_DEFAULTS, name='Home', securityConfiguration={
        'type': 'WPA2_PERSONAL', 'passphrase': PASSPHRASE})
    assert result['wifi_broadcast']['name'] == 'Home'
    assert_no_secret(result['wifi_broadcast'])
    assert_no_secret(result['diff'])


def test_create_iot_optimized_has_no_standard_defaults(fake, monkeypatch):
    run(monkeypatch, name='Things', type='iot_optimized', network='IoT', security=wpa2())
    assert fake.writes[0].body == dict(COMMON_DEFAULTS, type='IOT_OPTIMIZED', name='Things',
                                       network={'type': 'SPECIFIC', 'networkId': fake.iot['id']},
                                       securityConfiguration={'type': 'WPA2_PERSONAL', 'passphrase': PASSPHRASE})


def test_create_requires_security_type(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='security.type'):
        run(monkeypatch, name='Home')
    with pytest.raises(AnsibleFail, match='security.type'):
        run(monkeypatch, name='Home', security={'passphrase': PASSPHRASE})
    assert fake.writes == []


def test_create_personal_requires_passphrase(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='security.passphrase'):
        run(monkeypatch, name='Home', security={'type': 'wpa3_personal'})


def test_create_wpa2_wpa3_personal_fills_required_security_defaults(fake, monkeypatch):
    run(monkeypatch, name='Home', security={'type': 'wpa2_wpa3_personal', 'passphrase': PASSPHRASE})
    assert fake.writes[0].body['securityConfiguration'] == {
        'type': 'WPA2_WPA3_PERSONAL', 'passphrase': PASSPHRASE, 'pmfMode': 'OPTIONAL',
        'saeConfiguration': {'anticloggingThresholdSeconds': 5, 'syncTimeSeconds': 5},
        'wpa3FastRoamingEnabled': False}


def test_create_wpa3_personal_with_sae_and_options(fake, monkeypatch):
    run(monkeypatch, name='Home', security={'type': 'wpa3_personal', 'passphrase': PASSPHRASE, 'fast_roaming_enabled': True,
                                            'group_rekey_interval_seconds': 3600, 'sae': {'sync_time_seconds': 10}})
    assert fake.writes[0].body['securityConfiguration'] == {
        'type': 'WPA3_PERSONAL', 'passphrase': PASSPHRASE, 'fastRoamingEnabled': True, 'groupRekeyIntervalSeconds': 3600,
        'saeConfiguration': {'anticloggingThresholdSeconds': 5, 'syncTimeSeconds': 10}}


def test_create_open_with_enhanced_open(fake, monkeypatch):
    run(monkeypatch, name='Cafe', security={'type': 'open', 'encryption': 'enhanced_open_with_transition'})
    assert fake.writes[0].body['securityConfiguration'] == {'type': 'OPEN', 'encryption': 'ENHANCED_OPEN_WITH_TRANSITION'}


def test_create_wpa3_enterprise_defaults(fake, monkeypatch):
    run(monkeypatch, name='Corp', security={'type': 'wpa3_enterprise', 'radius_profile': 'Corp RADIUS',
                                            'nas_id': 'corp-wifi', 'mac_auth_format': 'uppercase_dash_separated'})
    assert fake.writes[0].body['securityConfiguration'] == {
        'type': 'WPA3_ENTERPRISE', 'coaEnabled': False, 'securityMode': 'DEFAULT',
        'radiusConfiguration': {'profileId': fake.radius['id'], 'nasId': {'type': 'USER_DEFINED', 'value': 'corp-wifi'},
                                'macAuthenticationConfiguration': {'macAddressFormat': 'UPPERCASE_DASH_SEPARATED'}}}


def test_personal_with_radius_mac_authentication_defaults_format(fake, monkeypatch):
    run(monkeypatch, name='Home', security=wpa2(radius_profile='Corp RADIUS', nas_id_source='site_name'))
    assert fake.writes[0].body['securityConfiguration']['radiusConfiguration'] == {
        'profileId': fake.radius['id'], 'nasId': {'type': 'DERIVED', 'source': 'SITE_NAME'},
        'macAuthenticationConfiguration': {'macAddressFormat': 'LOWERCASE_NOT_SEPARATED'}}


def test_preshared_keys_are_sent_but_never_returned(fake, monkeypatch):
    result = run(monkeypatch, name='Home', diff=True, security={
        'type': 'wpa2_personal', 'preshared_keys': [{'network': 'IoT', 'passphrase': PASSPHRASE},
                                                    {'network': 'native', 'passphrase': 'other passphrase'}]})
    assert fake.writes[0].body['securityConfiguration'] == {'type': 'WPA2_PERSONAL', 'presharedKeys': [
        {'network': {'type': 'SPECIFIC', 'networkId': fake.iot['id']}, 'passphrase': PASSPHRASE},
        {'network': {'type': 'NATIVE'}, 'passphrase': 'other passphrase'}]}
    assert_no_secret(result)
    assert 'other passphrase' not in json.dumps(result)
    again = run(monkeypatch, name='Home', security={'type': 'wpa2_personal', 'preshared_keys': [{'network': 'IoT', 'passphrase': 'x' * 8}]})
    assert again['changed'] is False


# ---- idempotency and secrets ------------------------------------------------

def test_rerun_with_other_passphrase_is_unchanged_under_on_create(fake, monkeypatch):
    run(monkeypatch, name='Home', network='IoT', security=wpa2(pmf_mode='optional'))
    result = run(monkeypatch, name='Home', network='IoT', security=wpa2(passphrase='a different one', pmf_mode='optional'))
    assert result['changed'] is False
    assert len(fake.writes) == 1


def test_update_passphrase_always_puts_passphrase(fake, monkeypatch):
    existing(fake)
    result = run(monkeypatch, name='Home', security=wpa2(passphrase='new passphrase'), update_passphrase='always', diff=True)
    assert result['changed'] is True
    put = fake.writes[0]
    assert put.method == 'PUT'
    assert put.body['securityConfiguration'] == {'type': 'WPA2_PERSONAL', 'passphrase': 'new passphrase', 'pmfMode': 'OPTIONAL'}
    assert 'new passphrase' not in json.dumps(result)
    assert 'passphrase' not in result['diff']['after']['securityConfiguration']


def test_passphrase_rides_along_with_other_changes(fake, monkeypatch):
    existing(fake)
    result = run(monkeypatch, name='Home', hide_name=True, security=wpa2())
    assert result['changed'] is True
    assert fake.writes[0].body['hideName'] is True
    assert fake.writes[0].body['securityConfiguration']['passphrase'] == PASSPHRASE
    assert_no_secret(result)


def test_update_compares_against_details_not_list_overview(fake, monkeypatch):
    existing(fake, uapsdEnabled=True, clientIsolationEnabled=True)
    assert update(monkeypatch, name='Home', uapsd_enabled=True, client_isolation_enabled=True)['changed'] is False
    update(monkeypatch, name='Home', hide_name=True)
    body = fake.writes[0].body
    # Settings that only the detail GET returns are kept in the full-replacement PUT.
    assert body['uapsdEnabled'] is True and body['clientIsolationEnabled'] is True
    assert body['securityConfiguration'] == {'type': 'WPA2_PERSONAL', 'pmfMode': 'OPTIONAL', 'passphrase': PASSPHRASE}
    assert 'id' not in body and 'metadata' not in body


def test_lookup_by_id_allows_renaming(fake, monkeypatch):
    obj = existing(fake)
    update(monkeypatch, id=obj['id'], name='Home 2')
    assert fake.writes[0].body['name'] == 'Home 2'


# ---- security type changes -------------------------------------------------

def test_switch_to_enterprise_replaces_security_and_resolves_radius_profile(fake, monkeypatch):
    existing(fake, securityConfiguration={'type': 'WPA2_PERSONAL', 'pmfMode': 'OPTIONAL', 'fastRoamingEnabled': True})
    result = run(monkeypatch, name='Home', security={'type': 'wpa2_enterprise', 'radius_profile': 'Corp RADIUS'})
    assert result['changed'] is True
    assert fake.writes[0].body['securityConfiguration'] == {
        'type': 'WPA2_ENTERPRISE', 'coaEnabled': False,
        'radiusConfiguration': {'profileId': fake.radius['id'], 'nasId': {'type': 'DERIVED', 'source': 'DEVICE_NAME'}}}
    again = run(monkeypatch, name='Home', security={'type': 'wpa2_enterprise', 'radius_profile': 'Corp RADIUS'})
    assert again['changed'] is False


def test_switch_to_enterprise_requires_radius_profile(fake, monkeypatch):
    existing(fake)
    with pytest.raises(AnsibleFail, match='security.radius_profile'):
        run(monkeypatch, name='Home', security={'type': 'wpa2_wpa3_enterprise'})


def test_switch_to_personal_requires_passphrase(fake, monkeypatch):
    existing(fake, securityConfiguration={'type': 'OPEN'})
    with pytest.raises(AnsibleFail, match='security.passphrase'):
        run(monkeypatch, name='Home', security={'type': 'wpa2_personal'})


def test_security_option_for_wrong_security_type_rejected(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='encryption.*open'):
        run(monkeypatch, name='Home', security=wpa2(encryption='enhanced_open'))
    existing(fake)
    with pytest.raises(AnsibleFail, match='security_mode.*wpa3_enterprise'):
        run(monkeypatch, name='Home', security={'security_mode': 'high_security_192_bit'})


def test_pmf_disabled_removes_pmf_mode(fake, monkeypatch):
    existing(fake)
    update(monkeypatch, name='Home', security={'pmf_mode': 'disabled'})
    assert fake.writes[0].body['securityConfiguration'] == {'type': 'WPA2_PERSONAL', 'passphrase': PASSPHRASE}
    assert update(monkeypatch, name='Home', security={'pmf_mode': 'disabled'})['changed'] is False


def test_enterprise_cannot_drop_radius_profile(fake, monkeypatch):
    existing(fake, securityConfiguration={'type': 'WPA2_ENTERPRISE', 'coaEnabled': False, 'radiusConfiguration': {
        'profileId': fake.radius['id'], 'nasId': {'type': 'DERIVED', 'source': 'DEVICE_NAME'}}})
    with pytest.raises(AnsibleFail, match='radius_profile'):
        run(monkeypatch, name='Home', security={'radius_profile': ''})


def test_personal_radius_profile_empty_string_turns_mac_auth_off(fake, monkeypatch):
    existing(fake, securityConfiguration={'type': 'WPA2_PERSONAL', 'radiusConfiguration': {
        'profileId': fake.radius['id'], 'nasId': {'type': 'DERIVED', 'source': 'DEVICE_NAME'},
        'macAuthenticationConfiguration': {'macAddressFormat': 'LOWERCASE_NOT_SEPARATED'}}})
    update(monkeypatch, name='Home', security={'radius_profile': ''})
    assert fake.writes[0].body['securityConfiguration'] == {'type': 'WPA2_PERSONAL', 'passphrase': PASSPHRASE}


# ---- network and broadcasting devices --------------------------------------

def test_network_native_and_specific_by_name(fake, monkeypatch):
    update(monkeypatch, name='Home', network='IoT', security=wpa2())
    assert fake.writes[0].body['network'] == {'type': 'SPECIFIC', 'networkId': fake.iot['id']}
    update(monkeypatch, name='Home', network='native')
    assert fake.writes[1].body['network'] == {'type': 'NATIVE'}
    assert update(monkeypatch, name='Home', network='native')['changed'] is False
    update(monkeypatch, name='Home', network=fake.guest['id'])
    assert fake.writes[2].body['network'] == {'type': 'SPECIFIC', 'networkId': fake.guest['id']}


def test_device_tags_by_name(fake, monkeypatch):
    existing(fake)
    update(monkeypatch, name='Home', device_tags=['Upstairs'])
    assert fake.writes[0].body['broadcastingDeviceFilter'] == {'type': 'DEVICE_TAGS', 'deviceTagIds': [fake.tag['id']]}
    assert update(monkeypatch, name='Home', device_tags=['Upstairs'])['changed'] is False


def test_devices_by_name_and_mac_replace_device_tags(fake, monkeypatch):
    existing(fake, broadcastingDeviceFilter={'type': 'DEVICE_TAGS', 'deviceTagIds': [fake.tag['id']]})
    update(monkeypatch, name='Home', devices=['Office AP', 'AA:BB:CC:00:00:02'])
    assert fake.writes[0].body['broadcastingDeviceFilter'] == {'type': 'DEVICES', 'deviceIds': [fake.ap['id'], fake.ap2['id']]}


def test_devices_and_device_tags_are_mutually_exclusive(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='mutually exclusive'):
        run(monkeypatch, name='Home', security=wpa2(), devices=['Office AP'], device_tags=['Upstairs'])


# ---- variant scope ----------------------------------------------------------

def test_standard_only_option_rejected_for_iot(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='frequencies.*standard'):
        run(monkeypatch, name='Things', type='iot_optimized', security=wpa2(), frequencies=[2.4])
    existing(fake, name='Things', type='IOT_OPTIMIZED')
    with pytest.raises(AnsibleFail, match='band_steering_enabled.*standard'):
        run(monkeypatch, name='Things', band_steering_enabled=True)
    with pytest.raises(AnsibleFail, match='pmf_mode.*standard'):
        run(monkeypatch, name='Things', security={'pmf_mode': 'required'})
    assert fake.writes == []


def test_switch_to_iot_drops_standard_only_settings(fake, monkeypatch):
    existing(fake, bandSteeringEnabled=True, hotspotConfiguration={'type': 'CAPTIVE_PORTAL'},
             securityConfiguration={'type': 'WPA2_PERSONAL', 'pmfMode': 'OPTIONAL', 'fastRoamingEnabled': True,
                                    'groupRekeyIntervalSeconds': 3600})
    update(monkeypatch, name='Home', type='iot_optimized')
    body = fake.writes[0].body
    assert body['type'] == 'IOT_OPTIMIZED'
    for key in ('advertiseDeviceName', 'arpProxyEnabled', 'bandSteeringEnabled', 'broadcastingFrequenciesGHz',
                'bssTransitionEnabled', 'hotspotConfiguration'):
        assert key not in body
    # Security features that IoT-optimized broadcasts do not support are dropped as well.
    assert body['securityConfiguration'] == {'type': 'WPA2_PERSONAL', 'passphrase': PASSPHRASE}
    assert body['uapsdEnabled'] is False


def test_switch_to_standard_adds_required_standard_settings(fake, monkeypatch):
    obj = dict(COMMON_DEFAULTS, type='IOT_OPTIMIZED', name='Things', securityConfiguration={'type': 'WPA2_PERSONAL'})
    fake.add_site(COLLECTION, obj)
    update(monkeypatch, name='Things', type='standard', frequencies=[2.4])
    body = fake.writes[0].body
    assert body['type'] == 'STANDARD'
    assert body['broadcastingFrequenciesGHz'] == [2.4]
    assert body['advertiseDeviceName'] is False and body['arpProxyEnabled'] is False and body['bssTransitionEnabled'] is True


# ---- nested features --------------------------------------------------------

def test_blackout_schedule_mapping(fake, monkeypatch):
    existing(fake)
    schedule = [
        {'day': 'mon', 'start_time': '00:00', 'end_time': '6:30'},
        {'day': 'sat'},
        {'day': 'mon', 'start_time': '22:00', 'stop_time': '23:59'},
    ]
    update(monkeypatch, name='Home', blackout_schedule=schedule)
    assert fake.writes[0].body['blackoutScheduleConfiguration'] == {'days': [
        {'day': 'MON', 'type': 'TIME_RANGE', 'timeRanges': [
            {'startTime': '00:00', 'endTime': '06:30'}, {'startTime': '22:00', 'endTime': '23:59'}]},
        {'day': 'SAT', 'type': 'ALL_DAY'},
    ]}
    assert update(monkeypatch, name='Home', blackout_schedule=list(reversed(schedule)))['changed'] is False


def test_blackout_schedule_rejects_bad_times_and_mixed_days(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='HH:MM'):
        run(monkeypatch, name='Home', security=wpa2(), blackout_schedule=[{'day': 'mon', 'start_time': '360', 'end_time': '07:00'}])
    with pytest.raises(AnsibleFail, match='all day'):
        run(monkeypatch, name='Home', security=wpa2(),
            blackout_schedule=[{'day': 'mon'}, {'day': 'mon', 'start_time': '01:00', 'end_time': '02:00'}])
    with pytest.raises(AnsibleFail, match='start_time'):
        run(monkeypatch, name='Home', security=wpa2(), blackout_schedule=[{'day': 'mon', 'start_time': '01:00'}])


def test_client_filtering_mdns_multicast_and_rates(fake, monkeypatch):
    existing(fake)
    update(
        monkeypatch, name='Home',
        client_filtering={'action': 'block', 'mac_addresses': ['AA:BB:CC:DD:EE:FF']},
        mdns_proxy={'mode': 'custom', 'policies': [
            {'action': 'allow', 'services': ['apple_air_play', 'printers'], 'bridging_networks': ['IoT'],
             'custom_services': [{'name': 'Home Assistant', 'type_domain': '_home-assistant._tcp'}], 'device_tags': ['Upstairs']},
            {'action': 'block', 'devices': ['Garage AP']},
        ]},
        multicast_filtering={'action': 'allow', 'source_mac_addresses': ['aa:bb:cc:00:00:99']},
        basic_data_rates={'rate_2g': 12000, 'rate_5g': 24000})
    body = fake.writes[0].body
    assert body['clientFilteringPolicy'] == {'action': 'BLOCK', 'macAddressFilter': ['AA:BB:CC:DD:EE:FF']}
    assert body['mdnsProxyConfiguration'] == {'mode': 'CUSTOM', 'policies': [
        {'action': 'ALLOW', 'bridgingNetworkIds': [fake.iot['id']],
         'serviceFilter': [{'type': 'PREDEFINED', 'name': 'APPLE_AIR_PLAY'}, {'type': 'PREDEFINED', 'name': 'PRINTERS'},
                           {'type': 'CUSTOM', 'name': 'Home Assistant', 'typeDomain': '_home-assistant._tcp'}],
         'deviceFilter': {'type': 'DEVICE_TAGS', 'deviceTagIds': [fake.tag['id']]}},
        {'action': 'BLOCK', 'deviceFilter': {'type': 'DEVICES', 'deviceIds': [fake.ap2['id']]}},
    ]}
    assert body['multicastFilteringPolicy'] == {'action': 'ALLOW', 'sourceMacAddressFilter': ['aa:bb:cc:00:00:99']}
    assert body['basicDataRateKbpsByFrequencyGHz'] == {'2.4': 12000, '5': 24000}


def test_client_filtering_action_change_keeps_mac_list(fake, monkeypatch):
    existing(fake, clientFilteringPolicy={'action': 'ALLOW', 'macAddressFilter': ['aa:bb:cc:dd:ee:ff']})
    update(monkeypatch, name='Home', client_filtering={'action': 'block'})
    assert fake.writes[0].body['clientFilteringPolicy'] == {'action': 'BLOCK', 'macAddressFilter': ['aa:bb:cc:dd:ee:ff']}


def test_feature_first_enable_requires_fields(fake, monkeypatch):
    existing(fake)
    with pytest.raises(AnsibleFail, match='client_filtering.action'):
        run(monkeypatch, name='Home', client_filtering={'mac_addresses': ['aa:bb:cc:dd:ee:ff']})
    with pytest.raises(AnsibleFail, match='basic_data_rates.rate_5g'):
        run(monkeypatch, name='Home', basic_data_rates={'rate_2g': 6000})
    with pytest.raises(AnsibleFail, match='policies'):
        run(monkeypatch, name='Home', mdns_proxy={'mode': 'custom'})
    with pytest.raises(AnsibleFail, match='services'):
        run(monkeypatch, name='Home', mdns_proxy={'mode': 'custom', 'policies': [{'action': 'block', 'services': ['printers']}]})


def test_standard_only_settings(fake, monkeypatch):
    existing(fake)
    update(
        monkeypatch, name='Home', frequencies=[5, 6, 2.4], band_steering_enabled=True, mlo_enabled=True, hotspot='captive_portal',
        dns_assistance={'mode': 'manual', 'servers': ['1.1.1.1']},
        dtim_period_override={'period_2g': 3, 'period_5g': 1, 'period_6g': 1},
        handoff_suggestions={'rssi_threshold_5g': -70})
    body = fake.writes[0].body
    assert sorted(body['broadcastingFrequenciesGHz']) == [2.4, 5, 6]
    assert all(isinstance(f, int) for f in body['broadcastingFrequenciesGHz'] if f != 2.4)
    assert body['bandSteeringEnabled'] is True and body['mloEnabled'] is True
    assert body['hotspotConfiguration'] == {'type': 'CAPTIVE_PORTAL'}
    assert body['dnsAssistanceConfiguration'] == {'mode': 'MANUAL', 'servers': ['1.1.1.1']}
    assert body['dtimPeriodByFrequencyGHzOverride'] == {'2.4': 3, '5': 1, '6': 1}
    assert body['handoffSuggestionsConfiguration'] == {'band5GHzRssiThreshold': -70}
    assert update(monkeypatch, name='Home', frequencies=[2.4, 5, 6], hotspot='captive_portal')['changed'] is False


def test_empty_lists_and_disabled_remove_features(fake, monkeypatch):
    existing(fake,
             broadcastingDeviceFilter={'type': 'DEVICES', 'deviceIds': [fake.ap['id']]},
             blackoutScheduleConfiguration={'days': [{'day': 'SUN', 'type': 'ALL_DAY'}]},
             clientFilteringPolicy={'action': 'ALLOW', 'macAddressFilter': []},
             mdnsProxyConfiguration={'mode': 'AUTO'},
             multicastFilteringPolicy={'action': 'BLOCK'},
             basicDataRateKbpsByFrequencyGHz={'2.4': 6000, '5': 6000},
             hotspotConfiguration={'type': 'PASSPOINT'},
             dnsAssistanceConfiguration={'mode': 'AUTO'},
             dtimPeriodByFrequencyGHzOverride={'2.4': 3, '5': 3, '6': 3},
             handoffSuggestionsConfiguration={'band5GHzRssiThreshold': -70})
    args = dict(name='Home', devices=[], blackout_schedule=[], client_filtering={'enabled': False},
                mdns_proxy={'mode': 'disabled'}, multicast_filtering={'enabled': False}, basic_data_rates={'enabled': False},
                hotspot='disabled', dns_assistance={'mode': 'disabled'}, dtim_period_override={'enabled': False},
                handoff_suggestions={'enabled': False})
    result = update(monkeypatch, **args)
    assert result['changed'] is True
    body = fake.writes[0].body
    for key in ('broadcastingDeviceFilter', 'blackoutScheduleConfiguration', 'clientFilteringPolicy', 'mdnsProxyConfiguration',
                'multicastFilteringPolicy', 'basicDataRateKbpsByFrequencyGHz', 'hotspotConfiguration', 'dnsAssistanceConfiguration',
                'dtimPeriodByFrequencyGHzOverride', 'handoffSuggestionsConfiguration'):
        assert key not in body
    assert update(monkeypatch, **args)['changed'] is False


# ---- check mode and absent ---------------------------------------------------

def test_check_mode_create_makes_no_writes(fake, monkeypatch):
    result = run(monkeypatch, check_mode=True, diff=True, name='Home', security=wpa2())
    assert result['changed'] is True
    assert fake.writes == []
    assert result['wifi_broadcast']['securityConfiguration'] == {'type': 'WPA2_PERSONAL'}
    assert_no_secret(result)


def test_check_mode_update_makes_no_writes(fake, monkeypatch):
    existing(fake)
    result = run(monkeypatch, check_mode=True, diff=True, name='Home', enabled=False, security=wpa2(), update_passphrase='always')
    assert result['changed'] is True
    assert fake.writes == []
    assert result['wifi_broadcast']['enabled'] is False
    assert_no_secret(result)


def test_absent_with_force(fake, monkeypatch):
    existing(fake)
    assert run(monkeypatch, name='Home', state='absent', force=True)['changed'] is True
    assert fake.writes[0].method == 'DELETE' and fake.writes[0].query == {'force': 'true'}
    assert run(monkeypatch, name='Home', state='absent')['changed'] is False


def test_update_without_passphrase_fails_when_the_api_hides_it(fake, monkeypatch):
    existing(fake)
    with pytest.raises(AnsibleFail, match='security.passphrase is required to update'):
        run(monkeypatch, name='Home', hide_name=True)
    assert fake.writes == []


def test_update_with_passphrase_sends_it_without_reporting_it(fake, monkeypatch):
    existing(fake)
    result = run(monkeypatch, name='Home', hide_name=True, security={'passphrase': PASSPHRASE}, diff=True)
    assert result['changed'] is True
    assert fake.writes[0].body['securityConfiguration']['passphrase'] == PASSPHRASE
    assert_no_secret(result)
