#!/usr/bin/python
# -*- coding: utf-8 -*-

#########################################################################################################################################
# kenmoini.hyperv.vm_info - Get the configuration information of Virtual Machines from a Windows Server running Hyper-V
#########################################################################################################################################

# this is a windows documentation stub. actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: vm_info
version_added: "1.0.0"
short_description: Get the configuration information of Virtual Machines from a Windows Server running Hyper-V
description:
    - Get the configuration information of Virtual Machines from a Windows Server running Hyper-V
options:
  name:
    description:
      - Name of the Virtual Machine
    required: true
'''

EXAMPLES = '''
- name: Get the information of a VM
  kenmoini.hyperv.vm_info:
    name: my-vm
  register: r_vm_info

- name: Print out the results
  debug:
    msg: "{{ r_vm_info.json | from_json }}"
'''

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}
