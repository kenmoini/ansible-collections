#!/usr/bin/python
# -*- coding: utf-8 -*-

#########################################################################################################################################
# kenmoini.hyperv.vmswitch_info - Get the configuration information of Virtual Switches from a Windows Server running Hyper-V
#########################################################################################################################################

# this is a windows documentation stub. actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: vmswitch_info
version_added: "1.0.0"
short_description: Get the configuration information of Virtual Switches from a Windows Server running Hyper-V
description:
    - Get the configuration information of Virtual Switches from a Windows Server running Hyper-V
options:
  name:
    description:
      - Name of Virtual Switch
    required: true
'''

EXAMPLES = '''
- name: Get the information of a Virtual Switch called VMNetwork
  kenmoini.hyperv.vmswitch_info:
    name: VMNetwork
  register: r_vmswitch_info

- name: Print out the results
  debug:
    msg: "{{ r_vmswitch_info.json | from_json }}"
'''

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}
