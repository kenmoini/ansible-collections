# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""Shared argument specs.  Each builder returns a fresh dict that is safe to mutate."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import env_fallback

from .api import DEFAULT_API_PATH


def connection_argument_spec():
    return dict(
        unifi_network_url=dict(type='str', required=True, aliases=['url'],
                               fallback=(env_fallback, ['UNIFI_NETWORK_URL', 'UNIFI_NETWORK_API'])),
        unifi_network_api_key=dict(type='str', required=True, no_log=True, aliases=['api_key'],
                                   fallback=(env_fallback, ['UNIFI_NETWORK_API_KEY'])),
        unifi_network_skip_tls_verify=dict(type='bool', default=False, aliases=['skip_tls_verify'],
                                           fallback=(env_fallback, ['UNIFI_NETWORK_SKIP_TLS_VERIFY'])),
        unifi_network_api_path=dict(type='str', default=DEFAULT_API_PATH, aliases=['api_path'],
                                    fallback=(env_fallback, ['UNIFI_NETWORK_API_PATH'])),
        unifi_network_timeout=dict(type='int', default=30, aliases=['request_timeout'],
                                   fallback=(env_fallback, ['UNIFI_NETWORK_TIMEOUT'])),
    )


def site_argument_spec():
    return dict(
        unifi_network_site_id=dict(type='str', required=True,
                                   aliases=['site', 'site_id', 'site_uuid', 'unifi_network_site', 'unifi_network_site_uuid'],
                                   fallback=(env_fallback, ['UNIFI_NETWORK_SITE_ID', 'UNIFI_NETWORK_SITE_UUID', 'UNIFI_NETWORK_SITE'])),
    )


def filter_argument_spec():
    return dict(
        unifi_network_filters=dict(type='raw', aliases=['filters', 'filter']),
        unifi_network_filters_match=dict(type='str', default='all', choices=['all', 'any'], aliases=['filters_match']),
        unifi_network_filters_raw=dict(type='str', aliases=['filters_raw', 'filter_raw']),
    )


def info_argument_spec(site=True, id_aliases=None, name=True, filters=True):
    """Build the argument spec for an ``_info`` module.

    :param id_aliases: ``None`` when the module has no ``id`` option, else the alias list.
    """
    spec = connection_argument_spec()
    if site:
        spec.update(site_argument_spec())
    if id_aliases is not None:
        spec['id'] = dict(type='str', aliases=list(id_aliases))
    if name:
        spec['name'] = dict(type='str')
    if filters:
        spec.update(filter_argument_spec())
    spec['limit'] = dict(type='int')
    return spec


def info_mutually_exclusive(spec):
    pairs = [
        ('id', 'name'), ('id', 'unifi_network_filters'), ('id', 'unifi_network_filters_raw'),
        ('unifi_network_filters', 'unifi_network_filters_raw'),
    ]
    return [list(p) for p in pairs if p[0] in spec and p[1] in spec]


def state_argument_spec(site=True, states=('present', 'absent'), default_state='present'):
    """Connection + site + ``state`` + ``id`` for state modules."""
    spec = connection_argument_spec()
    if site:
        spec.update(site_argument_spec())
    spec['state'] = dict(type='str', default=default_state, choices=list(states))
    spec['id'] = dict(type='str')
    return spec
