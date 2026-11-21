# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""In-memory stand-in for the UniFi Network Integration API used by unit tests.

Install it with ``fake.install(monkeypatch)``; it replaces ``open_url`` in the
collection's api module and serves collections registered with ``add()``.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import io
import json
import re

from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

BASE = 'https://unifi.test/proxy/network/integrations'
SITE_ID = '00000000-0000-4000-8000-00000000a001'
SITE_COLLECTIONS = (
    'acl-rules', 'clients', 'device-tags', 'devices', 'dns/policies', 'firewall/policies', 'firewall/zones',
    'hotspot/vouchers', 'networks', 'radius/profiles', 'switching/lags', 'switching/mc-lag-domains',
    'switching/switch-stacks', 'traffic-matching-lists', 'vpn/servers', 'vpn/site-to-site-tunnels', 'wans',
    'wifi/broadcasts',
)

_TOKEN_RE = re.compile(r"\s*(?:(?P<str>'(?:\\.|[^'\\])*')|(?P<num>-?\d+(?:\.\d+)?)|(?P<word>[A-Za-z_][\w.]*)|(?P<punct>[(),]))")

# List endpoints that return a reduced "overview" instead of the full object (per the OpenAPI spec).
LIST_OVERVIEW_FIELDS = {
    'networks': ('default', 'deviceId', 'enabled', 'id', 'management', 'metadata', 'name', 'vlanId', 'zoneId'),
    'wifi/broadcasts': ('broadcastingDeviceFilter', 'broadcastingFrequenciesGHz', 'enabled', 'hotspotConfiguration', 'id',
                        'metadata', 'name', 'network', 'securityConfiguration', 'type'),
    'devices': ('features', 'firmwareUpdatable', 'firmwareVersion', 'id', 'interfaces', 'ipAddress', 'macAddress', 'model',
                'name', 'state', 'supported'),
}


def _tokenize(expr):
    pos, tokens = 0, []
    while pos < len(expr):
        m = _TOKEN_RE.match(expr, pos)
        if not m:
            raise ValueError('bad filter at %r' % expr[pos:])
        pos = m.end()
        kind = m.lastgroup
        text = m.group(kind)
        if kind == 'str':
            tokens.append(('val', re.sub(r'\\(.)', r'\1', text[1:-1])))
        elif kind == 'num':
            tokens.append(('val', float(text) if '.' in text else int(text)))
        elif kind == 'word' and text in ('true', 'false'):
            tokens.append(('val', text == 'true'))
        else:
            tokens.append((kind, text))
    return tokens


def _get_path(obj, dotted):
    for part in dotted.split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def _norm(v):
    return v


_FUNCS = {
    'eq': lambda a, b: _norm(a) == _norm(b[0]),
    'ne': lambda a, b: _norm(a) != _norm(b[0]),
    'gt': lambda a, b: a is not None and a > b[0],
    'ge': lambda a, b: a is not None and a >= b[0],
    'lt': lambda a, b: a is not None and a < b[0],
    'le': lambda a, b: a is not None and a <= b[0],
    'in': lambda a, b: _norm(a) in [_norm(x) for x in b],
    'notIn': lambda a, b: _norm(a) not in [_norm(x) for x in b],
    'isNull': lambda a, b: a is None,
    'isNotNull': lambda a, b: a is not None,
    'like': lambda a, b: a is not None and re.match('^' + re.escape(b[0]).replace(r'\*', '.*') + '$', a) is not None,
}


def _parse(tokens, i=0):
    kind, text = tokens[i]
    assert tokens[i + 1] == ('punct', '('), tokens
    i += 2
    if text in ('and', 'or', 'not'):
        subs = []
        while tokens[i] != ('punct', ')'):
            sub, i = _parse(tokens, i)
            subs.append(sub)
            if tokens[i] == ('punct', ','):
                i += 1
        i += 1
        if text == 'and':
            return (lambda o: all(s(o) for s in subs)), i
        if text == 'or':
            return (lambda o: any(s(o) for s in subs)), i
        return (lambda o: not subs[0](o)), i
    prop, func = text.rsplit('.', 1)
    args = []
    while tokens[i] != ('punct', ')'):
        if tokens[i][0] == 'val':
            args.append(tokens[i][1])
        i += 1
    i += 1
    fn = _FUNCS[func]
    return (lambda o: fn(_get_path(o, prop), args)), i


def compile_filter(expr):
    if not expr:
        return lambda o: True
    pred, _ = _parse(_tokenize(expr))
    return pred


class Call(object):
    def __init__(self, method, path, query, body):
        self.method, self.path, self.query, self.body = method, path, query, body

    def __repr__(self):
        return 'Call(%s %s %r %r)' % (self.method, self.path, self.query, self.body)


class _Response(object):
    def __init__(self, status, body):
        self.status = status
        self._raw = b'' if body is None else json.dumps(body).encode()

    def read(self):
        return self._raw

    def getcode(self):
        return self.status


class FakeUnifi(object):
    def __init__(self):
        self.collections = {}
        self.singletons = {}
        self.handlers = []
        self.calls = []
        self._seq = 0
        self.add('/v1/sites', {'id': SITE_ID, 'name': 'Default', 'internalReference': 'default'})
        # Every list endpoint exists (empty) like on a real controller.
        for path in ('countries', 'dpi/applications', 'dpi/categories', 'pending-devices'):
            self.collections.setdefault('/v1/' + path, [])
        for collection in SITE_COLLECTIONS:
            self.collections.setdefault(self.site_path(collection), [])

    # ---- setup helpers -------------------------------------------------
    def new_id(self):
        self._seq += 1
        return '00000000-0000-4000-8000-%012d' % self._seq

    def site_path(self, collection):
        return '/v1/sites/%s/%s' % (SITE_ID, collection)

    def add(self, path, obj):
        obj = copy.deepcopy(obj)
        obj.setdefault('id', self.new_id())
        self.collections.setdefault(path, []).append(obj)
        return obj

    def add_site(self, collection, obj):
        return self.add(self.site_path(collection), obj)

    def items(self, collection):
        return self.collections.setdefault(self.site_path(collection), [])

    def on(self, method, pattern, handler):
        """Register ``handler(fake, call, match)`` for requests matching a regex."""
        self.handlers.append((method, re.compile('^' + pattern + '$'), handler))

    @property
    def writes(self):
        return [c for c in self.calls if c.method != 'GET']

    def install(self, monkeypatch):
        from ansible_collections.kenmoini.unifi_network.plugins.module_utils import api
        monkeypatch.setattr(api, 'open_url', self)
        return self

    # ---- request handling ---------------------------------------------
    def error(self, url, status, message):
        body = json.dumps({'statusCode': status, 'statusName': 'ERR', 'code': 'api.err.Fake', 'message': message}).encode()
        return HTTPError(url, status, message, {}, io.BytesIO(body))

    def __call__(self, url, method='GET', headers=None, data=None, **kwargs):
        if not url.startswith(BASE):
            raise self.error(url, 404, 'wrong base url %s' % url)
        parts = urlsplit(url)
        path = parts.path[len(urlsplit(BASE).path):]
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        body = json.loads(data) if data else None
        call = Call(method, path, query, body)
        self.calls.append(call)

        for h_method, regex, handler in self.handlers:
            m = regex.match(path)
            if h_method == method and m:
                status, payload = handler(self, call, m)
                if status >= 400:
                    raise self.error(url, status, str(payload))
                return _Response(status, payload)

        if path in self.singletons:
            if method == 'GET':
                return _Response(200, self.singletons[path])
            if method == 'PUT':
                self.singletons[path] = body
                return _Response(200, body)

        if path in self.collections:
            items = self.collections[path]
            if method == 'GET':
                pred = compile_filter(query.get('filter'))
                matched = [o for o in items if pred(o)]
                offset = int(query.get('offset', 0))
                limit = int(query.get('limit', 25))
                data_page = matched[offset:offset + limit]
                overview = [v for k, v in LIST_OVERVIEW_FIELDS.items() if path == self.site_path(k)]
                if overview:
                    data_page = [dict((f, o[f]) for f in overview[0] if f in o) for o in data_page]
                return _Response(200, {'offset': offset, 'limit': limit, 'count': len(data_page),
                                       'totalCount': len(matched), 'data': copy.deepcopy(data_page)})
            if method == 'POST':
                obj = copy.deepcopy(body)
                obj['id'] = self.new_id()
                obj.setdefault('metadata', {'origin': 'USER_DEFINED'})
                items.append(obj)
                return _Response(201, copy.deepcopy(obj))

        parent, _, item_id = path.rpartition('/')
        if parent in self.collections:
            items = self.collections[parent]
            found = [o for o in items if o['id'] == item_id]
            if not found:
                raise self.error(url, 404, 'not found')
            obj = found[0]
            if method == 'GET':
                return _Response(200, copy.deepcopy(obj))
            if method == 'PUT':
                new = copy.deepcopy(body)
                new['id'] = obj['id']
                if 'metadata' in obj:
                    new['metadata'] = obj['metadata']
                items[items.index(obj)] = new
                return _Response(200, copy.deepcopy(new))
            if method == 'PATCH':
                obj.update(copy.deepcopy(body))
                return _Response(200, copy.deepcopy(obj))
            if method == 'DELETE':
                items.remove(obj)
                return _Response(200, {})

        raise self.error(url, 404, 'no route for %s %s' % (method, path))
