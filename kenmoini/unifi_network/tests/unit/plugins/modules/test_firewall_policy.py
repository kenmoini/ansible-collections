# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.modules import firewall_policy
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.fake_unifi import FakeUnifi
from ansible_collections.kenmoini.unifi_network.tests.unit.plugins.utils import AnsibleFail, run_module


@pytest.fixture
def fake(monkeypatch):
    f = FakeUnifi().install(monkeypatch)
    f.internal = f.add_site('firewall/zones', {'name': 'Internal', 'networkIds': []})
    f.external = f.add_site('firewall/zones', {'name': 'External', 'networkIds': []})
    f.iot = f.add_site('networks', {'name': 'IoT'})
    f.lan = f.add_site('networks', {'name': 'LAN'})
    f.web_ports = f.add_site('traffic-matching-lists', {'name': 'Web Ports', 'type': 'PORTS'})
    f.blocklist = f.add_site('traffic-matching-lists', {'name': 'Blocklist', 'type': 'IPV4_ADDRESSES'})
    f.wireguard = f.add_site('vpn/servers', {'name': 'WireGuard'})
    f.hq = f.add_site('vpn/site-to-site-tunnels', {'name': 'HQ'})
    return f


def run(monkeypatch, check_mode=False, diff=False, **args):
    return run_module(firewall_policy.main, args, monkeypatch, check_mode=check_mode, diff=diff)


def network_source(fake, *networks, **extra):
    tf = {'type': 'NETWORK', 'networkFilter': {'networkIds': [n['id'] for n in networks], 'matchOpposite': False}}
    tf.update(extra)
    return {'zoneId': fake.internal['id'], 'trafficFilter': tf}


def existing(fake, **overrides):
    obj = {
        'name': 'IoT to web', 'enabled': True, 'index': 10000, 'loggingEnabled': False, 'reportFlowEnabled': True,
        'action': {'type': 'ALLOW', 'allowReturnTraffic': True},
        'source': network_source(fake, fake.iot),
        'destination': {'zoneId': fake.external['id'], 'trafficFilter': {
            'type': 'PORT', 'portFilter': {'type': 'PORTS', 'matchOpposite': False,
                                           'items': [{'type': 'PORT_NUMBER', 'value': 443}]}}},
        'ipProtocolScope': {'ipVersion': 'IPV4_AND_IPV6', 'protocolFilter': {
            'type': 'NAMED_PROTOCOL', 'matchOpposite': False, 'protocol': {'name': 'TCP'}}},
        'metadata': {'origin': 'USER_DEFINED'},
    }
    obj.update(overrides)
    return fake.add_site('firewall/policies', obj)


def without_read_only(obj):
    return dict((k, copy.deepcopy(v)) for k, v in obj.items() if k not in ('id', 'metadata', 'index'))


# ---- create / idempotency / update ----------------------------------------

def test_create_with_zone_names_network_source_and_port_destination(fake, monkeypatch):
    result = run(monkeypatch, name='IoT to web', action='allow',
                 source={'zone': 'Internal', 'networks': ['IoT']},
                 destination={'zone': 'External', 'ports': [443, '8000-8100']},
                 protocol={'name': 'tcp'})
    assert result['changed'] is True
    assert [c.method for c in fake.writes] == ['POST']
    assert fake.writes[0].body == {
        'name': 'IoT to web', 'enabled': True, 'loggingEnabled': False,
        'action': {'type': 'ALLOW', 'allowReturnTraffic': True},
        'source': {'zoneId': fake.internal['id'], 'trafficFilter': {
            'type': 'NETWORK', 'networkFilter': {'networkIds': [fake.iot['id']], 'matchOpposite': False}}},
        'destination': {'zoneId': fake.external['id'], 'trafficFilter': {
            'type': 'PORT', 'portFilter': {'type': 'PORTS', 'matchOpposite': False, 'items': [
                {'type': 'PORT_NUMBER', 'value': 443}, {'type': 'PORT_NUMBER_RANGE', 'start': 8000, 'stop': 8100}]}}},
        'ipProtocolScope': {'ipVersion': 'IPV4_AND_IPV6', 'protocolFilter': {
            'type': 'NAMED_PROTOCOL', 'matchOpposite': False, 'protocol': {'name': 'TCP'}}},
    }
    assert result['firewall_policy']['name'] == 'IoT to web'
    assert result['firewall_policy']['id']


def test_rerun_is_idempotent(fake, monkeypatch):
    args = dict(name='IoT to web', action='allow', source={'zone': 'Internal', 'networks': ['IoT']},
                destination={'zone': 'External', 'ports': ['8000-8100', 443]}, protocol={'name': 'tcp'},
                connection_states=['new', 'established'], schedule={'mode': 'every_week', 'days': ['mon', 'tue']})
    assert run(monkeypatch, **args)['changed'] is True
    assert run(monkeypatch, **args)['changed'] is False
    assert len(fake.writes) == 1


def test_update_one_field_keeps_everything_else(fake, monkeypatch):
    policy = existing(fake)
    result = run(monkeypatch, name='IoT to web', logging_enabled=True, diff=True)
    assert result['changed'] is True
    put = fake.writes[0]
    assert put.method == 'PUT' and put.path.endswith('/firewall/policies/%s' % policy['id'])
    expected = without_read_only(policy)
    expected['loggingEnabled'] = True
    assert put.body == expected
    assert result['diff']['before']['loggingEnabled'] is False
    assert result['diff']['after']['loggingEnabled'] is True


def test_rename_by_id(fake, monkeypatch):
    policy = existing(fake)
    run(monkeypatch, id=policy['id'], name='Renamed')
    assert fake.writes[0].body['name'] == 'Renamed'


def test_description_set_and_removed(fake, monkeypatch):
    existing(fake, description='old')
    run(monkeypatch, name='IoT to web', description='')
    assert 'description' not in fake.writes[0].body
    assert run(monkeypatch, name='IoT to web', description='')['changed'] is False


def test_create_requires_name_action_and_zones(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match=r'requires: action, destination\.zone, source\.zone'):
        run(monkeypatch, name='New', source={'networks': ['IoT']})
    assert fake.writes == []


def test_requires_name_or_id(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='one of the following is required'):
        run(monkeypatch, action='allow')


def test_connection_states_and_ipsec(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', connection_states=['new', 'established'], ipsec='match_encrypted')
    body = fake.writes[0].body
    assert sorted(body['connectionStateFilter']) == ['ESTABLISHED', 'NEW']
    assert body['ipsecFilter'] == 'MATCH_ENCRYPTED'
    run(monkeypatch, name='IoT to web', connection_states=[], ipsec='any')
    assert 'connectionStateFilter' not in fake.writes[1].body and 'ipsecFilter' not in fake.writes[1].body
    assert run(monkeypatch, name='IoT to web', connection_states=[], ipsec='any')['changed'] is False


# ---- source / destination traffic filters ---------------------------------

def test_changing_source_filter_type_replaces_sub_object(fake, monkeypatch):
    existing(fake, source=network_source(fake, fake.iot, macAddressFilter='aa:bb:cc:dd:ee:ff', portFilter={
        'type': 'PORTS', 'matchOpposite': False, 'items': [{'type': 'PORT_NUMBER', 'value': 53}]}))
    run(monkeypatch, name='IoT to web', source={'zone': 'Internal', 'ip_addresses': ['10.0.0.0/24']})
    assert fake.writes[0].body['source'] == {'zoneId': fake.internal['id'], 'trafficFilter': {
        'type': 'IP_ADDRESS', 'ipAddressFilter': {'type': 'IP_ADDRESSES', 'matchOpposite': False,
                                                  'items': [{'type': 'SUBNET', 'value': '10.0.0.0/24'}]}}}


def test_same_filter_type_drops_omitted_ports_and_mac(fake, monkeypatch):
    existing(fake, source=network_source(fake, fake.iot, macAddressFilter='aa:bb:cc:dd:ee:ff', portFilter={
        'type': 'PORTS', 'matchOpposite': False, 'items': [{'type': 'PORT_NUMBER', 'value': 53}]}))
    run(monkeypatch, name='IoT to web', source={'networks': ['IoT', 'LAN']})
    assert fake.writes[0].body['source'] == network_source(fake, fake.iot, fake.lan)


def test_source_without_criteria_matches_any(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', source={'zone': 'Internal'})
    assert fake.writes[0].body['source'] == {'zoneId': fake.internal['id']}
    assert run(monkeypatch, name='IoT to web', source={'zone': 'Internal'})['changed'] is False


def test_ip_addresses_v4_v6_subnets_and_ranges(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', destination={'match_opposite': True, 'ip_addresses': [
        '10.0.0.1', '10.0.0.0/24', '10.0.0.10-10.0.0.20', '2001:db8::1', '2001:db8::/64', '2001:db8::10-2001:db8::20']})
    dest = fake.writes[0].body['destination']
    assert dest['zoneId'] == fake.external['id']
    assert dest['trafficFilter'] == {'type': 'IP_ADDRESS', 'ipAddressFilter': {
        'type': 'IP_ADDRESSES', 'matchOpposite': True, 'items': [
            {'type': 'IP_ADDRESS', 'value': '10.0.0.1'},
            {'type': 'SUBNET', 'value': '10.0.0.0/24'},
            {'type': 'IP_ADDRESS_RANGE', 'start': '10.0.0.10', 'stop': '10.0.0.20'},
            {'type': 'IP_ADDRESS', 'value': '2001:db8::1'},
            {'type': 'SUBNET', 'value': '2001:db8::/64'},
            {'type': 'IP_ADDRESS_RANGE', 'start': '2001:db8::10', 'stop': '2001:db8::20'}]}}


def test_invalid_ip_address_fails(fake, monkeypatch):
    existing(fake)
    with pytest.raises(AnsibleFail, match='not a valid IP'):
        run(monkeypatch, name='IoT to web', destination={'ip_addresses': ['10.0.0.300']})


def test_traffic_matching_lists_by_name(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', source={'ip_address_list': 'Blocklist', 'match_opposite': True},
        destination={'port_list': 'Web Ports', 'ports_match_opposite': True})
    body = fake.writes[0].body
    assert body['source']['trafficFilter'] == {'type': 'IP_ADDRESS', 'ipAddressFilter': {
        'type': 'TRAFFIC_MATCHING_LIST', 'trafficMatchingListId': fake.blocklist['id'], 'matchOpposite': True}}
    assert body['destination']['trafficFilter'] == {'type': 'PORT', 'portFilter': {
        'type': 'TRAFFIC_MATCHING_LIST', 'trafficMatchingListId': fake.web_ports['id'], 'matchOpposite': True}}


def test_source_mac_address_with_network_and_ports(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', source={'networks': ['IoT'], 'mac_address': 'AA-BB-CC-DD-EE-FF',
                                                'ports': ['1024-65535']})
    assert fake.writes[0].body['source']['trafficFilter'] == {
        'type': 'NETWORK', 'networkFilter': {'networkIds': [fake.iot['id']], 'matchOpposite': False},
        'macAddressFilter': 'aa:bb:cc:dd:ee:ff',
        'portFilter': {'type': 'PORTS', 'matchOpposite': False,
                       'items': [{'type': 'PORT_NUMBER_RANGE', 'start': 1024, 'stop': 65535}]}}


def test_source_mac_addresses_regions_vpn_and_tunnel(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', source={'mac_addresses': ['AA:BB:CC:DD:EE:01']})
    assert fake.writes[-1].body['source']['trafficFilter'] == {
        'type': 'MAC_ADDRESS', 'macAddressFilter': {'macAddresses': ['aa:bb:cc:dd:ee:01']}}
    run(monkeypatch, name='IoT to web', source={'regions': ['cn', 'RU']})
    assert fake.writes[-1].body['source']['trafficFilter'] == {'type': 'REGION', 'regionFilter': {'regions': ['CN', 'RU']}}
    run(monkeypatch, name='IoT to web', source={'vpn_servers': ['WireGuard'], 'match_opposite': True})
    assert fake.writes[-1].body['source']['trafficFilter'] == {
        'type': 'VPN_SERVER', 'vpnServerFilter': {'vpnServerIds': [fake.wireguard['id']], 'matchOpposite': True}}
    run(monkeypatch, name='IoT to web', source={'site_to_site_tunnel': 'HQ'})
    assert fake.writes[-1].body['source']['trafficFilter'] == {
        'type': 'SITE_TO_SITE_VPN_TUNNEL', 'siteToSiteVpnTunnelFilter': {'siteToSiteVpnTunnelId': fake.hq['id']}}
    run(monkeypatch, name='IoT to web', source={'ipv6_iid': '::1234:5678', 'mac_address': 'aa:bb:cc:dd:ee:02'})
    assert fake.writes[-1].body['source']['trafficFilter'] == {
        'type': 'IPV6_IID', 'ipv6IidFilter': {'ipv6Iid': '::1234:5678', 'matchOpposite': False},
        'macAddressFilter': 'aa:bb:cc:dd:ee:02'}


def test_destination_only_criteria(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', destination={'applications': [1, 2], 'ports': [443]})
    assert fake.writes[-1].body['destination']['trafficFilter'] == {
        'type': 'APPLICATION', 'applicationFilter': {'applicationIds': [1, 2]},
        'portFilter': {'type': 'PORTS', 'matchOpposite': False, 'items': [{'type': 'PORT_NUMBER', 'value': 443}]}}
    run(monkeypatch, name='IoT to web', destination={'application_categories': [5]})
    assert fake.writes[-1].body['destination']['trafficFilter'] == {
        'type': 'APPLICATION_CATEGORY', 'applicationCategoryFilter': {'applicationCategoryIds': [5]}}
    run(monkeypatch, name='IoT to web', destination={'domains': ['example.com', 'example.org']})
    assert fake.writes[-1].body['destination']['trafficFilter'] == {
        'type': 'DOMAIN', 'domainFilter': {'type': 'DOMAINS', 'domains': ['example.com', 'example.org']}}


def test_conflicting_criteria_fail(fake, monkeypatch):
    existing(fake)
    with pytest.raises(AnsibleFail, match='source can match on only one of.*got networks and ip_addresses'):
        run(monkeypatch, name='IoT to web', source={'networks': ['IoT'], 'ip_addresses': ['10.0.0.1']})
    assert fake.writes == []


def test_ports_and_port_list_conflict(fake, monkeypatch):
    existing(fake)
    with pytest.raises(AnsibleFail, match='mutually exclusive'):
        run(monkeypatch, name='IoT to web', destination={'ports': [443], 'port_list': 'Web Ports'})


@pytest.mark.parametrize('side, option, value', [
    ('destination', 'mac_addresses', ['aa:bb:cc:dd:ee:ff']),
    ('destination', 'mac_address', 'aa:bb:cc:dd:ee:ff'),
    ('source', 'domains', ['example.com']),
    ('source', 'applications', [1]),
    ('source', 'application_categories', [1]),
])
def test_side_specific_options_rejected(fake, monkeypatch, side, option, value):
    existing(fake)
    with pytest.raises(AnsibleFail, match=r'Unsupported parameters.*: %s\.%s\.' % (side, option)):
        run(monkeypatch, name='IoT to web', **{side: {option: value}})
    assert fake.writes == []


@pytest.mark.parametrize('side, spec, message', [
    ('source', {'regions': ['US'], 'match_opposite': True}, 'match_opposite is not supported with regions'),
    ('source', {'match_opposite': True}, 'match_opposite'),
    ('source', {'regions': ['US'], 'mac_address': 'aa:bb:cc:dd:ee:ff'}, 'mac_address'),
    ('source', {'mac_address': 'aa:bb:cc:dd:ee:ff'}, 'mac_address'),
    ('destination', {'ports_match_opposite': True}, 'ports_match_opposite'),
    ('destination', {'networks': []}, 'must not be empty'),
    ('destination', {'ports': []}, 'must not be empty'),
])
def test_invalid_side_combinations(fake, monkeypatch, side, spec, message):
    existing(fake)
    with pytest.raises(AnsibleFail, match=message):
        run(monkeypatch, name='IoT to web', **{side: spec})
    assert fake.writes == []


def test_unknown_reference_fails_before_writing(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match="No network named 'Nope'"):
        run(monkeypatch, name='X', action='block', source={'zone': 'Internal', 'networks': ['Nope']},
            destination={'zone': 'External'})
    assert fake.writes == []


# ---- action ---------------------------------------------------------------

def test_allow_return_traffic_defaults_true_on_new_allow(fake, monkeypatch):
    existing(fake, action={'type': 'BLOCK'})
    run(monkeypatch, name='IoT to web', action='allow')
    assert fake.writes[0].body['action'] == {'type': 'ALLOW', 'allowReturnTraffic': True}


def test_allow_keeps_existing_return_traffic_setting(fake, monkeypatch):
    existing(fake, action={'type': 'ALLOW', 'allowReturnTraffic': False})
    assert run(monkeypatch, name='IoT to web', action='allow')['changed'] is False
    run(monkeypatch, name='IoT to web', allow_return_traffic=True)
    assert fake.writes[0].body['action'] == {'type': 'ALLOW', 'allowReturnTraffic': True}


def test_switch_to_block_drops_return_traffic(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', action='reject')
    assert fake.writes[0].body['action'] == {'type': 'REJECT'}


def test_allow_return_traffic_only_with_allow(fake, monkeypatch):
    with pytest.raises(AnsibleFail, match='allow_return_traffic is only valid with action allow'):
        run(monkeypatch, name='X', action='block', allow_return_traffic=False,
            source={'zone': 'Internal'}, destination={'zone': 'External'})
    existing(fake, action={'type': 'BLOCK'})
    with pytest.raises(AnsibleFail, match='allow_return_traffic is only valid with action allow'):
        run(monkeypatch, name='IoT to web', allow_return_traffic=True)


# ---- protocol / IP version ------------------------------------------------

@pytest.mark.parametrize('args, expected', [
    (dict(protocol={'name': 'tcp_udp'}),
     {'ipVersion': 'IPV4_AND_IPV6', 'protocolFilter': {'type': 'PRESET', 'preset': {'name': 'TCP_UDP'}}}),
    (dict(protocol={'name': 'gre', 'match_opposite': True}),
     {'ipVersion': 'IPV4_AND_IPV6', 'protocolFilter': {'type': 'NAMED_PROTOCOL', 'matchOpposite': True,
                                                       'protocol': {'name': 'GRE'}}}),
    (dict(protocol={'number': 47}),
     {'ipVersion': 'IPV4_AND_IPV6', 'protocolFilter': {'type': 'PROTOCOL_NUMBER', 'protocolNumber': 47,
                                                       'matchOpposite': False}}),
    (dict(ip_version='ipv4', protocol={'name': 'icmp', 'icmp_type': 'echo-request'}),
     {'ipVersion': 'IPV4', 'protocolFilter': {'type': 'NAMED_PROTOCOL', 'matchOpposite': False,
                                              'protocol': {'name': 'ICMP', 'typenameFilter': 'ECHO_REQUEST'}}}),
    (dict(ip_version='ipv6', protocol={'name': 'ipv6-frag'}),
     {'ipVersion': 'IPV6', 'protocolFilter': {'type': 'NAMED_PROTOCOL', 'matchOpposite': False,
                                              'protocol': {'name': 'IPV6_FRAG'}}}),
    (dict(ip_version='ipv4', protocol={'name': 'any'}), {'ipVersion': 'IPV4'}),
    (dict(ip_version='ipv6'), {'ipVersion': 'IPV6'}),
    (dict(), {'ipVersion': 'IPV4_AND_IPV6'}),
])
def test_protocol_on_create(fake, monkeypatch, args, expected):
    run(monkeypatch, name='P', action='block', source={'zone': 'Internal'}, destination={'zone': 'External'}, **args)
    assert fake.writes[0].body['ipProtocolScope'] == expected


def test_protocol_any_removes_filter(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', protocol={'name': 'any'})
    assert fake.writes[0].body['ipProtocolScope'] == {'ipVersion': 'IPV4_AND_IPV6'}
    assert run(monkeypatch, name='IoT to web', protocol={'name': 'any'})['changed'] is False


def test_protocol_change_keeps_current_ip_version_and_drops_icmp_type(fake, monkeypatch):
    existing(fake, ipProtocolScope={'ipVersion': 'IPV4', 'protocolFilter': {
        'type': 'NAMED_PROTOCOL', 'matchOpposite': False, 'protocol': {'name': 'ICMP', 'typenameFilter': 'ECHO_REQUEST'}}})
    run(monkeypatch, name='IoT to web', protocol={'name': 'udp'})
    assert fake.writes[0].body['ipProtocolScope'] == {'ipVersion': 'IPV4', 'protocolFilter': {
        'type': 'NAMED_PROTOCOL', 'matchOpposite': False, 'protocol': {'name': 'UDP'}}}


def test_ip_version_change_keeps_compatible_protocol(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', ip_version='ipv4')
    assert fake.writes[0].body['ipProtocolScope'] == {'ipVersion': 'IPV4', 'protocolFilter': {
        'type': 'NAMED_PROTOCOL', 'matchOpposite': False, 'protocol': {'name': 'TCP'}}}


def test_ip_version_change_with_incompatible_protocol_fails(fake, monkeypatch):
    existing(fake, ipProtocolScope={'ipVersion': 'IPV4', 'protocolFilter': {
        'type': 'NAMED_PROTOCOL', 'matchOpposite': False, 'protocol': {'name': 'ICMP'}}})
    with pytest.raises(AnsibleFail, match='ICMP.*not valid with ip_version ipv6'):
        run(monkeypatch, name='IoT to web', ip_version='ipv6')


@pytest.mark.parametrize('args, message', [
    (dict(protocol={'name': 'icmp'}), 'not valid with ip_version ipv4_and_ipv6'),
    (dict(ip_version='ipv6', protocol={'name': 'icmp'}), 'not valid with ip_version ipv6'),
    (dict(protocol={'name': 'tcp', 'icmp_type': 'echo_request'}), 'icmp_type is only valid with'),
    (dict(ip_version='ipv4', protocol={'name': 'icmp', 'icmp_type': 'bogus'}), 'not a valid ICMP type'),
    (dict(protocol={'name': 'tcp_udp', 'match_opposite': True}), 'match_opposite is not supported with tcp_udp'),
    (dict(protocol={'name': 'tcp', 'number': 6}), 'mutually exclusive'),
    (dict(protocol={'number': 256}), '0 to 255'),
    (dict(protocol={'match_opposite': True}), 'one of the following is required'),
])
def test_invalid_protocols(fake, monkeypatch, args, message):
    with pytest.raises(AnsibleFail, match=message):
        run(monkeypatch, name='P', action='block', source={'zone': 'Internal'}, destination={'zone': 'External'}, **args)
    assert fake.writes == []


# ---- schedule -------------------------------------------------------------

def test_schedule_every_week_then_always(fake, monkeypatch):
    existing(fake)
    run(monkeypatch, name='IoT to web', schedule={'mode': 'every_week', 'days': ['friday', 'mon'],
                                                  'start_time': '8:00', 'stop_time': 1050})
    assert fake.writes[0].body['schedule'] == {
        'mode': 'EVERY_WEEK', 'repeatOnDays': ['MONDAY', 'FRIDAY'],
        'timeFilter': {'startTime': '08:00', 'stopTime': '17:30'}}
    run(monkeypatch, name='IoT to web', schedule={'mode': 'every_week', 'days': ['mon', 'fri']})
    assert fake.writes[1].body['schedule'] == {'mode': 'EVERY_WEEK', 'repeatOnDays': ['MONDAY', 'FRIDAY']}
    run(monkeypatch, name='IoT to web', schedule={'mode': 'always'})
    assert 'schedule' not in fake.writes[2].body
    assert run(monkeypatch, name='IoT to web', schedule={'mode': 'always'})['changed'] is False


@pytest.mark.parametrize('schedule, expected', [
    ({'mode': 'every_day', 'start_time': '22:00', 'stop_time': '06:00'},
     {'mode': 'EVERY_DAY', 'timeFilter': {'startTime': '22:00', 'stopTime': '06:00'}}),
    ({'mode': 'one_time_only', 'date': '2026-12-24', 'start_time': '18:00', 'stop_time': '23:59'},
     {'mode': 'ONE_TIME_ONLY', 'date': '2026-12-24', 'timeFilter': {'startTime': '18:00', 'stopTime': '23:59'}}),
    ({'mode': 'custom', 'days': ['sat', 'sun'], 'start_date': '2026-06-01', 'stop_date': '2026-08-31'},
     {'mode': 'CUSTOM', 'repeatOnDays': ['SATURDAY', 'SUNDAY'], 'startDate': '2026-06-01', 'stopDate': '2026-08-31'}),
])
def test_schedule_modes(fake, monkeypatch, schedule, expected):
    run(monkeypatch, name='S', action='block', source={'zone': 'Internal'}, destination={'zone': 'External'},
        schedule=schedule)
    assert fake.writes[0].body['schedule'] == expected


@pytest.mark.parametrize('schedule, message', [
    ({'mode': 'every_day'}, 'every_day requires: start_time, stop_time'),
    ({'mode': 'every_week'}, 'every_week requires: days'),
    ({'mode': 'one_time_only', 'start_time': '10:00', 'stop_time': '11:00'}, 'one_time_only requires: date'),
    ({'mode': 'custom', 'days': ['mon']}, 'custom requires: start_date, stop_date'),
    ({'mode': 'every_day', 'days': ['mon'], 'start_time': '10:00', 'stop_time': '11:00'}, 'days.*not valid with mode every_day'),
    ({'mode': 'always', 'start_time': '10:00'}, 'start_time.*not valid with mode always'),
    ({'mode': 'every_week', 'days': ['mon'], 'start_time': '10:00'}, 'start_time and schedule.stop_time'),
    ({'mode': 'every_day', 'start_time': '25:00', 'stop_time': '11:00'}, 'HH:MM'),
    ({'mode': 'one_time_only', 'date': '24/12/2026', 'start_time': '10:00', 'stop_time': '11:00'}, 'YYYY-MM-DD'),
])
def test_invalid_schedules(fake, monkeypatch, schedule, message):
    with pytest.raises(AnsibleFail, match=message):
        run(monkeypatch, name='S', action='block', source={'zone': 'Internal'}, destination={'zone': 'External'},
            schedule=schedule)
    assert fake.writes == []


# ---- system-defined / derived ---------------------------------------------

def test_system_defined_logging_change_uses_patch(fake, monkeypatch):
    policy = existing(fake, name='Block Invalid Traffic', action={'type': 'BLOCK'},
                      metadata={'origin': 'SYSTEM_DEFINED'})
    result = run(monkeypatch, name='Block Invalid Traffic', logging_enabled=True, report_flow_enabled=False,
                 action='block', enabled=True)
    assert result['changed'] is True
    assert [(c.method, c.body) for c in fake.writes] == [('PATCH', {'loggingEnabled': True, 'reportFlowEnabled': False})]
    assert fake.writes[0].path.endswith(policy['id'])
    assert result['firewall_policy']['loggingEnabled'] is True


def test_system_defined_other_changes_refused(fake, monkeypatch):
    existing(fake, name='Block Invalid Traffic', action={'type': 'BLOCK'}, metadata={'origin': 'SYSTEM_DEFINED'})
    with pytest.raises(AnsibleFail, match='system-defined.*only logging_enabled and report_flow_enabled.*action, enabled'):
        run(monkeypatch, name='Block Invalid Traffic', action='allow', enabled=False, logging_enabled=True)
    assert fake.writes == []


def test_system_defined_cannot_be_deleted(fake, monkeypatch):
    existing(fake, name='Block Invalid Traffic', metadata={'origin': 'SYSTEM_DEFINED'})
    with pytest.raises(AnsibleFail, match='system-defined.*cannot be deleted'):
        run(monkeypatch, name='Block Invalid Traffic', state='absent')
    assert fake.writes == []


def test_derived_policy_cannot_be_changed_or_deleted(fake, monkeypatch):
    existing(fake, name='Allow Return Traffic', metadata={'origin': 'DERIVED'})
    with pytest.raises(AnsibleFail, match='derived'):
        run(monkeypatch, name='Allow Return Traffic', logging_enabled=True)
    with pytest.raises(AnsibleFail, match='derived'):
        run(monkeypatch, name='Allow Return Traffic', state='absent')
    assert fake.writes == []


# ---- check mode / diff / absent -------------------------------------------

def test_check_mode_create_predicts_without_writing(fake, monkeypatch):
    result = run(monkeypatch, check_mode=True, diff=True, name='New', action='block',
                 source={'zone': 'Internal'}, destination={'zone': 'External', 'regions': ['CN']})
    assert result['changed'] is True
    assert fake.writes == []
    assert result['firewall_policy']['action'] == {'type': 'BLOCK'}
    assert result['diff']['before'] == {}
    assert result['diff']['after']['destination']['trafficFilter']['type'] == 'REGION'


def test_check_mode_update_diff(fake, monkeypatch):
    existing(fake)
    result = run(monkeypatch, check_mode=True, diff=True, name='IoT to web',
                 destination={'zone': 'External', 'ports': [80]})
    assert result['changed'] is True
    assert fake.writes == []
    assert result['diff']['before']['destination']['trafficFilter']['portFilter']['items'] == [
        {'type': 'PORT_NUMBER', 'value': 443}]
    assert result['diff']['after']['destination']['trafficFilter']['portFilter']['items'] == [
        {'type': 'PORT_NUMBER', 'value': 80}]


def test_absent_then_absent(fake, monkeypatch):
    existing(fake)
    assert run(monkeypatch, name='IoT to web', state='absent')['changed'] is True
    assert fake.writes[0].method == 'DELETE'
    result = run(monkeypatch, name='IoT to web', state='absent')
    assert result['changed'] is False
    assert len(fake.writes) == 1


def test_absent_check_mode(fake, monkeypatch):
    existing(fake)
    assert run(monkeypatch, check_mode=True, name='IoT to web', state='absent')['changed'] is True
    assert fake.writes == []


def test_duplicate_names_require_id(fake, monkeypatch):
    existing(fake)
    existing(fake)
    with pytest.raises(AnsibleFail, match='More than one firewall policy named'):
        run(monkeypatch, name='IoT to web', enabled=False)
