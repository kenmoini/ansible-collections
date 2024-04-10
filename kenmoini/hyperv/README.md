# Ansible Collection - kenmoini.hyperv

## Available Modules

- vhd
- vhd_info
- vm
- vm_info
- vmswitch
- vmswitch_info

## Examples

### vhd

```yaml
- name: Create VHD with size of 120GB with dynamic expansion
  kenmoini.hyperv.vhd:
    path: "C:\Temp\my_vhd.vhdx"
    state: present
    size: 120GB
    dynamicExpansion: true

- name: Delete a VHD
  kenmoini.hyperv.vhd:
    name: "C:\Temp\my_vhd.vhdx"
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
```

### vhd_info

```yaml
- name: Get the information of a VHD File
  kenmoini.hyperv.vhd_info:
    path: "C:\Temp\my_vm.vhdx"
  register: r_vhd_info

- name: Print out the results
  debug:
    msg: "{{ r_vhd_info.json | from_json }}"
```

### vm

```yaml
- name: Create a VM
  kenmoini.hyperv.vm:
    name: my-vm
    state: present
    memory: 4GB
    cpu: 4
    network_switch: VMNetwork
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
    network_switch: WAN1
```

### vm_info

```yaml
- name: Get the information of a Virtual Machine called my-vm
  kenmoini.hyperv.vm_info:
    name: my-vm
  register: r_vm_info

- name: Print out the results
  debug:
    msg: "{{ r_vm_info.json | from_json }}"
```

### vmswitch

```yaml
- name: Create Virtual Switch bridged from Ethernet Adapter 1
  kenmoini.hyperv.vmswitch:
    name: VMNetwork
    state: present
    adapterName: Ethernet Adapter 1
    allowManagementOS: true

- name: Delete a Virtual Switch
  kenmoini.hyperv.vmswitch:
    name: VMNetwork
    state: absent

- name: Create an Internally routed Virtual Switch
  kenmoini.hyperv.vmswitch:
    name: natty
    state: present
    switchType: Internal

- name: Create a Private Virtual Switch
  kenmoini.hyperv.vmswitch:
    name: NoNet
    state: present
    switchType: Private
```

### vmswitch_info

```yaml
- name: Get the information of a Virtual Switch called VMNetwork
  kenmoini.hyperv.vmswitch_info:
    name: VMNetwork
  register: r_vmswitch_info

- name: Print out the results
  debug:
    msg: "{{ r_vmswitch_info.json | from_json }}"
```