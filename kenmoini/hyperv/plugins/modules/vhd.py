#!/usr/bin/python
# -*- coding: utf-8 -*-

#########################################################################################################################################
# kenmoini.hyperv.vhd - Adds, deletes and performs configuration of Hyper-V Virtual Hard Drives (VHDX).
#########################################################################################################################################

# this is a windows documentation stub. actual code lives in the .ps1
# file of the same name

# https://docs.microsoft.com/en-us/powershell/module/hyper-v/new-vhd?view=windowsserver2022-ps

DOCUMENTATION = '''
---
module: vhd
version_added: "1.0.0"
short_description: Adds, deletes and performs configuration of Hyper-V Virtual Hard Drives (VHDX).
description:
    - Adds, deletes and performs configuration of Hyper-V Virtual Hard Drives (VHDX).
options:
  path:
    description:
      - Path to the VHDX file
    required: true
  state:
    description:
      - State of the VHDX file
    required: false
    choices:
      - present
      - absent
    default: present
  size:
    description:
      - Size of the VHDX file
    required: false
    default: null
  cloneVHD:
    description:
      - Path to the source disk if being cloned
    required: false
    default: null
  dynamicExpansion:
    description:
      - Specifies whether the VHDX file is expandable. Mutually exclusive with fixedSize.
    required: false
    default: true
  fixedSize:
    description:
      - Specifies whether the VHDX file is fixed.  Mutually exclusive with dynamicExpansion.
    required: false
    default: null
'''

EXAMPLES = '''
- name: Create VHD with size of 120GB with dynamic expansion
  kenmoini.hyperv.vhd:
    path: "C:\Temp\my_vhd.vhdx"
    state: present
    size: 120GB
    dynamicExpansion: true

- name: Delete a VHD
  kenmoini.hyperv.vhd:
    path: "C:\Temp\my_vhd.vhdx"
    state: absent

- name: Create a fixed size VHD with size of 100GB
  kenmoini.hyperv.vhd:
    path: "C:\Temp\my_fixed_vhd.vhdx"
    state: present
    size: 120GB
    fixed: true

- name: Clone a VHD
  kenmoini.hyperv.vhd:
    path: "C:\Temp\my_cloned_vhd.vhdx"
    state: present
    cloneVHD: "C:\Temp\my_original_vhd.vhdx"
'''

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}
