Role Name
=========

The `kenmoini.kemo.architecture_helper` role provides a few normalized architecture variables to use across different system types.

Requirements
------------

None.

Role Variables
--------------

None.

Dependencies
------------

None.

Example Playbook
----------------


The `kenmoini.kemo.architecture_helper` role provides a few normalized architecture variables to use across different system types.

```yaml
---
- name: example for kenmoini.kemo.architecture_helper
  hosts: some_host_pattern
  tasks:
    - name: import role
      import_role:
        name: kenmoini.kemo.architecture_helper

    - name: Debug set variables
      ansible.builtin.debug:
        msg:
          - "detected_architecture: {{ detected_architecture }}"
          - "deb_architecture: {{ deb_architecture }}"
          - "rpm_architecture: {{ rpm_architecture }}"
```

The set variables can help when downloading binaries, ISOs, etc.

License
-------

MIT

Author Information
------------------

Ken Moini <ken@kenmoini.com>
