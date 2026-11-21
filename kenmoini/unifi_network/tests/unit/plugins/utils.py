# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""Run an Ansible module's ``main()`` in-process and capture its result."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils import basic
from ansible.module_utils.testing import patch_module_args

BASE_ARGS = dict(
    unifi_network_url='https://unifi.test',
    unifi_network_api_key='test-key',
    unifi_network_site_id='default',
)


class AnsibleExit(Exception):
    def __init__(self, result):
        super(AnsibleExit, self).__init__(result)
        self.result = result


class AnsibleFail(Exception):
    def __init__(self, result):
        super(AnsibleFail, self).__init__(result.get('msg'))
        self.result = result


def _exit_json(self, **kwargs):
    kwargs.setdefault('changed', False)
    raise AnsibleExit(kwargs)


def _fail_json(self, msg, **kwargs):
    kwargs['msg'] = msg
    kwargs['failed'] = True
    raise AnsibleFail(kwargs)


def run_module(main, args, monkeypatch, check_mode=False, diff=False, site=True):
    """Run ``main`` with ``args`` (merged over connection defaults); return the exit_json result.

    ``AnsibleFail`` propagates so tests can ``pytest.raises`` it.
    """
    full = dict(BASE_ARGS)
    if not site:
        full.pop('unifi_network_site_id')
    full.update(args)
    if check_mode:
        full['_ansible_check_mode'] = True
    if diff:
        full['_ansible_diff'] = True
    monkeypatch.setattr(basic.AnsibleModule, 'exit_json', _exit_json)
    monkeypatch.setattr(basic.AnsibleModule, 'fail_json', _fail_json)
    with patch_module_args(full):
        try:
            main()
        except AnsibleExit as exc:
            return exc.result
    raise AssertionError('module did not call exit_json or fail_json')
