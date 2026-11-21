# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""Helpers to turn Ansible-friendly option values into UniFi API structures."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ipaddress

from .api import UnifiNetworkError


def pick(src, mapping):
    """Return ``{api_key: src[option]}`` for every option in ``mapping`` that is set (not ``None``)."""
    if not src:
        return {}
    return dict((api_key, src[opt]) for opt, api_key in mapping.items() if src.get(opt) is not None)


def upper(value):
    return value.upper() if isinstance(value, str) else value


def _ip(text, version):
    addr = ipaddress.ip_address(text.strip())
    if version is not None and addr.version != version:
        raise ValueError(text)
    return addr


def parse_ip_item(item, version, allow_subnet=True, allow_range=True):
    """Turn ``10.0.0.1``, ``10.0.0.0/24`` or ``10.0.0.1-10.0.0.9`` into a typed API item.

    ``version`` is 4 or 6, or ``None`` to accept either.  IPv6 ranges are only
    accepted when ``version`` is ``None`` (the firewall API supports them).
    """
    text = str(item).strip()
    try:
        if allow_subnet and '/' in text:
            net = ipaddress.ip_network(text, strict=False)
            if version is not None and net.version != version:
                raise ValueError(text)
            return {'type': 'SUBNET', 'value': str(net)}
        if allow_range and version != 6 and '-' in text:
            start, stop = text.split('-', 1)
            start, stop = _ip(start, version), _ip(stop, version)
            if start.version != stop.version:
                raise ValueError(text)
            return {'type': 'IP_ADDRESS_RANGE', 'start': str(start), 'stop': str(stop)}
        return {'type': 'IP_ADDRESS', 'value': str(_ip(text, version))}
    except ValueError:
        kinds = ['address']
        if allow_subnet:
            kinds.append('subnet')
        if allow_range and version != 6:
            kinds.append('range')
        text_kinds = kinds[0] if len(kinds) == 1 else ', '.join(kinds[:-1]) + ' or ' + kinds[-1]
        label = 'IP' if version is None else 'IPv%d' % version
        raise UnifiNetworkError('%r is not a valid %s %s' % (item, label, text_kinds))


def _port(text):
    port = int(str(text).strip())
    if not 1 <= port <= 65535:
        raise ValueError(text)
    return port


def parse_port_item(item):
    """Turn ``443`` or ``8000-8100`` into a typed API port item."""
    try:
        text = str(item).strip()
        if '-' in text:
            start, stop = text.split('-', 1)
            start, stop = _port(start), _port(stop)
            if start > stop:
                raise ValueError(text)
            return {'type': 'PORT_NUMBER_RANGE', 'start': start, 'stop': stop}
        return {'type': 'PORT_NUMBER', 'value': _port(text)}
    except ValueError:
        raise UnifiNetworkError('%r is not a valid port or port range (1-65535)' % (item,))
