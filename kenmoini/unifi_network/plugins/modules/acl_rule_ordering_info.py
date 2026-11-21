#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: acl_rule_ordering_info
short_description: Get the order of user-defined ACL rules in UniFi Network
version_added: "2.0.0"
description:
  - Returns the evaluation order of the user-defined ACL rules at a site. Rules earlier in the list take priority.
  - Use M(kenmoini.unifi_network.acl_rule_ordering) to change the order.
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Get the ACL rule order
  kenmoini.unifi_network.acl_rule_ordering_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
  register: r_order
'''

RETURN = r'''
ordering:
  description: The ACL rule ordering, exactly as returned by the API.
  returned: always
  type: dict
  sample: {"orderedAclRuleIds": ["497f6eca-6276-4993-bfeb-53cbbbba6f08", "7f1c8a52-5b6e-4d0e-9f53-2b7a1d0c9e11"]}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import (
    connection_argument_spec,
    site_argument_spec,
)
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_single_info_module


def main():
    spec = connection_argument_spec()
    spec.update(site_argument_spec())
    run_single_info_module('acl-rules/ordering', 'ordering', spec)


if __name__ == '__main__':
    main()
