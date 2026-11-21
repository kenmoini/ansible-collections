# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

"""HTTP client for the UniFi Network Integration API."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import socket

from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode

from ansible.module_utils.urls import open_url

DEFAULT_API_PATH = '/proxy/network/integrations'
PAGE_SIZE = 200

_STATUS_HINTS = {
    400: 'The request was rejected as invalid; check the module parameters.',
    401: 'Authentication failed; check the API key.',
    403: 'The API key is not permitted to perform this action.',
    404: 'The resource was not found; check the site and resource IDs/names.',
    409: 'The request conflicts with the current state (for example a duplicate name, or a resource that is still referenced).',
}
_SERVER_ERROR_HINT = 'The UniFi Network application reported a server error; check the controller logs and try again.'


class UnifiNetworkError(Exception):
    """Base error for this collection; modules turn it into ``fail_json``."""


class UnifiNetworkApiError(UnifiNetworkError):
    """An error talking to the UniFi Network API.

    ``status`` is the HTTP status (``None`` for connection failures) and
    ``body`` the decoded error payload when the API returned one.
    """

    def __init__(self, message, status=None, body=None):
        super(UnifiNetworkApiError, self).__init__(message)
        self.status = status
        self.body = body


def _decode(raw):
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')
    if not raw.strip():
        return None
    return json.loads(raw)


def _query_value(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return value


def _format_http_error(method, path, status, reason, body, raw):
    parts = ['%s %s failed with HTTP %s' % (method, path, status)]
    if isinstance(body, dict):
        label = body.get('statusName') or reason
        if label:
            parts[0] += ' %s' % label
        detail = ' - '.join(str(body[k]) for k in ('code', 'message') if body.get(k))
        if detail:
            parts.append(detail)
        if body.get('requestId'):
            parts.append('requestId: %s' % body['requestId'])
    else:
        if reason:
            parts[0] += ' %s' % reason
        text = raw.decode('utf-8', errors='replace').strip() if isinstance(raw, bytes) else (raw or '')
        if text:
            parts.append(text[:300])
    hint = _STATUS_HINTS.get(status) or (_SERVER_ERROR_HINT if status and status >= 500 else None)
    if hint:
        parts.append(hint)
    return '. '.join(parts)


class UnifiNetworkClient(object):
    """Thin JSON client: builds URLs, sends requests, maps errors, paginates."""

    def __init__(self, url, api_key, api_path=DEFAULT_API_PATH, validate_certs=True, timeout=30):
        self.base_url = url.rstrip('/') + '/' + (api_path or '').strip('/')
        self.base_url = self.base_url.rstrip('/')
        self.api_key = api_key
        self.validate_certs = validate_certs
        self.timeout = timeout

    @classmethod
    def from_module(cls, module):
        params = module.params
        return cls(
            url=params['unifi_network_url'],
            api_key=params['unifi_network_api_key'],
            api_path=params.get('unifi_network_api_path') or DEFAULT_API_PATH,
            validate_certs=not params.get('unifi_network_skip_tls_verify', False),
            timeout=params.get('unifi_network_timeout') or 30,
        )

    def url_for(self, path, query=None):
        url = self.base_url + path
        if query:
            pairs = [(k, _query_value(v)) for k, v in query.items() if v is not None]
            if pairs:
                url += '?' + urlencode(pairs, quote_via=quote, safe='')
        return url

    def request(self, method, path, query=None, body=None):
        url = self.url_for(path, query)
        headers = {'X-API-Key': self.api_key, 'Accept': 'application/json'}
        data = None
        if body is not None:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(body)
        try:
            response = open_url(url, method=method, headers=headers, data=data,
                                validate_certs=self.validate_certs, timeout=self.timeout)
            raw = response.read()
        except HTTPError as exc:
            raw = exc.read() if exc.fp is not None else b''
            try:
                err_body = _decode(raw)
            except ValueError:
                err_body = None
            raise UnifiNetworkApiError(_format_http_error(method, path, exc.code, exc.reason, err_body, raw),
                                       status=exc.code, body=err_body)
        except (URLError, socket.timeout, ConnectionError, OSError) as exc:
            reason = getattr(exc, 'reason', exc)
            raise UnifiNetworkApiError('%s %s failed: could not connect to %s: %s' % (method, path, self.base_url, reason))
        try:
            return _decode(raw)
        except ValueError:
            raise UnifiNetworkApiError('%s %s returned a response that is not valid JSON: %r' % (method, path, raw[:300]))

    def get(self, path, query=None):
        return self.request('GET', path, query=query)

    def get_or_none(self, path, query=None):
        try:
            return self.get(path, query=query)
        except UnifiNetworkApiError as exc:
            if exc.status == 404:
                return None
            raise

    def post(self, path, body, query=None):
        return self.request('POST', path, query=query, body=body)

    def put(self, path, body, query=None):
        return self.request('PUT', path, query=query, body=body)

    def patch(self, path, body, query=None):
        return self.request('PATCH', path, query=query, body=body)

    def delete(self, path, query=None):
        return self.request('DELETE', path, query=query)

    def paginate(self, path, filter_expr=None, max_items=None, page_size=PAGE_SIZE):
        """Return every item of a paginated list endpoint (up to ``max_items``)."""
        items = []
        offset = 0
        while True:
            limit = page_size
            if max_items is not None:
                limit = min(page_size, max_items - len(items))
                if limit <= 0:
                    break
            page = self.get(path, query={'offset': offset, 'limit': limit, 'filter': filter_expr})
            if isinstance(page, list):
                return page if max_items is None else page[:max_items]
            data = (page or {}).get('data') or []
            items.extend(data)
            total = (page or {}).get('totalCount')
            if not data or (total is not None and offset + len(data) >= total):
                break
            offset += len(data)
        return items
