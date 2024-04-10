#!/usr/bin/python
# -*- coding: utf-8 -*-

#########################################################################################################################################
# kenmoini.hyperv.vm - Create/Delete Virtual Machines from a Windows Server running Hyper-V
#########################################################################################################################################

# this is a windows documentation stub. actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: vm
version_added: "1.0.0"
short_description: Create/Delete Virtual Machines from a Windows Server running Hyper-V
description:
    - Create/Delete Virtual Machines from a Windows Server running Hyper-V
options:
  name:
    description:
      - Name of VM
    required: true
  state:
    description:
      - State of VM
    required: false
    choices:
      - present
      - absent
      - started
      - stopped
      - poweredon
      - poweredoff
    default: null
  force:
    description:
      - Force VM to be deleted or stopped
    required: false
    choices:
      - true
      - false
    default: null

  cpu:
    description:
      - Number of CPUs
    required: false
    default: null
  memory:
    description:
      - Sets the amount of memory for the VM.
    required: false
    default: null
  generation:
    description:
      - Specifies the generation of the VM
    required: false
    default: 2

  networkSwitch:
    description:
      - Specifies a network adapter for the VM
    required: false
    default: null

  diskPath:
    description:
      - Specify path of VHD/VHDX file for VM
      - If the file exists it will be attached, if not then a new one will be created
    require: false
    default: null
  diskSize:
    description:
      - Specify size of VHD/VHDX file for VM if being created dynamically
    required: false
    default: null
  bootDevice:
    description:
      - Specify the boot device for the VM - accepts Floppy, CD, IDE, LegacyNetworkAdapter, NetworkAdapter, VHD
    required: false
    default: null
  cdrom:
    description:
      - Specify the path of the ISO image to use for the VM installation
    required: false
    default: null

  liveMigration:
    description:
      - Enable or disable CPU Live Migration
    required: false
    default: false
  nestedVirtualization:
    description:
      - Enable or disable Nested Virtualization
    required: false
    default: false
'''

EXAMPLES = '''
- name: Create a VM
  kenmoini.hyperv.vm:
    name: my-vm
    state: present
    memory: 4GB
    cpu: 4
    networkSwitch: VMNetwork
    diskSize: 10GB
    diskpath: C:\Temp\my_vm.vhdx

- name: Delete a VM
  kenmoini.hyperv.vm:
    name: bye-vm
    state: absent

- name: Start a VM
  kenmoini.hyperv.vm:
    name: hi-vm
    state: started

- name: Stop a VM
  kenmoini.hyperv.vm:
    name: night-vm
    state: stopped

- name: Create a VM with 256MB memory and 2 CPUs and a specific pre-created VHDX
  kenmoini.hyperv.vm:
    name: mini-vm
    state: present
    memory: 256MB
    cpu: 2
    diskpath: C:\Temp\mini_vm.vhdx

- name: Create and start a generation 1 VM with 256MB memory and a network adapter
  kenmoini.hyperv.vm:
    name: old-vm
    state: present
    generation: 1
    memory: 256MB
    networkSwitch: WAN1
'''

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}
