#!/usr/bin/python
# -*- coding: utf-8 -*-

#########################################################################################################################################
# kenmoini.hyperv.vhd_info - Get the configuration information of Virtual Hard Disks from a Windows Server running Hyper-V
#########################################################################################################################################

# this is a windows documentation stub. actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: vhd_info
version_added: "1.0.0"
short_description: Get the configuration information of Virtual Hard Disks from a Windows Server running Hyper-V
description:
    - Get the configuration information of Virtual Hard Disks from a Windows Server running Hyper-V
options:
  path:
    description:
      - Path to the VHD file
    required: true
'''

EXAMPLES = '''
- name: Get the information of a VHD File
  kenmoini.hyperv.vhd_info:
    path: "C:\Temp\my_vm.vhdx"
  register: r_vhd_info

- name: Print out the results
  debug:
    msg: "{{ r_vhd_info.json | from_json }}"
'''

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}
