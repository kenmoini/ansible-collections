# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""Compare and merge UniFi Network API objects for idempotent updates.

Conventions used by the state modules:

* A *desired* fragment contains only the keys the user manages.  A key whose
  value is ``None`` means "this nullable feature must be absent/disabled".
* Lists are authoritative: the desired list replaces the current one.  Lists
  compare order-insensitively unless their key is in ``ORDERED_LIST_KEYS``.
* When a sub-object's discriminator (``type``, ``mode``...) changes, the whole
  sub-object is replaced so fields of the previous variant do not linger.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import ipaddress
import re

DISCRIMINATOR_KEYS = ('type', 'mode', 'management', 'interfaceType', 'ipVersion', 'action')

# Lists whose element order is meaningful to the API.
ORDERED_LIST_KEYS = frozenset((
    'dnsServerIpAddressesOverride',
    'ntpServerIpAddresses',
    'winsServerIpAddresses',
    'dhcpServerIpAddresses',
    'orderedAclRuleIds',
    'beforeSystemDefined',
    'afterSystemDefined',
))

_MAC_RE = re.compile(r'^[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}$')


def normalize_scalar(value):
    """Return a comparison key for a scalar so equivalent API values compare equal."""
    if isinstance(value, bool):
        return ('bool', value)
    if isinstance(value, (int, float)):
        return ('num', float(value))
    if isinstance(value, str):
        if _MAC_RE.match(value):
            return ('mac', value.lower().replace('-', ':'))
        if ':' in value or '.' in value:
            for parser in (ipaddress.ip_address, ipaddress.ip_interface):
                try:
                    return ('ip', str(parser(value)))
                except ValueError:
                    continue
        return value
    return value


def _is_empty(value):
    return value is None or value == [] or value == {}


def is_subset(desired, current, key=None):
    """Return True when everything in ``desired`` is already reflected in ``current``."""
    if isinstance(desired, dict):
        if not isinstance(current, dict):
            return False
        for k, v in desired.items():
            if v is None:
                if not _is_empty(current.get(k)):
                    return False
                continue
            if isinstance(v, (list, dict)) and not v and _is_empty(current.get(k)):
                continue
            if k not in current or not is_subset(v, current[k], key=k):
                return False
        return True

    if isinstance(desired, list):
        if current is None:
            current = []
        if not isinstance(current, list) or len(desired) != len(current):
            return False
        if key in ORDERED_LIST_KEYS:
            return all(is_subset(d, c, key=key) for d, c in zip(desired, current))
        remaining = list(current)
        for d in desired:
            for idx, c in enumerate(remaining):
                if is_subset(d, c, key=key):
                    del remaining[idx]
                    break
            else:
                return False
        return True

    return normalize_scalar(desired) == normalize_scalar(current)


def _discriminator_changed(current, desired):
    for k in DISCRIMINATOR_KEYS:
        if k in desired and k in current and normalize_scalar(desired[k]) != normalize_scalar(current[k]):
            return True
    return False


def merge(current, desired, _depth=0):
    """Return a new object: ``current`` with ``desired`` applied on top.

    Nested sub-objects whose discriminator changes are replaced wholesale; the
    top-level object is always merged because its identity persists.
    """
    if not isinstance(desired, dict) or not isinstance(current, dict):
        return copy.deepcopy(desired)
    if _depth > 0 and _discriminator_changed(current, desired):
        return {k: copy.deepcopy(v) for k, v in desired.items() if v is not None}
    result = copy.deepcopy(current)
    for k, v in desired.items():
        if v is None:
            result.pop(k, None)
        else:
            result[k] = merge(current.get(k), v, _depth + 1)
    return result


def prune_none(obj):
    """Return a deep copy of ``obj`` with ``None`` values removed from every dict."""
    if isinstance(obj, dict):
        return {k: prune_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [prune_none(v) for v in obj]
    return copy.deepcopy(obj)


def strip_keys(obj, keys):
    """Return a deep copy of ``obj`` without the given top-level keys."""
    return {k: copy.deepcopy(v) for k, v in obj.items() if k not in keys}


def _remove_path(node, path):
    if not path:
        return
    head, rest = path[0], path[1:]
    if head == '*':
        for item in node if isinstance(node, list) else []:
            _remove_path(item, rest)
    elif isinstance(node, dict):
        if not rest:
            node.pop(head, None)
        elif head in node:
            _remove_path(node[head], rest)


def remove_paths(obj, paths):
    """Return a deep copy of ``obj`` with each key path (tuple of keys) removed.

    A ``'*'`` element in a path applies the rest of the path to every item of a list.
    """
    result = copy.deepcopy(obj)
    for path in paths:
        _remove_path(result, tuple(path))
    return result
