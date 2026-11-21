# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""Shared implementation of the read-only ``*_info`` modules."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

from .api import UnifiNetworkClient, UnifiNetworkError
from .diff import remove_paths
from .args import info_argument_spec, info_mutually_exclusive
from .filters import FilterError, build_filter, render_condition, server_filterable
from .resource import fail_from_exception, resolve_site


def run_info_module(collection, result_key, site_scoped=True, id_lookup='path', id_aliases=(),
                    name_lookup='server', filters=True, secret_paths=()):
    """Run an ``_info`` module for a list endpoint and exit with ``{result_key: [...]}``.

    :param collection: API path below ``/v1/`` (or below the site when ``site_scoped``).
    :param id_lookup: ``'path'`` to GET ``<collection>/<id>``, ``'filter'`` to use ``id.eq()``,
        ``None`` when the module has no ``id`` option.
    :param name_lookup: ``'server'`` for ``name.eq()``, ``'client'`` to match after listing,
        ``None`` when the module has no ``name`` option.
    :param secret_paths: key paths (``'*'`` for list items) removed from every returned item.
    """
    spec = info_argument_spec(site=site_scoped, id_aliases=id_aliases if id_lookup else None,
                              name=name_lookup is not None, filters=filters)
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True,
                           mutually_exclusive=info_mutually_exclusive(spec))
    params = module.params
    if name_lookup == 'server' and params.get('name') is not None and not server_filterable(params['name']):
        name_lookup = 'client'
    try:
        filter_expr = None
        if filters or name_lookup == 'server':
            filter_expr = build_filter(
                filters=params.get('unifi_network_filters'),
                match=params.get('unifi_network_filters_match') or 'all',
                raw=params.get('unifi_network_filters_raw'),
                name=params.get('name') if name_lookup == 'server' else None,
            )
        client = UnifiNetworkClient.from_module(module)
        if site_scoped:
            base = '/v1/sites/%s/%s' % (resolve_site(module, client).site_id, collection)
        else:
            base = '/v1/%s' % collection

        item_id = params.get('id') if id_lookup else None
        if item_id and id_lookup == 'path':
            item = client.get_or_none('%s/%s' % (base, item_id))
            items = [item] if item else []
        else:
            if item_id:
                filter_expr = render_condition({'property': 'id', 'function': 'eq', 'value': item_id})
            client_side_name = name_lookup == 'client' and params.get('name') is not None
            items = client.paginate(base, filter_expr=filter_expr,
                                    max_items=None if client_side_name else params.get('limit'))
            if client_side_name:
                items = [i for i in items if i.get('name') == params['name']]
                if params.get('limit') is not None:
                    items = items[:params['limit']]
    except (UnifiNetworkError, FilterError) as exc:
        fail_from_exception(module, exc)
    if secret_paths:
        items = [remove_paths(item, secret_paths) for item in items]
    module.exit_json(changed=False, **{result_key: items})


def run_single_info_module(path_template, result_key, argument_spec, site_scoped=True, resolve=None):
    """Run an ``_info`` module for a single-object endpoint.

    ``path_template`` is relative to ``/v1/`` (or the site) and is formatted
    with ``site_id`` plus the path values from ``resolve(module, refs)``, which
    returns ``(path_values, query)``.
    """
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    try:
        client = UnifiNetworkClient.from_module(module)
        values, query, refs = {}, None, None
        if site_scoped:
            refs = resolve_site(module, client)
            values['site_id'] = refs.site_id
        if resolve:
            extra, query = resolve(module, refs)
            values.update(extra)
        prefix = '/v1/sites/{site_id}/' if site_scoped else '/v1/'
        data = client.get((prefix + path_template).format(**values), query=query)
    except (UnifiNetworkError, FilterError) as exc:
        fail_from_exception(module, exc)
    module.exit_json(changed=False, **{result_key: data})
