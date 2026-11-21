# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""Resolve user-friendly references (names, MACs) to UniFi object UUIDs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re

from .api import UnifiNetworkError
from .filters import render_condition, server_filterable

UUID_RE = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
MAC_RE = re.compile(r'^[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}$')
IPV4_RE = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')

# path: collection path (site-scoped unless site_scoped is False)
# fields: properties matched against a plain name
# mac_field / ip_field: property matched when the value is a MAC / IPv4 address
# filterable: whether the endpoint accepts ``filter`` for the name fields
REFERENCE_KINDS = {
    'site': dict(label='site', path='/v1/sites', site_scoped=False, fields=('internalReference', 'name')),
    'network': dict(label='network', path='networks', fields=('name',)),
    'firewall_zone': dict(label='firewall zone', path='firewall/zones', fields=('name',)),
    'firewall_policy': dict(label='firewall policy', path='firewall/policies', fields=('name',)),
    'acl_rule': dict(label='ACL rule', path='acl-rules', fields=('name',)),
    'traffic_matching_list': dict(label='traffic matching list', path='traffic-matching-lists', fields=('name',)),
    'wifi_broadcast': dict(label='WiFi broadcast', path='wifi/broadcasts', fields=('name',)),
    'device': dict(label='device', path='devices', fields=('name',), mac_field='macAddress', ip_field='ipAddress'),
    'device_tag': dict(label='device tag', path='device-tags', fields=('name',)),
    'client': dict(label='client', path='clients', fields=('name',), mac_field='macAddress', ip_field='ipAddress',
                   filterable=False),
    'radius_profile': dict(label='RADIUS profile', path='radius/profiles', fields=('name',)),
    'vpn_server': dict(label='VPN server', path='vpn/servers', fields=('name',)),
    'site_to_site_tunnel': dict(label='site-to-site VPN tunnel', path='vpn/site-to-site-tunnels', fields=('name',)),
    'wan_interface': dict(label='WAN interface', path='wans', fields=('name',), filterable=False),
}


def is_uuid(value):
    return isinstance(value, str) and UUID_RE.match(value) is not None


def _eq(field, value):
    return render_condition({'property': field, 'function': 'eq', 'value': value})


class ReferenceResolver(object):
    """Looks objects up by name/MAC/IP and caches the results for the module run."""

    def __init__(self, client, site_id=None):
        self.client = client
        self.site_id = site_id
        self._cache = {}

    def collection_path(self, kind):
        spec = REFERENCE_KINDS[kind]
        if not spec.get('site_scoped', True):
            return spec['path']
        if not self.site_id:
            raise UnifiNetworkError('A site is required to look up a %s' % spec['label'])
        return '/v1/sites/%s/%s' % (self.site_id, spec['path'])

    def _match_fields(self, spec, value):
        """Return (fields, server_filterable, normalizer) for a lookup value."""
        if spec.get('mac_field') and MAC_RE.match(value):
            return (spec['mac_field'],), True, lambda v: v.lower().replace('-', ':') if isinstance(v, str) else v
        if spec.get('ip_field') and IPV4_RE.match(value):
            return (spec['ip_field'],), True, lambda v: v
        return spec['fields'], spec.get('filterable', True), lambda v: v

    def lookup(self, kind, value):
        """Return every object of ``kind`` whose name (or MAC/IP) exactly matches ``value``."""
        spec = REFERENCE_KINDS[kind]
        fields, filterable, norm = self._match_fields(spec, value)
        wanted = norm(value)
        filter_expr = None
        if filterable and server_filterable(wanted):
            conditions = [_eq(f, wanted) for f in fields]
            filter_expr = conditions[0] if len(conditions) == 1 else 'or(%s)' % ','.join(conditions)
        items = self.client.paginate(self.collection_path(kind), filter_expr=filter_expr)
        return [item for item in items if any(norm(item.get(f)) == wanted for f in fields)]

    def resolve(self, kind, value):
        """Return the UUID for ``value``, which may already be a UUID."""
        if value is None or is_uuid(value):
            return value
        key = (kind, value)
        if key not in self._cache:
            label = REFERENCE_KINDS[kind]['label']
            matches = self.lookup(kind, value)
            if not matches:
                raise UnifiNetworkError('No %s named %r was found%s' % (
                    label, value, '' if kind == 'site' else ' in the site'))
            if len(matches) > 1:
                raise UnifiNetworkError('Multiple %ss match %r (ids: %s); use the UUID instead' % (
                    label, value, ', '.join(m['id'] for m in matches)))
            self._cache[key] = matches[0]['id']
        return self._cache[key]

    def resolve_many(self, kind, values):
        if values is None:
            return None
        return [self.resolve(kind, v) for v in values]
