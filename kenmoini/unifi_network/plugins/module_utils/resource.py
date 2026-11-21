# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""Idempotent ``state: present|absent`` engine shared by the resource modules.

Flow for ``present``: find the object (by ``id`` or natural key), build the
desired API fragment from the options the user set, then create it, leave it
alone when it already matches, or PUT the current object merged with the
desired fragment (PUT is full replacement in this API).  ``absent`` deletes
when found.  Check mode predicts the result without writing, and ``--diff``
reports before/after.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

from .api import UnifiNetworkClient, UnifiNetworkError, UnifiNetworkApiError
from .diff import is_subset, merge, prune_none, remove_paths, strip_keys
from .filters import FilterError, build_filter, server_filterable
from .references import ReferenceResolver


def fail_from_exception(module, exc):
    details = {}
    if isinstance(exc, UnifiNetworkApiError):
        details = dict(status=exc.status, response=exc.body)
    module.fail_json(msg=str(exc), **details)


def lookup_path(obj, dotted):
    """Return the value at a dotted key path such as ``source.zoneId``, or ``None``."""
    for part in dotted.split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def origin_of(obj):
    return ((obj or {}).get('metadata') or {}).get('origin')


def resolve_site(module, client):
    refs = ReferenceResolver(client)
    refs.site_id = refs.resolve('site', module.params['unifi_network_site_id'])
    return refs


class StateResource(object):
    """Base class for idempotent resource modules.

    Subclasses set ``path`` (collection under the site), ``result_key``,
    ``label`` and implement ``to_api()``.  ``create_required`` maps API keys
    required on create to the option names reported when they are missing.
    """

    path = None
    result_key = None
    label = None
    read_only_keys = ('id', 'metadata')
    create_required = {}
    secret_paths = ()
    secret_update_param = None
    supports_force = False

    def __init__(self, module, client=None):
        self.module = module
        self.params = module.params
        self.client = client or UnifiNetworkClient.from_module(module)
        self.refs = resolve_site(module, self.client)
        self.site_id = self.refs.site_id

    # ---- paths --------------------------------------------------------
    @property
    def collection_path(self):
        return '/v1/sites/%s/%s' % (self.site_id, self.path)

    def item_path(self, item_id):
        return '%s/%s' % (self.collection_path, item_id)

    # ---- hooks --------------------------------------------------------
    def to_api(self, current):
        """Return the desired API fragment built only from options the user set.

        ``current`` is the existing object, or ``None`` when it will be created.
        """
        raise NotImplementedError

    def lookup_filter(self):
        if not server_filterable(self.params['name']):
            return None
        return build_filter(name=self.params['name'])

    def lookup_match(self, item):
        return item.get('name') == self.params['name']

    def lookup_description(self):
        return 'named %r' % self.params['name']

    def create_defaults(self):
        return {}

    def required_for_create(self, payload):
        """Return ``{api_key: option_name}`` that must be set to create ``payload``; keys may be dotted paths."""
        return self.create_required

    def check_updatable(self, current, desired):
        """Raise ``UnifiNetworkError`` when ``current`` may not be changed this way."""

    def update_request(self, current, desired):
        """Return ``(method, body)`` for an update; subclasses may PATCH or refuse."""
        return 'PUT', prune_none(merge(strip_keys(current, self.read_only_keys), desired))

    def check_deletable(self, current):
        """Raise ``UnifiNetworkError`` when ``current`` must not be deleted."""

    def delete_query(self):
        if self.supports_force and self.params.get('force'):
            return {'force': True}
        return None

    # ---- engine -------------------------------------------------------
    def find(self):
        item_id = self.params.get('id')
        if item_id:
            return self.client.get_or_none(self.item_path(item_id))
        items = self.client.paginate(self.collection_path, filter_expr=self.lookup_filter())
        matches = [item for item in items if self.lookup_match(item)]
        if len(matches) > 1:
            raise UnifiNetworkError('More than one %s %s exists (ids: %s); set id to choose one' % (
                self.label, self.lookup_description(), ', '.join(m['id'] for m in matches)))
        if not matches:
            return None
        # List endpoints may return a reduced overview; compare and update against the full object.
        return self.client.get(self.item_path(matches[0]['id']))

    def mask(self, obj):
        if not obj:
            return {}
        return remove_paths(obj, self.secret_paths)

    def force_secret_update(self, desired):
        if not self.secret_update_param or self.params.get(self.secret_update_param) != 'always':
            return False
        return any(remove_paths(desired, [p]) != desired for p in self.secret_paths)

    def finish(self, changed, before, after):
        result = {'changed': changed, self.result_key: self.mask(after)}
        if self.module._diff:
            result['diff'] = {'before': self.mask(before), 'after': self.mask(after)}
        self.module.exit_json(**result)

    def ensure_present(self, current):
        desired = self.to_api(current)
        if current is None:
            if self.params.get('id'):
                raise UnifiNetworkError('No %s with id %s exists; omit id to create one' % (self.label, self.params['id']))
            payload = prune_none(merge(self.create_defaults(), desired))
            missing = [opt for key, opt in self.required_for_create(payload).items() if lookup_path(payload, key) in (None, '', [])]
            if missing:
                raise UnifiNetworkError('Creating a %s requires: %s' % (self.label, ', '.join(sorted(missing))))
            created = payload if self.module.check_mode else self.client.post(self.collection_path, payload)
            return self.finish(True, None, created)

        compare = remove_paths(desired, self.secret_paths)
        if is_subset(compare, current) and not self.force_secret_update(desired):
            return self.finish(False, current, current)

        self.check_updatable(current, desired)
        method, body = self.update_request(current, desired)
        if self.module.check_mode:
            if method == 'PUT':
                # PUT replaces the object: the result is the body plus the read-only keys the API keeps.
                kept = dict((k, current[k]) for k in self.read_only_keys if k in current)
                updated = prune_none(merge(kept, body))
            else:
                updated = prune_none(merge(current, body))
        else:
            updated = self.client.request(method, self.item_path(current['id']), body=body)
        return self.finish(True, current, updated)

    def ensure_absent(self, current):
        if current is None:
            return self.finish(False, None, None)
        self.check_deletable(current)
        if not self.module.check_mode:
            self.client.delete(self.item_path(current['id']), query=self.delete_query())
        return self.finish(True, current, None)

    def run(self):
        current = self.find()
        if self.params['state'] == 'absent':
            return self.ensure_absent(current)
        return self.ensure_present(current)


def run_state_module(resource_cls, argument_spec, **module_kwargs):
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, **module_kwargs)
    try:
        resource_cls(module).run()
    except (UnifiNetworkError, FilterError) as exc:
        fail_from_exception(module, exc)
