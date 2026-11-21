# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""Build UniFi Network API ``filter`` query expressions.

The API accepts expressions such as ``name.eq('IoT')``, ``vlanId.in(10,20)``,
``deviceId.isNull()`` and the compound forms ``and(...)``, ``or(...)`` and
``not(...)``.  Values are typed: strings/UUIDs/timestamps are single quoted,
numbers and booleans are bare.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


FILTER_FUNCTIONS = (
    'isNull', 'isNotNull', 'isEmpty',
    'eq', 'ne', 'gt', 'ge', 'lt', 'le', 'like',
    'in', 'notIn',
    'contains', 'containsAny', 'containsAll', 'containsExactly',
)
NO_VALUE_FUNCTIONS = ('isNull', 'isNotNull', 'isEmpty')
MULTI_VALUE_FUNCTIONS = ('in', 'notIn', 'containsAny', 'containsAll', 'containsExactly')
CONDITION_KEYS = ('property', 'function', 'value')
MATCH_OPERATORS = {'all': 'and', 'any': 'or'}


class FilterError(ValueError):
    """Raised when a structured filter cannot be rendered."""


def server_filterable(value):
    """Return False for strings whose quoting in a filter expression is not verified (quotes, backslashes).

    Callers then list without that condition and match on the client side instead.
    """
    return not (isinstance(value, str) and ("'" in value or '\\' in value))


def render_value(value):
    """Render a single typed value for use inside a filter function call."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace('\\', '\\\\').replace("'", "\\'")
    return "'%s'" % text


def render_condition(condition):
    """Render one ``{property, function, value}`` condition."""
    if not isinstance(condition, dict):
        raise FilterError('Each filter must be a dict with property, function and value keys, got %r' % (condition,))
    unknown = sorted(set(condition) - set(CONDITION_KEYS))
    if unknown:
        raise FilterError('Unsupported filter key(s) %s; supported keys are %s' % (', '.join(unknown), ', '.join(CONDITION_KEYS)))

    prop = condition.get('property')
    if not prop or not isinstance(prop, str):
        raise FilterError('Each filter requires a non-empty string "property"')
    function = condition.get('function')
    if function not in FILTER_FUNCTIONS:
        raise FilterError('Filter function %r is not valid; choose one of %s' % (function, ', '.join(FILTER_FUNCTIONS)))

    value = condition.get('value')
    if function in NO_VALUE_FUNCTIONS:
        if value is not None:
            raise FilterError('Filter function %s on %s does not take a value' % (function, prop))
        return '%s.%s()' % (prop, function)

    if value is None:
        raise FilterError('Filter function %s on %s requires a value' % (function, prop))

    if function in MULTI_VALUE_FUNCTIONS:
        values = value if isinstance(value, (list, tuple)) else [value]
        if not values:
            raise FilterError('Filter function %s on %s requires at least one value' % (function, prop))
        return '%s.%s(%s)' % (prop, function, ','.join(render_value(v) for v in values))

    if isinstance(value, (list, tuple, dict)):
        raise FilterError('Filter function %s on %s takes a single value, not a list' % (function, prop))
    return '%s.%s(%s)' % (prop, function, render_value(value))


def _combine(operator, expressions):
    if len(expressions) == 1:
        return expressions[0]
    return '%s(%s)' % (operator, ','.join(expressions))


def build_filter(filters=None, match='all', raw=None, name=None):
    """Build the full filter expression, or ``None`` when nothing filters.

    :param filters: a condition dict, or a list of condition dicts.
    :param match: ``all`` joins the conditions with ``and()``, ``any`` with ``or()``.
    :param raw: a raw filter expression, mutually exclusive with ``filters``.
    :param name: shorthand for ``name.eq(<name>)``, always ANDed with the rest.
    """
    if match not in MATCH_OPERATORS:
        raise FilterError('Filter match must be one of %s, got %r' % (', '.join(MATCH_OPERATORS), match))
    if isinstance(filters, dict):
        filters = [filters]
    filters = filters or []
    if filters and raw:
        raise FilterError('Structured filters and a raw filter expression are mutually exclusive')
    for item in filters:
        if not isinstance(item, dict):
            raise FilterError('Each filter must be a dict with property, function and value keys, got %r' % (item,))

    expressions = []
    if name is not None:
        expressions.append(render_condition({'property': 'name', 'function': 'eq', 'value': name}))

    if raw:
        expressions.append(raw)
    elif filters:
        expressions.append(_combine(MATCH_OPERATORS[match], [render_condition(f) for f in filters]))

    if not expressions:
        return None
    return _combine('and', expressions)
