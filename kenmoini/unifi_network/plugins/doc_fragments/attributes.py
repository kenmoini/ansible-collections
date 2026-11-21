# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

# Module attributes (check mode, diff mode, action group).

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
attributes:
  action_group:
    description: Use C(group/kenmoini.unifi_network.fullset) in C(module_defaults) to set shared options such as the URL and API key.
    support: full
    membership:
      - kenmoini.unifi_network.fullset
"""

    INFO = r"""
attributes:
  check_mode:
    description: Can run in check mode and returns the same data, because the module never changes anything.
    support: full
  diff_mode:
    description: Read-only module; there is nothing to diff.
    support: N/A
"""

    STATE = r"""
attributes:
  check_mode:
    description: Can run in check mode; the module reports what it would change and returns the predicted object.
    support: full
  diff_mode:
    description: Returns the object before and after the change when run with C(--diff).
    support: full
"""

    ACTION = r"""
attributes:
  check_mode:
    description: In check mode the module verifies the target exists and reports a change without performing the action.
    support: full
  diff_mode:
    description: The module performs an action and has no state to diff.
    support: none
"""
