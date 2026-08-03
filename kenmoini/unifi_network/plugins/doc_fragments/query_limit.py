# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Ken Moini <ken@kenmoini.com>
# MIT License

# Options for specifying the Query Limit.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  query_limit:
    description:
      - The Limit to use for the query.
    required: false
    default: 100
    type: int
"""