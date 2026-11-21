# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for filtering and limiting list queries.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_filters:
    description:
      - One filter condition (a dict), or a list of conditions, evaluated by the API.
      - Each condition has the keys C(property), C(function) and C(value).
      - C(property) is a filterable property of the resource; nested properties use dots, for example C(metadata.origin).
        The module description lists the filterable properties.
      - C(function) is one of C(eq), C(ne), C(gt), C(ge), C(lt), C(le), C(like), C(in), C(notIn), C(isNull), C(isNotNull),
        C(isEmpty), C(contains), C(containsAny), C(containsAll) or C(containsExactly).
      - C(value) keeps its YAML type, so V(true) and V(10) are sent as a boolean and a number while strings and UUIDs are quoted.
        C(in), C(notIn), C(containsAny), C(containsAll) and C(containsExactly) take a list.
        C(isNull), C(isNotNull) and C(isEmpty) take no value.
      - C(like) matches patterns where C(*) matches any characters and C(.) one character.
      - Mutually exclusive with O(unifi_network_filters_raw).
    required: false
    aliases: ['filters', 'filter']
    type: raw
  unifi_network_filters_match:
    description:
      - How a list of conditions in O(unifi_network_filters) is combined.
      - V(all) requires every condition to match (C(and)), V(any) requires at least one (C(or)).
    required: false
    default: all
    choices: ['all', 'any']
    aliases: ['filters_match']
    type: str
  unifi_network_filters_raw:
    description:
      - A raw filter expression passed to the API as-is, for logic the structured form cannot express,
        for example V(not(name.like('guest*'))) or V(and(vlanId.ge(10),or(enabled.eq(false),name.eq('IoT')))).
      - Mutually exclusive with O(unifi_network_filters).
    required: false
    aliases: ['filters_raw', 'filter_raw']
    type: str
  limit:
    description:
      - Return at most this many items.
      - By default every page is fetched and all matching items are returned.
    required: false
    type: int
"""

    LIMIT = r"""
options:
  limit:
    description:
      - Return at most this many items.
      - By default every page is fetched and all matching items are returned.
    required: false
    type: int
"""
