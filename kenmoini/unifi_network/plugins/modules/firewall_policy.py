#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: firewall_policy
short_description: Manage zone-based firewall policies in UniFi Network
version_added: "2.0.0"
description:
  - Creates, updates or deletes firewall policies, which allow, block or reject traffic going from a source firewall zone
    to a destination firewall zone, optionally narrowed down by networks, addresses, ports, protocol, schedule and more.
  - The policy is found by O(name), or by O(id) when given (which also allows renaming it). When several policies share
    a name, set O(id) to choose one.
  - Only the options you set are managed. The module reads the policy first, merges your options into it and only writes
    when something differs, so settings made in the UniFi UI that you do not set are kept.
  - O(source), O(destination), O(protocol) and O(schedule) each describe one complete setting. For example, the traffic
    filter of O(source) is rebuilt from the suboptions you give, so a criterion you leave out is removed.
  - System-defined policies cannot be created or deleted, and only their O(logging_enabled) and O(report_flow_enabled)
    can change. Derived policies (such as the return-traffic policies created by O(allow_return_traffic)) cannot be
    changed or deleted; change the policy they are derived from instead.
  - Use M(kenmoini.unifi_network.firewall_policy_ordering) to set the order in which policies are evaluated.
options:
  name:
    description:
      - Name of the firewall policy. Used to find the policy when O(id) is not set.
      - Required unless O(id) is set.
    type: str
  id:
    description:
      - UUID of an existing firewall policy to manage. When set, O(name) renames the policy.
    type: str
  state:
    description:
      - V(present) creates or updates the policy, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  enabled:
    description:
      - Whether the policy is active. New policies are enabled unless this is V(false).
    type: bool
  description:
    description:
      - Free-text description of the policy. An empty string removes it.
    type: str
  action:
    description:
      - What happens to matched traffic. Required when creating a policy.
      - V(block) silently drops the traffic, V(reject) drops it and tells the sender.
    type: str
    choices: [allow, block, reject]
  allow_return_traffic:
    description:
      - Also allow the return traffic, by creating a derived policy for the mirrored zone pair. Only with O(action=allow).
      - Defaults to V(true) when a policy becomes V(allow); otherwise the current setting is kept.
    type: bool
  logging_enabled:
    description:
      - Send a syslog entry to the remote syslog server whenever traffic matches. New policies do not log unless this is V(true).
    type: bool
  report_flow_enabled:
    description:
      - Report matched traffic in Insights Flows. The UniFi Network application enables this for new policies unless this is V(false).
    type: bool
  connection_states:
    description:
      - Only match traffic in these connection states.
      - An empty list matches every connection state, which is also the default for new policies.
    type: list
    elements: str
    choices: [new, invalid, established, related]
    aliases: [connection_state_filter]
  ipsec:
    description:
      - Match traffic by IPsec encryption. V(match_encrypted) only matches IPsec-encrypted traffic, V(match_not_encrypted)
        only matches unencrypted traffic and V(any) matches both, which is the default for new policies.
    type: str
    choices: [match_encrypted, match_not_encrypted, any]
    aliases: [ipsec_filter]
  ip_version:
    description:
      - The IP versions the policy matches. New policies match V(ipv4_and_ipv6).
      - When the version changes and O(protocol) is not set, the current protocol is kept if it is valid for the new version.
    type: str
    choices: [ipv4, ipv6, ipv4_and_ipv6]
  protocol:
    description:
      - The protocol to match. Omit to keep the current protocol; new policies match every protocol.
      - Set exactly one of O(protocol.name) and O(protocol.number).
    type: dict
    suboptions:
      name:
        description:
          - IANA protocol name, such as V(tcp), V(udp), V(gre), V(esp), V(icmp) (only with O(ip_version=ipv4)) or
            V(icmpv6) (only with O(ip_version=ipv6)). The name is case-insensitive.
          - V(tcp_udp) matches both TCP and UDP. V(any) matches every protocol, removing the protocol filter.
          - Which names are valid depends on O(ip_version). With V(ipv4_and_ipv6) only V(ah), V(dccp), V(eigrp), V(esp),
            V(gre), V(ipcomp), V(isis), V(l2tp), V(manet), V(mobility-header), V(mpls-in-ip), V(ospf), V(pim), V(rsvp),
            V(sctp), V(shim6), V(tcp), V(udp) and V(vrrp) are valid.
        type: str
      number:
        description:
          - IANA protocol number, from 0 to 255.
        type: int
      match_opposite:
        description:
          - Match every protocol except this one. Not valid with V(tcp_udp) or V(any).
        type: bool
        default: false
      icmp_type:
        description:
          - Only match this ICMP or ICMPv6 message type, for example V(echo_request) or V(destination_unreachable).
            Only with O(protocol.name=icmp) and O(protocol.name=icmpv6). Omit to match every type.
        type: str
  source:
    description:
      - Where the matched traffic comes from. Required when creating a policy, with at least O(source.zone).
      - The traffic filter is rebuilt from the suboptions you give. With no criterion the policy matches all traffic from the zone.
      - Set at most one main criterion, which is one of O(source.networks), O(source.ip_addresses), O(source.ip_address_list),
        O(source.mac_addresses), O(source.ipv6_iid), O(source.regions), O(source.vpn_servers) and O(source.site_to_site_tunnel).
        Ports (O(source.ports) or O(source.port_list)) can be combined with any of them, or used alone.
    type: dict
    suboptions:
      zone:
        description:
          - Firewall zone the traffic comes from, given as its name or UUID. Required when creating a policy; kept when omitted.
        type: str
        aliases: [zone_id]
      networks:
        description:
          - Match traffic from these Networks, given as names or UUIDs.
        type: list
        elements: str
        aliases: [network_ids]
      ip_addresses:
        description:
          - Match traffic from these IPv4 or IPv6 addresses, subnets (V(10.0.0.0/24)) or ranges (V(10.0.0.10-10.0.0.20)).
        type: list
        elements: str
      ip_address_list:
        description:
          - Match traffic from the addresses in this IPv4 or IPv6 address traffic matching list, given as its name or UUID.
        type: str
        aliases: [ip_address_traffic_matching_list]
      mac_addresses:
        description:
          - Match traffic from these MAC addresses.
        type: list
        elements: str
      ipv6_iid:
        description:
          - Match traffic from this IPv6 interface identifier (the host part of an IPv6 address), for example V(::1234:5678).
        type: str
        aliases: [ipv6_interface_identifier]
      regions:
        description:
          - Match traffic from these regions, given as ISO 3166-1 alpha-2 country codes such as V(US).
        type: list
        elements: str
      vpn_servers:
        description:
          - Match traffic from the clients of these VPN servers, given as names or UUIDs.
        type: list
        elements: str
        aliases: [vpn_server_ids]
      site_to_site_tunnel:
        description:
          - Match traffic from this site-to-site VPN tunnel, given as its name or UUID.
        type: str
        aliases: [site_to_site_vpn_tunnel]
      match_opposite:
        description:
          - Match all traffic except what the main criterion selects.
          - Only with O(source.networks), O(source.ip_addresses), O(source.ip_address_list), O(source.ipv6_iid) and O(source.vpn_servers).
        type: bool
        default: false
      mac_address:
        description:
          - Additionally require this source MAC address.
          - Only with O(source.networks), O(source.ip_addresses), O(source.ip_address_list) and O(source.ipv6_iid);
            use O(source.mac_addresses) to match on MAC addresses alone.
        type: str
      ports:
        description:
          - Match traffic from these ports or port ranges, for example V(53) or V(8000-8100).
          - Mutually exclusive with O(source.port_list).
        type: list
        elements: raw
      port_list:
        description:
          - Match traffic from the ports in this port traffic matching list, given as its name or UUID.
        type: str
        aliases: [port_traffic_matching_list]
      ports_match_opposite:
        description:
          - Match all ports except those in O(source.ports) or O(source.port_list).
        type: bool
        default: false
  destination:
    description:
      - Where the matched traffic goes to. Required when creating a policy, with at least O(destination.zone).
      - The traffic filter is rebuilt from the suboptions you give. With no criterion the policy matches all traffic to the zone.
      - Set at most one main criterion, which is one of O(destination.networks), O(destination.ip_addresses),
        O(destination.ip_address_list), O(destination.ipv6_iid), O(destination.regions), O(destination.vpn_servers),
        O(destination.site_to_site_tunnel), O(destination.applications), O(destination.application_categories) and
        O(destination.domains). Ports (O(destination.ports) or O(destination.port_list)) can be combined with any of them, or used alone.
    type: dict
    suboptions:
      zone:
        description:
          - Firewall zone the traffic goes to, given as its name or UUID. Required when creating a policy; kept when omitted.
        type: str
        aliases: [zone_id]
      networks:
        description:
          - Match traffic to these Networks, given as names or UUIDs.
        type: list
        elements: str
        aliases: [network_ids]
      ip_addresses:
        description:
          - Match traffic to these IPv4 or IPv6 addresses, subnets (V(10.0.0.0/24)) or ranges (V(10.0.0.10-10.0.0.20)).
        type: list
        elements: str
      ip_address_list:
        description:
          - Match traffic to the addresses in this IPv4 or IPv6 address traffic matching list, given as its name or UUID.
        type: str
        aliases: [ip_address_traffic_matching_list]
      ipv6_iid:
        description:
          - Match traffic to this IPv6 interface identifier (the host part of an IPv6 address), for example V(::1234:5678).
        type: str
        aliases: [ipv6_interface_identifier]
      regions:
        description:
          - Match traffic to these regions, given as ISO 3166-1 alpha-2 country codes such as V(US).
        type: list
        elements: str
      vpn_servers:
        description:
          - Match traffic to the clients of these VPN servers, given as names or UUIDs.
        type: list
        elements: str
        aliases: [vpn_server_ids]
      site_to_site_tunnel:
        description:
          - Match traffic into this site-to-site VPN tunnel, given as its name or UUID.
        type: str
        aliases: [site_to_site_vpn_tunnel]
      applications:
        description:
          - Match traffic to these DPI applications, given as their numeric IDs (up to 100).
          - Use M(kenmoini.unifi_network.dpi_application_info) to find the IDs.
        type: list
        elements: int
        aliases: [application_ids]
      application_categories:
        description:
          - Match traffic to these DPI application categories, given as their numeric IDs.
          - Use M(kenmoini.unifi_network.dpi_category_info) to find the IDs.
        type: list
        elements: int
        aliases: [application_category_ids]
      domains:
        description:
          - Match traffic to these domain names.
        type: list
        elements: str
      match_opposite:
        description:
          - Match all traffic except what the main criterion selects.
          - Only with O(destination.networks), O(destination.ip_addresses), O(destination.ip_address_list),
            O(destination.ipv6_iid) and O(destination.vpn_servers).
        type: bool
        default: false
      ports:
        description:
          - Match traffic to these ports or port ranges, for example V(443) or V(8000-8100).
          - Mutually exclusive with O(destination.port_list).
        type: list
        elements: raw
      port_list:
        description:
          - Match traffic to the ports in this port traffic matching list, given as its name or UUID.
        type: str
        aliases: [port_traffic_matching_list]
      ports_match_opposite:
        description:
          - Match all ports except those in O(destination.ports) or O(destination.port_list).
        type: bool
        default: false
  schedule:
    description:
      - When the policy is active. The schedule is replaced as a whole. New policies are always active.
    type: dict
    suboptions:
      mode:
        description:
          - V(always) removes the schedule, so the policy is always active.
          - V(every_day) is active every day between O(schedule.start_time) and O(schedule.stop_time).
          - V(every_week) is active on O(schedule.days), all day or between the start and stop times when given.
          - V(one_time_only) is active on O(schedule.date) between the start and stop times.
          - V(custom) is active on O(schedule.days) from O(schedule.start_date) to O(schedule.stop_date),
            all day or between the start and stop times when given.
        type: str
        required: true
        choices: [always, every_day, every_week, one_time_only, custom]
      start_time:
        description:
          - Start time in 24-hour V(HH:MM) format, for example V("08:00").
          - Required for V(every_day) and V(one_time_only); optional, together with O(schedule.stop_time), for V(every_week) and V(custom).
          - Quote the value. YAML reads an unquoted time such as V(17:30) as a number of minutes, which is converted back.
        type: raw
      stop_time:
        description:
          - Stop time in 24-hour V(HH:MM) format, for example V("17:30").
          - Required for V(every_day) and V(one_time_only); optional, together with O(schedule.start_time), for V(every_week) and V(custom).
        type: raw
      days:
        description:
          - Days of the week the policy is active. Required for V(every_week) and V(custom).
        type: list
        elements: str
        choices: [mon, tue, wed, thu, fri, sat, sun, monday, tuesday, wednesday, thursday, friday, saturday, sunday]
        aliases: [repeat_on_days]
      date:
        description:
          - The day the policy is active, in V(YYYY-MM-DD) format. Required for V(one_time_only).
        type: str
      start_date:
        description:
          - First day the policy is active, in V(YYYY-MM-DD) format. Required for V(custom).
        type: str
      stop_date:
        description:
          - Last day the policy is active, in V(YYYY-MM-DD) format. Required for V(custom).
        type: str
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Allow IoT devices to reach the internet on HTTPS only
  kenmoini.unifi_network.firewall_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: IoT to web
    action: allow
    source:
      zone: Internal
      networks: [IoT]
    destination:
      zone: External
      ports: [443]
    protocol:
      name: tcp

- name: Block a list of addresses from reaching the servers, logging every hit
  kenmoini.unifi_network.firewall_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Block bad actors
    action: block
    logging_enabled: true
    source:
      zone: External
      ip_address_list: Blocklist
    destination:
      zone: Internal
      ip_addresses:
        - 10.20.0.0/24
        - 10.20.1.10-10.20.1.20
        - 2001:db8:20::/64

- name: Let kids' devices reach games only on weekday evenings
  kenmoini.unifi_network.firewall_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Kids gaming
    action: allow
    allow_return_traffic: true
    source:
      zone: Internal
      networks: [Kids]
    destination:
      zone: External
      application_categories: [8]
    schedule:
      mode: every_week
      days: [mon, tue, wed, thu, fri]
      start_time: "18:00"
      stop_time: "20:30"

- name: Reject pings from the guest network to the gateway
  kenmoini.unifi_network.firewall_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: No guest pings
    action: reject
    ip_version: ipv4
    protocol:
      name: icmp
      icmp_type: echo_request
    source:
      zone: Hotspot
    destination:
      zone: Gateway

- name: Turn on logging for a system-defined policy (the only change allowed besides report_flow_enabled)
  kenmoini.unifi_network.firewall_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
    logging_enabled: true

- name: Remove the schedule and match any source in the zone again
  kenmoini.unifi_network.firewall_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Kids gaming
    schedule:
      mode: always
    source:
      zone: Internal

- name: Preview a change without making it (run with --check --diff)
  kenmoini.unifi_network.firewall_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: IoT to web
    destination:
      zone: External
      ports: [443, 8443]
  check_mode: true
  diff: true

- name: Delete a policy
  kenmoini.unifi_network.firewall_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Kids gaming
    state: absent
'''

RETURN = r'''
firewall_policy:
  description:
    - The firewall policy as returned by the API after the change, or the predicted policy in check mode.
    - Empty when O(state=absent).
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "name": "IoT to web", "enabled": true, "index": 10000,
           "action": {"type": "ALLOW", "allowReturnTraffic": true},
           "source": {"zoneId": "7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11",
                      "trafficFilter": {"type": "NETWORK",
                                        "networkFilter": {"networkIds": ["3c2e8f10-4b6a-4c1e-9d2a-0f5b7e9a1c33"], "matchOpposite": false}}},
           "destination": {"zoneId": "1b0e3d7c-9a52-4f6e-8c41-6d2f0a9b8e77",
                           "trafficFilter": {"type": "PORT", "portFilter": {"type": "PORTS", "matchOpposite": false,
                                                                            "items": [{"type": "PORT_NUMBER", "value": 443}]}}},
           "ipProtocolScope": {"ipVersion": "IPV4_AND_IPV6",
                               "protocolFilter": {"type": "NAMED_PROTOCOL", "matchOpposite": false, "protocol": {"name": "TCP"}}},
           "loggingEnabled": false, "reportFlowEnabled": true, "metadata": {"origin": "USER_DEFINED"}}
'''

import datetime
import re

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.convert import (
    parse_ip_item,
    parse_port_item,
    pick,
    upper,
)
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.diff import is_subset
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import (
    StateResource,
    origin_of,
    run_state_module,
)

IP_VERSIONS = {'ipv4': 'IPV4', 'ipv6': 'IPV6', 'ipv4_and_ipv6': 'IPV4_AND_IPV6'}
DEFAULT_IP_VERSION = 'IPV4_AND_IPV6'
IPSEC = {'match_encrypted': 'MATCH_ENCRYPTED', 'match_not_encrypted': 'MATCH_NOT_ENCRYPTED', 'any': None}

# Named protocols the API accepts per IP version (discriminator mappings of the 11.0.97 spec).
_COMMON_PROTOCOLS = ('AH DCCP EIGRP ESP GRE IPCOMP ISIS L2TP MANET MOBILITY_HEADER MPLS_IN_IP OSPF PIM RSVP SCTP SHIM6 '
                     'TCP UDP VRRP')
NAMED_PROTOCOLS = {
    'IPV4_AND_IPV6': frozenset(_COMMON_PROTOCOLS.split()),
    'IPV4': frozenset((_COMMON_PROTOCOLS + ' AX_25 DDP EGP ENCAP ETHERIP FC GGP HIP HMP ICMP IDPR_CMTP IDRP IGMP IGP IP '
                       'IPENCAP IPIP ISO_TP4 PUP RDP ROHC RSPF SKIP ST UDPLITE VMTP WESP XNS_IDP XTP').split()),
    'IPV6': frozenset((_COMMON_PROTOCOLS + ' ICMPV6 IPV6 IPV6_FRAG IPV6_NONXT IPV6_OPTS IPV6_ROUTE').split()),
}
ICMP_TYPES = {
    'ICMP': frozenset((
        'ADDRESS_MASK_REPLY ADDRESS_MASK_REQUEST COMMUNICATION_PROHIBITED DESTINATION_UNREACHABLE ECHO_REPLY ECHO_REQUEST '
        'FRAGMENTATION_NEEDED HOST_PRECEDENCE_VIOLATION HOST_PROHIBITED HOST_REDIRECT HOST_UNKNOWN HOST_UNREACHABLE '
        'IP_HEADER_BAD NETWORK_PROHIBITED NETWORK_REDIRECT NETWORK_UNKNOWN NETWORK_UNREACHABLE PARAMETER_PROBLEM '
        'PORT_UNREACHABLE PRECEDENCE_CUTOFF PROTOCOL_UNREACHABLE REDIRECT REQUIRED_OPTION_MISSING ROUTER_ADVERTISEMENT '
        'ROUTER_SOLICITATION SOURCE_QUENCH SOURCE_ROUTE_FAILED TIME_EXCEEDED TIMESTAMP_REPLY TIMESTAMP_REQUEST '
        'TOS_HOST_REDIRECT TOS_HOST_UNREACHABLE TOS_NETWORK_REDIRECT TOS_NETWORK_UNREACHABLE TTL_ZERO_DURING_REASSEMBLY '
        'TTL_ZERO_DURING_TRANSIT').split()),
    'ICMPV6': frozenset((
        'ADDRESS_UNREACHABLE BAD_HEADER BEYOND_SCOPE COMMUNICATION_PROHIBITED DESTINATION_UNREACHABLE ECHO_REPLY '
        'ECHO_REQUEST FAILED_POLICY NEIGHBOR_ADVERTISEMENT NEIGHBOR_SOLICITATION NO_ROUTE PACKET_TOO_BIG PARAMETER_PROBLEM '
        'PORT_UNREACHABLE REDIRECT REJECT_ROUTE ROUTER_ADVERTISEMENT ROUTER_SOLICITATION TIME_EXCEEDED '
        'TTL_ZERO_DURING_REASSEMBLY TTL_ZERO_DURING_TRANSIT UNKNOWN_HEADER_TYPE UNKNOWN_OPTION').split()),
}

# Main traffic-filter criteria: option -> (API filter type, sides where it is valid).
CRITERIA = (
    ('networks', 'NETWORK', ('source', 'destination')),
    ('ip_addresses', 'IP_ADDRESS', ('source', 'destination')),
    ('ip_address_list', 'IP_ADDRESS', ('source', 'destination')),
    ('mac_addresses', 'MAC_ADDRESS', ('source',)),
    ('ipv6_iid', 'IPV6_IID', ('source', 'destination')),
    ('regions', 'REGION', ('source', 'destination')),
    ('vpn_servers', 'VPN_SERVER', ('source', 'destination')),
    ('site_to_site_tunnel', 'SITE_TO_SITE_VPN_TUNNEL', ('source', 'destination')),
    ('applications', 'APPLICATION', ('destination',)),
    ('application_categories', 'APPLICATION_CATEGORY', ('destination',)),
    ('domains', 'DOMAIN', ('destination',)),
)
MATCH_OPPOSITE_CRITERIA = ('networks', 'ip_addresses', 'ip_address_list', 'ipv6_iid', 'vpn_servers')
MAC_ADDRESS_CRITERIA = ('networks', 'ip_addresses', 'ip_address_list', 'ipv6_iid')

WEEKDAYS = ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY')
DAY_CHOICES = [d[:3].lower() for d in WEEKDAYS] + [d.lower() for d in WEEKDAYS]
SCHEDULE_OPTIONS = ('start_time', 'stop_time', 'days', 'date', 'start_date', 'stop_date')
# schedule mode -> (options required, options allowed besides those)
SCHEDULE_MODES = {
    'always': ((), ()),
    'every_day': (('start_time', 'stop_time'), ()),
    'every_week': (('days',), ('start_time', 'stop_time')),
    'one_time_only': (('date', 'start_time', 'stop_time'), ()),
    'custom': (('days', 'start_date', 'stop_date'), ('start_time', 'stop_time')),
}
_TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})$')
_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# Fields a system-defined policy accepts (sent with PATCH), and option names for the API keys in error messages.
PATCHABLE = ('loggingEnabled', 'reportFlowEnabled')
OPTION_NAMES = {
    'name': 'name', 'enabled': 'enabled', 'description': 'description', 'action': 'action',
    'ipProtocolScope': 'ip_version/protocol', 'connectionStateFilter': 'connection_states', 'ipsecFilter': 'ipsec',
    'source': 'source', 'destination': 'destination', 'schedule': 'schedule',
}


def _api_name(value):
    return str(value).strip().upper().replace('-', '_').replace('.', '_')


def _mac(value):
    return value.strip().lower().replace('-', ':')


def _time(option, value):
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value < 24 * 60:
        # YAML 1.1 reads an unquoted 17:30 as the sexagesimal number 1050.
        return '%02d:%02d' % divmod(value, 60)
    match = _TIME_RE.match(str(value).strip())
    if not match or int(match.group(1)) > 23 or int(match.group(2)) > 59:
        raise UnifiNetworkError('schedule.%s must be a 24-hour time in HH:MM format, got %r' % (option, value))
    return '%02d:%s' % (int(match.group(1)), match.group(2))


def _date(option, value):
    text = str(value).strip()
    try:
        if not _DATE_RE.match(text):
            raise ValueError(text)
        datetime.datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        raise UnifiNetworkError('schedule.%s must be a date in YYYY-MM-DD format, got %r' % (option, value))
    return text


class FirewallPolicy(StateResource):
    path = 'firewall/policies'
    result_key = 'firewall_policy'
    label = 'firewall policy'
    read_only_keys = ('id', 'metadata', 'index')

    def create_defaults(self):
        return {'enabled': True, 'loggingEnabled': False, 'ipProtocolScope': {'ipVersion': DEFAULT_IP_VERSION}}

    create_required = {'name': 'name', 'action': 'action', 'source.zoneId': 'source.zone', 'destination.zoneId': 'destination.zone'}

    # ---- desired state ---------------------------------------------------
    def to_api(self, current):
        p = self.params
        desired = pick(p, {'name': 'name', 'enabled': 'enabled', 'logging_enabled': 'loggingEnabled',
                           'report_flow_enabled': 'reportFlowEnabled'})
        if p['description'] is not None:
            desired['description'] = p['description'] or None
        action = self.action(current)
        if action is not None:
            desired['action'] = action
        if p['connection_states'] is not None:
            states = []
            for state in p['connection_states']:
                if upper(state) not in states:
                    states.append(upper(state))
            desired['connectionStateFilter'] = states or None
        if p['ipsec'] is not None:
            desired['ipsecFilter'] = IPSEC[p['ipsec']]
        scope = self.ip_protocol_scope(current)
        if scope is not None:
            desired['ipProtocolScope'] = scope
        for side in ('source', 'destination'):
            if p[side] is not None:
                desired[side] = self.endpoint(side, p[side])
        if p['schedule'] is not None:
            desired['schedule'] = self.schedule(p['schedule'])
        return desired

    def action(self, current):
        p = self.params
        current_action = (current or {}).get('action') or {}
        action_type = upper(p['action']) if p['action'] else current_action.get('type')
        return_traffic = p['allow_return_traffic']
        if return_traffic is not None and action_type and action_type != 'ALLOW':
            raise UnifiNetworkError('allow_return_traffic is only valid with action allow')
        if action_type != 'ALLOW':
            return {'type': action_type} if p['action'] else None
        if return_traffic is None:
            if not p['action']:
                return None
            if current_action.get('type') == 'ALLOW' and current_action.get('allowReturnTraffic') is not None:
                return {'type': 'ALLOW'}
            # The API requires allowReturnTraffic for ALLOW; match the UniFi UI default.
            return_traffic = True
        return {'type': 'ALLOW', 'allowReturnTraffic': return_traffic}

    def ip_protocol_scope(self, current):
        p = self.params
        current_scope = (current or {}).get('ipProtocolScope') or {}
        current_version = current_scope.get('ipVersion')
        version = IP_VERSIONS[p['ip_version']] if p['ip_version'] else (current_version or DEFAULT_IP_VERSION)
        if p['protocol'] is not None:
            return {'ipVersion': version, 'protocolFilter': self.protocol_filter(p['protocol'], version)}
        if p['ip_version'] is None:
            return None
        scope = {'ipVersion': version}
        carried = current_scope.get('protocolFilter')
        if version != current_version and carried:
            # A changed ipVersion replaces the scope object; keep the protocol when it is valid for the new version.
            named = carried.get('protocol') or {}
            if carried.get('type') == 'NAMED_PROTOCOL' and named.get('name') not in NAMED_PROTOCOLS.get(version, ()):
                raise UnifiNetworkError('The current protocol %s is not valid with ip_version %s; set protocol as well'
                                        % (named.get('name'), p['ip_version']))
            scope['protocolFilter'] = carried
        return scope

    def protocol_filter(self, proto, version):
        version_option = [k for k, v in IP_VERSIONS.items() if v == version][0]
        match_opposite = proto['match_opposite']
        icmp_type = proto['icmp_type']
        if proto['number'] is not None:
            if not 0 <= proto['number'] <= 255:
                raise UnifiNetworkError('protocol.number must be from 0 to 255, got %d' % proto['number'])
            if icmp_type is not None:
                raise UnifiNetworkError('protocol.icmp_type is only valid with protocol.name icmp or icmpv6')
            return {'type': 'PROTOCOL_NUMBER', 'protocolNumber': proto['number'], 'matchOpposite': match_opposite}

        name = _api_name(proto['name'])
        if name in ('ANY', 'TCP_UDP'):
            if match_opposite:
                raise UnifiNetworkError('protocol.match_opposite is not supported with %s' % proto['name'].lower())
            if icmp_type is not None:
                raise UnifiNetworkError('protocol.icmp_type is only valid with protocol.name icmp or icmpv6')
            return None if name == 'ANY' else {'type': 'PRESET', 'preset': {'name': 'TCP_UDP'}}
        if name not in NAMED_PROTOCOLS[version]:
            raise UnifiNetworkError('protocol %r is not valid with ip_version %s; valid names are tcp_udp, any and %s' % (
                proto['name'], version_option, ', '.join(sorted(n.lower().replace('_', '-') for n in NAMED_PROTOCOLS[version]))))
        typename = None
        if icmp_type is not None:
            if name not in ICMP_TYPES:
                raise UnifiNetworkError('protocol.icmp_type is only valid with protocol.name icmp or icmpv6')
            typename = _api_name(icmp_type)
            if typename not in ICMP_TYPES[name]:
                raise UnifiNetworkError('%r is not a valid %s type; valid types are %s' % (
                    icmp_type, name, ', '.join(sorted(t.lower() for t in ICMP_TYPES[name]))))
        # typenameFilter None removes a stale ICMP type when the protocol changes.
        return {'type': 'NAMED_PROTOCOL', 'matchOpposite': match_opposite,
                'protocol': {'name': name, 'typenameFilter': typename}}

    # ---- source / destination ----------------------------------------------
    def endpoint(self, side, spec):
        result = {}
        if spec.get('zone') is not None:
            result['zoneId'] = self.refs.resolve('firewall_zone', spec['zone'])
        result['trafficFilter'] = self.traffic_filter(side, spec)
        return result

    def traffic_filter(self, side, spec):
        valid = [opt for opt, _type, sides in CRITERIA if side in sides]
        present = [opt for opt in valid if spec.get(opt) is not None]
        if len(present) > 1:
            raise UnifiNetworkError('%s can match on only one of %s; got %s' % (side, ', '.join(valid), ' and '.join(present)))
        ports = self.port_filter(side, spec)
        mac_address = spec.get('mac_address')
        if not present:
            if spec['match_opposite']:
                raise UnifiNetworkError('%s.match_opposite needs one of %s' % (side, ', '.join(MATCH_OPPOSITE_CRITERIA)))
            if mac_address is not None:
                raise UnifiNetworkError('%s.mac_address must be combined with one of %s; use %s.mac_addresses to match '
                                        'on MAC addresses alone' % (side, ', '.join(MAC_ADDRESS_CRITERIA), side))
            return {'type': 'PORT', 'portFilter': ports} if ports else None

        option = present[0]
        value = spec[option]
        if isinstance(value, list) and not value:
            raise UnifiNetworkError('%s.%s must not be empty' % (side, option))
        if spec['match_opposite'] and option not in MATCH_OPPOSITE_CRITERIA:
            raise UnifiNetworkError('%s.match_opposite is not supported with %s' % (side, option))
        if mac_address is not None and option not in MAC_ADDRESS_CRITERIA:
            raise UnifiNetworkError('%s.mac_address can only be combined with %s, not %s' % (
                side, ', '.join(MAC_ADDRESS_CRITERIA), option))
        result = {'type': dict((o, t) for o, t, _sides in CRITERIA)[option]}
        result.update(self.criterion(option, value, spec['match_opposite']))
        # Explicit None removes a port/MAC filter left over from the current filter of the same type.
        result['portFilter'] = ports
        if side == 'source' and option != 'mac_addresses':
            result['macAddressFilter'] = _mac(mac_address) if mac_address is not None else None
        return result

    def criterion(self, option, value, match_opposite):
        refs = self.refs
        if option == 'networks':
            return {'networkFilter': {'networkIds': refs.resolve_many('network', value), 'matchOpposite': match_opposite}}
        if option == 'ip_addresses':
            return {'ipAddressFilter': {'type': 'IP_ADDRESSES', 'items': [parse_ip_item(v, None) for v in value],
                                        'matchOpposite': match_opposite}}
        if option == 'ip_address_list':
            return {'ipAddressFilter': {'type': 'TRAFFIC_MATCHING_LIST', 'matchOpposite': match_opposite,
                                        'trafficMatchingListId': refs.resolve('traffic_matching_list', value)}}
        if option == 'mac_addresses':
            return {'macAddressFilter': {'macAddresses': [_mac(v) for v in value]}}
        if option == 'ipv6_iid':
            return {'ipv6IidFilter': {'ipv6Iid': value, 'matchOpposite': match_opposite}}
        if option == 'regions':
            return {'regionFilter': {'regions': [upper(v.strip()) for v in value]}}
        if option == 'vpn_servers':
            return {'vpnServerFilter': {'vpnServerIds': refs.resolve_many('vpn_server', value), 'matchOpposite': match_opposite}}
        if option == 'site_to_site_tunnel':
            return {'siteToSiteVpnTunnelFilter': {'siteToSiteVpnTunnelId': refs.resolve('site_to_site_tunnel', value)}}
        if option == 'applications':
            return {'applicationFilter': {'applicationIds': value}}
        if option == 'application_categories':
            return {'applicationCategoryFilter': {'applicationCategoryIds': value}}
        return {'domainFilter': {'type': 'DOMAINS', 'domains': value}}

    def port_filter(self, side, spec):
        ports, port_list, opposite = spec.get('ports'), spec.get('port_list'), spec['ports_match_opposite']
        if ports is not None:
            if not ports:
                raise UnifiNetworkError('%s.ports must not be empty' % side)
            return {'type': 'PORTS', 'items': [parse_port_item(p) for p in ports], 'matchOpposite': opposite}
        if port_list is not None:
            return {'type': 'TRAFFIC_MATCHING_LIST', 'matchOpposite': opposite,
                    'trafficMatchingListId': self.refs.resolve('traffic_matching_list', port_list)}
        if opposite:
            raise UnifiNetworkError('%s.ports_match_opposite needs %s.ports or %s.port_list' % (side, side, side))
        return None

    # ---- schedule -------------------------------------------------------
    def schedule(self, sched):
        mode = sched['mode']
        required, optional = SCHEDULE_MODES[mode]
        invalid = [o for o in SCHEDULE_OPTIONS if sched.get(o) is not None and o not in required + optional]
        if invalid:
            raise UnifiNetworkError('schedule option(s) %s are not valid with mode %s' % (', '.join(invalid), mode))
        missing = [o for o in required if sched.get(o) in (None, [])]
        if missing:
            raise UnifiNetworkError('schedule mode %s requires: %s' % (mode, ', '.join(missing)))
        if mode == 'always':
            return None
        if (sched.get('start_time') is None) != (sched.get('stop_time') is None):
            raise UnifiNetworkError('schedule.start_time and schedule.stop_time must be set together')

        result = {'mode': upper(mode)}
        if 'days' in required:
            days = set(d for d in WEEKDAYS for given in sched['days'] if d.lower().startswith(given.lower()))
            result['repeatOnDays'] = [d for d in WEEKDAYS if d in days]
        if mode == 'one_time_only':
            result['date'] = _date('date', sched['date'])
        if mode == 'custom':
            result['startDate'] = _date('start_date', sched['start_date'])
            result['stopDate'] = _date('stop_date', sched['stop_date'])
        result['timeFilter'] = None
        if sched.get('start_time') is not None:
            result['timeFilter'] = {'startTime': _time('start_time', sched['start_time']),
                                    'stopTime': _time('stop_time', sched['stop_time'])}
        return result

    # ---- guards for system-defined and derived policies -------------------
    def check_updatable(self, current, desired):
        origin = origin_of(current)
        if origin == 'DERIVED':
            raise UnifiNetworkError('The firewall policy %r is derived from another policy and cannot be changed; '
                                    'change the policy it is derived from instead' % current.get('name'))
        if origin == 'SYSTEM_DEFINED':
            blocked = sorted(set(OPTION_NAMES.get(k, k) for k, v in desired.items()
                                 if k not in PATCHABLE and not is_subset({k: v}, current)))
            if blocked:
                raise UnifiNetworkError('The firewall policy %r is system-defined: only logging_enabled and report_flow_enabled '
                                        'can be changed, but these options differ: %s' % (current.get('name'), ', '.join(blocked)))

    def update_request(self, current, desired):
        if origin_of(current) == 'SYSTEM_DEFINED':
            return 'PATCH', dict((k, desired[k]) for k in PATCHABLE if k in desired)
        return super(FirewallPolicy, self).update_request(current, desired)

    def check_deletable(self, current):
        origin = origin_of(current)
        if origin == 'SYSTEM_DEFINED':
            raise UnifiNetworkError('The firewall policy %r is system-defined and cannot be deleted' % current.get('name'))
        if origin == 'DERIVED':
            raise UnifiNetworkError('The firewall policy %r is derived from another policy and cannot be deleted; '
                                    'change or delete the policy it is derived from instead' % current.get('name'))


def endpoint_spec(side):
    spec = dict(
        zone=dict(type='str', aliases=['zone_id']),
        networks=dict(type='list', elements='str', aliases=['network_ids']),
        ip_addresses=dict(type='list', elements='str'),
        ip_address_list=dict(type='str', aliases=['ip_address_traffic_matching_list']),
        ipv6_iid=dict(type='str', aliases=['ipv6_interface_identifier']),
        regions=dict(type='list', elements='str'),
        vpn_servers=dict(type='list', elements='str', aliases=['vpn_server_ids']),
        site_to_site_tunnel=dict(type='str', aliases=['site_to_site_vpn_tunnel']),
        match_opposite=dict(type='bool', default=False),
        ports=dict(type='list', elements='raw'),
        port_list=dict(type='str', aliases=['port_traffic_matching_list']),
        ports_match_opposite=dict(type='bool', default=False),
    )
    if side == 'source':
        spec.update(
            mac_addresses=dict(type='list', elements='str'),
            mac_address=dict(type='str'),
        )
    else:
        spec.update(
            applications=dict(type='list', elements='int', aliases=['application_ids']),
            application_categories=dict(type='list', elements='int', aliases=['application_category_ids']),
            domains=dict(type='list', elements='str'),
        )
    return dict(type='dict', options=spec, mutually_exclusive=[('ports', 'port_list')])


def argument_spec():
    spec = state_argument_spec()
    spec.update(
        name=dict(type='str'),
        enabled=dict(type='bool'),
        description=dict(type='str'),
        action=dict(type='str', choices=['allow', 'block', 'reject']),
        allow_return_traffic=dict(type='bool'),
        logging_enabled=dict(type='bool'),
        report_flow_enabled=dict(type='bool'),
        connection_states=dict(type='list', elements='str', choices=['new', 'invalid', 'established', 'related'],
                               aliases=['connection_state_filter']),
        ipsec=dict(type='str', choices=list(IPSEC), aliases=['ipsec_filter']),
        ip_version=dict(type='str', choices=list(IP_VERSIONS)),
        protocol=dict(type='dict', options=dict(
            name=dict(type='str'),
            number=dict(type='int'),
            match_opposite=dict(type='bool', default=False),
            icmp_type=dict(type='str'),
        ), mutually_exclusive=[('name', 'number')], required_one_of=[('name', 'number')]),
        source=endpoint_spec('source'),
        destination=endpoint_spec('destination'),
        schedule=dict(type='dict', options=dict(
            mode=dict(type='str', required=True, choices=list(SCHEDULE_MODES)),
            start_time=dict(type='raw'),
            stop_time=dict(type='raw'),
            days=dict(type='list', elements='str', choices=DAY_CHOICES, aliases=['repeat_on_days']),
            date=dict(type='str'),
            start_date=dict(type='str'),
            stop_date=dict(type='str'),
        )),
    )
    return spec


def main():
    run_state_module(FirewallPolicy, argument_spec(), required_one_of=[('name', 'id')])


if __name__ == '__main__':
    main()
