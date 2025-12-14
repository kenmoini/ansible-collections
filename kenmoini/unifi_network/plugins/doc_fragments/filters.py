# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for filtering queries.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  unifi_network_filters:
    description:
      - Query filters to apply to the request.  Find the documentation for filter syntax at Ubiquiti's official API documentation seen in your Unifi Dashboard under a specific Site > Integrations.  Mutually exclusive with unifi_network_filters_raw.
    required: false
    aliases: ['filters', 'filter']
    type: dict
    options:
      property:
        description:
          - The property to filter on, eg "name", "id", etc.
        type: str
        required: true
      function:
        description:
          - The function to apply for filtering.
        type: str
        required: true
        choices: ['isNull', 'isNotNull', 'eq', 'ne', 'gt', 'ge', 'lt', 'le', 'like', 'in', 'notIn', 'isEmpty', 'contains', 'containsAny', 'containsAll', 'containsExactly']
      value:
        description:
          - The value to filter against.  Not required for some functions like isNull.
        type: str
        required: false
        default: null
  unifi_network_filters_raw:
    description:
      - Raw filter string to apply to the request.  Use this instead of unifi_network_filters when you need to apply multiple filters or complex filter logic.  Mutually exclusive with unifi_network_filters.
    required: false
    aliases: ['filters_raw', 'filter_raw']
    type: str
"""