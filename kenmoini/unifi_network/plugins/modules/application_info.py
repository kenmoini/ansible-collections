#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: application_info
short_description: Get UniFi Network application information
version_added: "1.0.0"
description:
  - Returns general details about the UniFi Network application, such as its version.
  - Useful to validate connectivity and credentials before running other modules.
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.info
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Get the UniFi Network application version
  kenmoini.unifi_network.application_info:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
  register: r_app

- name: Show the version
  ansible.builtin.debug:
    msg: "{{ r_app.application.applicationVersion }}"
'''

RETURN = r'''
application:
  description: Application information, exactly as returned by the API.
  returned: always
  type: dict
  sample: {"applicationVersion": "11.0.97"}
'''

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import connection_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.info import run_single_info_module


def main():
    run_single_info_module('info', 'application', connection_argument_spec(), site_scoped=False)


if __name__ == '__main__':
    main()
