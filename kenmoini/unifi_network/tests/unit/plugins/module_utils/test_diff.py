# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.diff import (
    is_subset,
    merge,
    normalize_scalar,
    remove_paths,
    strip_keys,
)


class TestNormalizeScalar:
    def test_mac_addresses_compare_case_insensitively(self):
        assert normalize_scalar('AA:BB:CC:DD:EE:FF') == normalize_scalar('aa:bb:cc:dd:ee:ff')

    def test_ipv6_addresses_are_canonicalized(self):
        assert normalize_scalar('2001:db8:0:0::1') == normalize_scalar('2001:DB8::1')

    def test_cidr_is_canonicalized(self):
        assert normalize_scalar('2001:DB8::/32') == normalize_scalar('2001:db8::/32')

    def test_ints_and_floats_compare_numerically(self):
        assert normalize_scalar(1) == normalize_scalar(1.0)

    def test_bool_is_not_equal_to_int(self):
        assert normalize_scalar(True) != normalize_scalar(1)

    def test_plain_strings_are_untouched(self):
        assert normalize_scalar('IoT') == 'IoT'
        assert normalize_scalar('IoT') != normalize_scalar('iot')


class TestIsSubset:
    def test_partial_dict_is_subset(self):
        assert is_subset({'name': 'IoT'}, {'name': 'IoT', 'vlanId': 30})

    def test_missing_key_is_not_subset(self):
        assert not is_subset({'vlanId': 30}, {'name': 'IoT'})

    def test_nested_mismatch_is_not_subset(self):
        assert not is_subset({'ipv4': {'prefixLength': 24}}, {'ipv4': {'prefixLength': 16}})

    def test_none_matches_missing_or_null(self):
        assert is_subset({'dhcpGuarding': None}, {'name': 'x'})
        assert is_subset({'dhcpGuarding': None}, {'dhcpGuarding': None})

    def test_none_does_not_match_a_value(self):
        assert not is_subset({'dhcpGuarding': None}, {'dhcpGuarding': {'trustedDhcpServerIpAddresses': ['10.0.0.1']}})

    def test_scalar_lists_are_unordered_by_default(self):
        assert is_subset({'networkIds': ['a', 'b']}, {'networkIds': ['b', 'a']})

    def test_lists_are_authoritative_on_length(self):
        assert not is_subset({'networkIds': ['a']}, {'networkIds': ['a', 'b']})

    def test_duplicates_must_match(self):
        assert not is_subset({'ids': ['a', 'a']}, {'ids': ['a', 'b']})

    def test_ordered_keys_compare_in_order(self):
        desired = {'dnsServerIpAddressesOverride': ['1.1.1.1', '8.8.8.8']}
        assert not is_subset(desired, {'dnsServerIpAddressesOverride': ['8.8.8.8', '1.1.1.1']})
        assert is_subset(desired, {'dnsServerIpAddressesOverride': ['1.1.1.1', '8.8.8.8']})

    def test_list_of_dicts_matches_unordered_subsets(self):
        desired = {'items': [{'type': 'PORT_NUMBER', 'value': 22}, {'type': 'PORT_NUMBER', 'value': 443}]}
        current = {'items': [{'type': 'PORT_NUMBER', 'value': 443, 'x': 1}, {'type': 'PORT_NUMBER', 'value': 22}]}
        assert is_subset(desired, current)

    def test_empty_list_matches_missing_or_null(self):
        assert is_subset({'macAddresses': []}, {})
        assert is_subset({'macAddresses': []}, {'macAddresses': None})

    def test_normalized_scalars_compare_equal(self):
        assert is_subset({'macAddress': 'AA:BB:CC:DD:EE:FF'}, {'macAddress': 'aa:bb:cc:dd:ee:ff'})


class TestMerge:
    def test_deep_merge_keeps_unmanaged_keys(self):
        current = {'name': 'IoT', 'ipv4': {'hostIpAddress': '10.0.0.1', 'prefixLength': 24}}
        desired = {'ipv4': {'prefixLength': 16}}
        assert merge(current, desired) == {'name': 'IoT', 'ipv4': {'hostIpAddress': '10.0.0.1', 'prefixLength': 16}}

    def test_none_removes_key(self):
        assert merge({'name': 'IoT', 'dhcpGuarding': {'x': 1}}, {'dhcpGuarding': None}) == {'name': 'IoT'}

    def test_lists_are_replaced(self):
        assert merge({'networkIds': ['a', 'b']}, {'networkIds': ['c']}) == {'networkIds': ['c']}

    def test_changed_discriminator_replaces_sub_object(self):
        current = {'trafficFilter': {'type': 'NETWORK', 'networkFilter': {'networkIds': ['a']}}}
        desired = {'trafficFilter': {'type': 'IP_ADDRESS', 'ipAddressFilter': {'addresses': ['10.0.0.1']}}}
        assert merge(current, desired) == desired

    def test_same_discriminator_merges(self):
        current = {'dhcp': {'mode': 'SERVER', 'leaseTimeSeconds': 86400, 'domainName': 'lan'}}
        desired = {'dhcp': {'mode': 'SERVER', 'leaseTimeSeconds': 3600}}
        assert merge(current, desired) == {'dhcp': {'mode': 'SERVER', 'leaseTimeSeconds': 3600, 'domainName': 'lan'}}

    def test_inputs_are_not_mutated(self):
        current = {'a': {'b': [1]}}
        desired = {'a': {'c': 2}}
        snapshot = copy.deepcopy((current, desired))
        merge(current, desired)
        assert (current, desired) == snapshot


class TestKeyHelpers:
    def test_strip_keys_removes_top_level_keys_only(self):
        obj = {'id': '1', 'metadata': {'origin': 'USER_DEFINED'}, 'name': 'x', 'sub': {'id': 'keep'}}
        assert strip_keys(obj, ('id', 'metadata')) == {'name': 'x', 'sub': {'id': 'keep'}}

    def test_remove_paths_drops_nested_keys(self):
        obj = {'securityConfiguration': {'type': 'WPA2_PERSONAL', 'passphrase': 's3cret'}}
        assert remove_paths(obj, [('securityConfiguration', 'passphrase'), ('missing', 'path')]) == {
            'securityConfiguration': {'type': 'WPA2_PERSONAL'}}
        assert obj['securityConfiguration']['passphrase'] == 's3cret'


class TestMergeTopLevel:
    def test_top_level_discriminator_change_merges_instead_of_replacing(self):
        current = {'name': 'IoT', 'management': 'GATEWAY', 'enabled': True}
        desired = {'management': 'SWITCH'}
        assert merge(current, desired) == {'name': 'IoT', 'management': 'SWITCH', 'enabled': True}


class TestPruneNone:
    def test_removes_none_values_recursively(self):
        from ansible_collections.kenmoini.unifi_network.plugins.module_utils.diff import prune_none
        obj = {'a': None, 'b': {'c': None, 'd': 1}, 'e': [{'f': None, 'g': 2}], 'h': 0}
        assert prune_none(obj) == {'b': {'d': 1}, 'e': [{'g': 2}], 'h': 0}


class TestEmptyDicts:
    def test_empty_dict_matches_missing_or_null(self):
        assert is_subset({'ipv6Configuration': {}}, {'name': 'x'})
        assert is_subset({'ipv6Configuration': {}}, {'ipv6Configuration': None})


class TestRemovePathsWildcard:
    def test_star_applies_to_every_list_item(self):
        obj = {'sec': {'keys': [{'name': 'a', 'passphrase': 'x'}, {'name': 'b', 'passphrase': 'y'}]}}
        assert remove_paths(obj, [('sec', 'keys', '*', 'passphrase')]) == {'sec': {'keys': [{'name': 'a'}, {'name': 'b'}]}}
