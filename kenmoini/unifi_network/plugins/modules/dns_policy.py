#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: dns_policy
short_description: Manage DNS policies (local DNS records and forwarding) in UniFi Network
version_added: "2.0.0"
description:
  - Creates, updates or deletes DNS policies served by the UniFi gateway, which are local DNS records
    (A, AAAA, CNAME, MX, SRV and TXT) and conditional forwarding of a domain to another DNS server.
  - A policy is found by its O(type) and O(domain) (case-insensitive), or by O(id) when given.
    One policy per type and domain is assumed; when several exist, set O(id) to choose one.
  - Only the options you set are managed; the module reads the policy first and only writes when something differs.
  - Each type accepts only its own options, and some are required when creating; see each option.
options:
  type:
    description:
      - The kind of DNS policy. Required together with O(domain) unless O(id) is set.
      - V(forward_domain) forwards queries for O(domain) to the DNS server at O(ip_address).
    type: str
    choices: [a, aaaa, cname, mx, srv, txt, forward_domain]
  domain:
    description:
      - The domain name the policy applies to, for example V(nas.home.arpa).
    type: str
  id:
    description:
      - UUID of an existing policy to manage. When set, O(type) and O(domain) can be changed.
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
  ipv4_address:
    description:
      - IPv4 address the name resolves to. Only for V(a); required when creating one.
    type: str
  ipv6_address:
    description:
      - IPv6 address the name resolves to. Only for V(aaaa); required when creating one.
    type: str
  target_domain:
    description:
      - The canonical name the alias points to. Only for V(cname); required when creating one.
    type: str
  ttl_seconds:
    description:
      - Time to live in seconds. Only for V(a), V(aaaa) and V(cname); required when creating one.
    type: int
  mail_server_domain:
    description:
      - Domain of the mail server. Only for V(mx); required when creating one.
    type: str
  priority:
    description:
      - Priority, where a lower number is preferred. Only for V(mx) and V(srv); required when creating them.
    type: int
  server_domain:
    description:
      - Domain of the server that runs the service. Only for V(srv); required when creating one.
    type: str
  service:
    description:
      - Service name, for example V(_sip). Only for V(srv); required when creating one.
    type: str
  protocol:
    description:
      - Protocol of the service, for example V(_tcp). Only for V(srv); required when creating one.
    type: str
  port:
    description:
      - Port of the service. Only for V(srv); required when creating one.
    type: int
  weight:
    description:
      - Relative weight for records with the same priority. Only for V(srv); required when creating one.
    type: int
  text:
    description:
      - The text value, up to 1024 characters. Only for V(txt); required when creating one.
    type: str
  ip_address:
    description:
      - IP address of the DNS server to forward queries to. Only for V(forward_domain); required when creating one.
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
- name: Local A record for the NAS
  kenmoini.unifi_network.dns_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    type: a
    domain: nas.home.arpa
    ipv4_address: 192.168.1.20
    ttl_seconds: 300

- name: Alias pointing at the NAS
  kenmoini.unifi_network.dns_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    type: cname
    domain: files.home.arpa
    target_domain: nas.home.arpa
    ttl_seconds: 300

- name: Forward a corporate domain to its own DNS server
  kenmoini.unifi_network.dns_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    type: forward_domain
    domain: corp.example.com
    ip_address: 10.10.0.53

- name: SRV record for a SIP server
  kenmoini.unifi_network.dns_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    type: srv
    domain: _sip._tcp.home.arpa
    service: _sip
    protocol: _tcp
    server_domain: pbx.home.arpa
    port: 5060
    priority: 10
    weight: 5

- name: Manage many records from a variable
  kenmoini.unifi_network.dns_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    type: a
    domain: "{{ item.name }}.home.arpa"
    ipv4_address: "{{ item.ip }}"
    ttl_seconds: 300
  loop:
    - {name: printer, ip: 192.168.1.30}
    - {name: camera, ip: 192.168.1.31}

- name: Temporarily disable a record
  kenmoini.unifi_network.dns_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    type: a
    domain: nas.home.arpa
    enabled: false

- name: Delete a record
  kenmoini.unifi_network.dns_policy:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    type: cname
    domain: files.home.arpa
    state: absent
'''

RETURN = r'''
dns_policy:
  description:
    - The DNS policy as returned by the API after the change, or the predicted policy in check mode.
    - Empty when O(state=absent).
  returned: always
  type: dict
  sample: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "type": "A_RECORD", "domain": "nas.home.arpa",
           "ipv4Address": "192.168.1.20", "ttlSeconds": 300, "enabled": true, "metadata": {"origin": "USER_DEFINED"}}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.diff import merge, prune_none
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.filters import build_filter
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import StateResource, run_state_module

TYPES = {
    'a': 'A_RECORD', 'aaaa': 'AAAA_RECORD', 'cname': 'CNAME_RECORD', 'mx': 'MX_RECORD',
    'srv': 'SRV_RECORD', 'txt': 'TXT_RECORD', 'forward_domain': 'FORWARD_DOMAIN',
}
API_TYPES = dict((v, k) for k, v in TYPES.items())

FIELDS = {
    'ipv4_address': 'ipv4Address', 'ipv6_address': 'ipv6Address', 'target_domain': 'targetDomain',
    'ttl_seconds': 'ttlSeconds', 'mail_server_domain': 'mailServerDomain', 'priority': 'priority',
    'server_domain': 'serverDomain', 'service': 'service', 'protocol': 'protocol', 'port': 'port',
    'weight': 'weight', 'text': 'text', 'ip_address': 'ipAddress',
}

# type -> (options required on create, optional options)
TYPE_FIELDS = {
    'a': (('ipv4_address', 'ttl_seconds'), ()),
    'aaaa': (('ipv6_address', 'ttl_seconds'), ()),
    'cname': (('target_domain', 'ttl_seconds'), ()),
    'mx': (('mail_server_domain', 'priority'), ()),
    'srv': (('server_domain', 'service', 'protocol', 'port', 'priority', 'weight'), ()),
    'txt': (('text',), ()),
    'forward_domain': (('ip_address',), ()),
}


class DnsPolicy(StateResource):
    path = 'dns/policies'
    result_key = 'dns_policy'
    label = 'DNS policy'

    def lookup_filter(self):
        if not self.params['domain']:
            raise UnifiNetworkError('type and domain are required to find a DNS policy unless id is set')
        # Only the type is filtered server-side; domains are compared case-insensitively below,
        # which does not depend on how the API compares strings.
        return build_filter(filters=[{'property': 'type', 'function': 'eq', 'value': TYPES[self.params['type']]}])

    def lookup_match(self, item):
        return (item.get('type') == TYPES[self.params['type']]
                and (item.get('domain') or '').lower() == self.params['domain'].lower())

    def lookup_description(self):
        return 'of type %s for %r' % (self.params['type'], self.params['domain'])

    def create_defaults(self):
        return {'enabled': True}

    def required_for_create(self, payload):
        required = {'type': 'type', 'domain': 'domain'}
        record_type = API_TYPES.get(payload.get('type'))
        if record_type:
            required.update((FIELDS[opt], opt) for opt in TYPE_FIELDS[record_type][0])
        return required

    def to_api(self, current):
        p = self.params
        record_type = p['type'] or API_TYPES.get((current or {}).get('type'))
        if record_type:
            allowed = set(TYPE_FIELDS[record_type][0]) | set(TYPE_FIELDS[record_type][1])
            invalid = sorted(opt for opt in FIELDS if p[opt] is not None and opt not in allowed)
            if invalid:
                raise UnifiNetworkError('Option(s) %s are not valid for type %s' % (', '.join(invalid), record_type))
        desired = {}
        if p['type']:
            desired['type'] = TYPES[p['type']]
        if p['domain'] is not None:
            # DNS names are case-insensitive: keep the stored spelling when only the case differs.
            same = current and (current.get('domain') or '').lower() == p['domain'].lower()
            desired['domain'] = current['domain'] if same else p['domain']
        if p['enabled'] is not None:
            desired['enabled'] = p['enabled']
        for opt, key in FIELDS.items():
            if p[opt] is not None:
                desired[key] = p[opt]
        return desired

    def update_request(self, current, desired):
        if 'type' in desired and desired['type'] != current.get('type'):
            base = dict((k, current[k]) for k in ('domain', 'enabled') if k in current)
            body = prune_none(merge(base, desired))
            missing = [opt for opt in TYPE_FIELDS[API_TYPES[desired['type']]][0] if body.get(FIELDS[opt]) is None]
            if missing:
                raise UnifiNetworkError('Changing the type to %s requires: %s' % (
                    API_TYPES[desired['type']], ', '.join(missing)))
            return 'PUT', body
        return super(DnsPolicy, self).update_request(current, desired)


def main():
    spec = state_argument_spec()
    spec.update(
        type=dict(type='str', choices=list(TYPES)),
        domain=dict(type='str'),
        enabled=dict(type='bool'),
        ipv4_address=dict(type='str'),
        ipv6_address=dict(type='str'),
        target_domain=dict(type='str'),
        ttl_seconds=dict(type='int'),
        mail_server_domain=dict(type='str'),
        priority=dict(type='int'),
        server_domain=dict(type='str'),
        service=dict(type='str'),
        protocol=dict(type='str'),
        port=dict(type='int'),
        weight=dict(type='int'),
        text=dict(type='str'),
        ip_address=dict(type='str'),
    )
    run_state_module(DnsPolicy, spec, required_one_of=[('id', 'type')])


if __name__ == '__main__':
    main()
