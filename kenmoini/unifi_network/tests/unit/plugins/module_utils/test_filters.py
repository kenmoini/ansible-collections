# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.filters import (
    FilterError,
    build_filter,
    render_condition,
    render_value,
)


class TestRenderValue:
    def test_string_is_single_quoted(self):
        assert render_value('IoT') == "'IoT'"

    def test_single_quote_and_backslash_are_escaped(self):
        assert render_value("O'Brien\\x") == "'O\\'Brien\\\\x'"

    def test_bool_is_bare_lowercase(self):
        assert render_value(True) == 'true'
        assert render_value(False) == 'false'

    def test_int_and_float_are_bare(self):
        assert render_value(10) == '10'
        assert render_value(2.4) == '2.4'


class TestRenderCondition:
    def test_eq_string(self):
        assert render_condition({'property': 'name', 'function': 'eq', 'value': 'IoT'}) == "name.eq('IoT')"

    def test_typed_values_are_not_quoted(self):
        assert render_condition({'property': 'enabled', 'function': 'eq', 'value': True}) == 'enabled.eq(true)'
        assert render_condition({'property': 'vlanId', 'function': 'gt', 'value': 10}) == 'vlanId.gt(10)'

    def test_multi_value_function_joins_list(self):
        cond = {'property': 'id', 'function': 'in', 'value': ['a', 'b']}
        assert render_condition(cond) == "id.in('a','b')"

    def test_multi_value_function_accepts_scalar(self):
        assert render_condition({'property': 'id', 'function': 'notIn', 'value': 'a'}) == "id.notIn('a')"

    def test_contains_any_with_ints(self):
        cond = {'property': 'sourceFilter.portFilter', 'function': 'containsAny', 'value': [22, 443]}
        assert render_condition(cond) == 'sourceFilter.portFilter.containsAny(22,443)'

    def test_no_value_functions_render_empty_parens(self):
        assert render_condition({'property': 'deviceId', 'function': 'isNull'}) == 'deviceId.isNull()'
        assert render_condition({'property': 'features', 'function': 'isEmpty', 'value': None}) == 'features.isEmpty()'

    def test_no_value_function_rejects_value(self):
        with pytest.raises(FilterError, match='does not take a value'):
            render_condition({'property': 'deviceId', 'function': 'isNull', 'value': 'x'})

    def test_value_function_requires_value(self):
        with pytest.raises(FilterError, match='requires a value'):
            render_condition({'property': 'name', 'function': 'eq'})

    def test_single_value_function_rejects_list(self):
        with pytest.raises(FilterError, match='single value'):
            render_condition({'property': 'name', 'function': 'eq', 'value': ['a', 'b']})

    def test_unknown_function_rejected(self):
        with pytest.raises(FilterError, match='function'):
            render_condition({'property': 'name', 'function': 'equals', 'value': 'a'})

    def test_missing_property_rejected(self):
        with pytest.raises(FilterError, match='property'):
            render_condition({'function': 'eq', 'value': 'a'})

    def test_unknown_key_rejected(self):
        with pytest.raises(FilterError, match='Unsupported'):
            render_condition({'property': 'name', 'function': 'eq', 'value': 'a', 'op': 'x'})


class TestBuildFilter:
    def test_nothing_returns_none(self):
        assert build_filter() is None
        assert build_filter(filters=[]) is None

    def test_single_dict_is_accepted(self):
        assert build_filter(filters={'property': 'name', 'function': 'eq', 'value': 'IoT'}) == "name.eq('IoT')"

    def test_list_is_anded_by_default(self):
        filters = [
            {'property': 'name', 'function': 'like', 'value': 'guest*'},
            {'property': 'vlanId', 'function': 'gt', 'value': 10},
        ]
        assert build_filter(filters=filters) == "and(name.like('guest*'),vlanId.gt(10))"

    def test_list_is_ored_when_match_any(self):
        filters = [
            {'property': 'type', 'function': 'eq', 'value': 'WIRED'},
            {'property': 'type', 'function': 'eq', 'value': 'VPN'},
        ]
        assert build_filter(filters=filters, match='any') == "or(type.eq('WIRED'),type.eq('VPN'))"

    def test_name_shorthand_alone(self):
        assert build_filter(name='IoT') == "name.eq('IoT')"

    def test_name_shorthand_is_always_anded_with_filters(self):
        filters = [{'property': 'enabled', 'function': 'eq', 'value': True}]
        assert build_filter(filters=filters, name='IoT') == "and(name.eq('IoT'),enabled.eq(true))"

    def test_name_shorthand_ands_with_ored_group(self):
        filters = [
            {'property': 'vlanId', 'function': 'eq', 'value': 10},
            {'property': 'vlanId', 'function': 'eq', 'value': 20},
        ]
        assert build_filter(filters=filters, match='any', name='IoT') == "and(name.eq('IoT'),or(vlanId.eq(10),vlanId.eq(20)))"

    def test_raw_passthrough(self):
        assert build_filter(raw="not(name.eq('x'))") == "not(name.eq('x'))"

    def test_raw_with_name_is_anded(self):
        assert build_filter(raw="not(enabled.eq(true))", name='IoT') == "and(name.eq('IoT'),not(enabled.eq(true)))"

    def test_raw_and_structured_are_mutually_exclusive(self):
        with pytest.raises(FilterError, match='mutually exclusive'):
            build_filter(filters={'property': 'name', 'function': 'eq', 'value': 'a'}, raw="name.eq('b')")

    def test_non_dict_list_item_rejected(self):
        with pytest.raises(FilterError, match='must be a dict'):
            build_filter(filters=['name.eq(1)'])

    def test_invalid_match_rejected(self):
        with pytest.raises(FilterError, match='match'):
            build_filter(filters=[{'property': 'a', 'function': 'isNull'}], match='some')
