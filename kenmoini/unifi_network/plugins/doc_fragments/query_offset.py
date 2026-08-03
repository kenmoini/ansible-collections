# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for specifying the Query Offset.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  query_offset:
    description:
      - The Offset to use for the query.
    required: false
    default: 0
    type: int
"""