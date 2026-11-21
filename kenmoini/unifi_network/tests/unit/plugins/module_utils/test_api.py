# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import io
import json

import pytest

from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from ansible_collections.kenmoini.unifi_network.plugins.module_utils import api
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import (
    UnifiNetworkApiError,
    UnifiNetworkClient,
)


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body if isinstance(body, bytes) else json.dumps(body).encode()

    def read(self):
        return self._body

    def getcode(self):
        return self.status


class FakeOpenUrl:
    """Stands in for ansible.module_utils.urls.open_url and records calls."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append(dict(url=url, **kwargs))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def http_error(code, body, msg='Error'):
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    return HTTPError('https://unifi/x', code, msg, {}, io.BytesIO(raw))


@pytest.fixture
def client():
    return UnifiNetworkClient(url='https://unifi.example.com/', api_key='k3y',
                              api_path='/proxy/network/integration', validate_certs=False, timeout=12)


def install(monkeypatch, responses):
    fake = FakeOpenUrl(responses)
    monkeypatch.setattr(api, 'open_url', fake)
    return fake


def query_of(call):
    return parse_qs(urlsplit(call['url']).query)


class TestRequest:
    def test_get_builds_url_headers_and_tls_options(self, client, monkeypatch):
        fake = install(monkeypatch, [FakeResponse(200, {'applicationVersion': '11.0.97'})])
        assert client.get('/v1/info') == {'applicationVersion': '11.0.97'}
        call = fake.calls[0]
        assert call['url'] == 'https://unifi.example.com/proxy/network/integration/v1/info'
        assert call['method'] == 'GET'
        assert call['headers']['X-API-Key'] == 'k3y'
        assert call['headers']['Accept'] == 'application/json'
        assert call['validate_certs'] is False
        assert call['timeout'] == 12
        assert call['data'] is None

    def test_post_sends_json_and_accepts_201(self, client, monkeypatch):
        fake = install(monkeypatch, [FakeResponse(201, {'id': 'n1', 'name': 'IoT'})])
        assert client.post('/v1/sites/s/networks', {'name': 'IoT'}) == {'id': 'n1', 'name': 'IoT'}
        assert json.loads(fake.calls[0]['data']) == {'name': 'IoT'}
        assert fake.calls[0]['headers']['Content-Type'] == 'application/json'

    def test_empty_success_body_returns_none(self, client, monkeypatch):
        install(monkeypatch, [FakeResponse(200, b'')])
        assert client.delete('/v1/sites/s/networks/n1') is None

    def test_query_is_percent_encoded(self, client, monkeypatch):
        fake = install(monkeypatch, [FakeResponse(200, b'')])
        client.delete('/v1/sites/s/hotspot/vouchers', query={'filter': "name.eq('a b')", 'force': None})
        url = fake.calls[0]['url']
        assert '+' not in url and '%20' in url
        assert query_of(fake.calls[0]) == {'filter': ["name.eq('a b')"]}

    def test_bool_query_values_are_lowercase(self, client, monkeypatch):
        fake = install(monkeypatch, [FakeResponse(200, b'')])
        client.delete('/v1/sites/s/networks/n1', query={'force': True})
        assert query_of(fake.calls[0]) == {'force': ['true']}


class TestErrors:
    def test_api_error_message_includes_details_and_hint(self, client, monkeypatch):
        body = {'statusCode': 404, 'statusName': 'NOT_FOUND', 'code': 'api.err.NotFound',
                'message': 'Network not found', 'requestId': 'req-1'}
        install(monkeypatch, [http_error(404, body)])
        with pytest.raises(UnifiNetworkApiError) as exc:
            client.get('/v1/sites/s/networks/n1')
        err = exc.value
        assert err.status == 404
        assert err.body == body
        text = str(err)
        assert 'GET /v1/sites/s/networks/n1' in text
        assert 'HTTP 404' in text
        assert 'api.err.NotFound' in text and 'Network not found' in text
        assert 'req-1' in text
        assert 'check the site and resource' in text.lower()

    def test_non_json_error_body_is_tolerated(self, client, monkeypatch):
        install(monkeypatch, [http_error(502, b'<html>Bad Gateway</html>', msg='Bad Gateway')])
        with pytest.raises(UnifiNetworkApiError) as exc:
            client.get('/v1/info')
        assert exc.value.status == 502
        assert 'Bad Gateway' in str(exc.value)

    def test_connection_error_is_wrapped(self, client, monkeypatch):
        install(monkeypatch, [URLError('connection refused')])
        with pytest.raises(UnifiNetworkApiError) as exc:
            client.get('/v1/info')
        assert exc.value.status is None
        assert 'connection refused' in str(exc.value)
        assert 'https://unifi.example.com' in str(exc.value)

    def test_get_or_none_returns_none_on_404(self, client, monkeypatch):
        install(monkeypatch, [http_error(404, {'code': 'api.err.NotFound', 'message': 'nope'})])
        assert client.get_or_none('/v1/sites/s/networks/missing') is None

    def test_get_or_none_reraises_other_errors(self, client, monkeypatch):
        install(monkeypatch, [http_error(401, {'code': 'api.err.Unauthorized', 'message': 'no'})])
        with pytest.raises(UnifiNetworkApiError):
            client.get_or_none('/v1/sites/s/networks/x')


def page(items, offset, total):
    return FakeResponse(200, {'offset': offset, 'limit': 200, 'count': len(items), 'totalCount': total, 'data': items})


class TestPaginate:
    def test_walks_all_pages(self, client, monkeypatch):
        fake = install(monkeypatch, [
            page(list(range(0, 200)), 0, 450),
            page(list(range(200, 400)), 200, 450),
            page(list(range(400, 450)), 400, 450),
        ])
        assert client.paginate('/v1/sites/s/clients') == list(range(450))
        assert [query_of(c)['offset'] for c in fake.calls] == [['0'], ['200'], ['400']]
        assert all(query_of(c)['limit'] == ['200'] for c in fake.calls)

    def test_passes_filter_on_every_page(self, client, monkeypatch):
        fake = install(monkeypatch, [page([1], 0, 2), page([2], 1, 2)])
        assert client.paginate('/v1/sites', filter_expr="name.eq('x')") == [1, 2]
        assert all(query_of(c)['filter'] == ["name.eq('x')"] for c in fake.calls)

    def test_max_items_limits_requests(self, client, monkeypatch):
        fake = install(monkeypatch, [page(list(range(200)), 0, 1000), page(list(range(200, 250)), 200, 1000)])
        assert client.paginate('/v1/sites/s/clients', max_items=250) == list(range(250))
        assert query_of(fake.calls[1])['limit'] == ['50']

    def test_stops_on_empty_page(self, client, monkeypatch):
        fake = install(monkeypatch, [page([1, 2], 0, 10), page([], 2, 10)])
        assert client.paginate('/v1/sites') == [1, 2]
        assert len(fake.calls) == 2

    def test_unpaged_list_response_is_returned_as_is(self, client, monkeypatch):
        install(monkeypatch, [FakeResponse(200, [{'id': 'a'}])])
        assert client.paginate('/v1/sites/s/wans') == [{'id': 'a'}]
