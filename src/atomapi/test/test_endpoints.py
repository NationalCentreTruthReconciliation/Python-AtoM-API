from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position,no-name-in-module,import-error
from . import ExampleSession, InMemoryCache
from endpoints import BrowseTaxonomyEndpoint


class TestTaxonomyEndpoint:
    def test_instance_variables_set(self):
        session = ExampleSession('https://example.com')
        cache = InMemoryCache()
        endpoint = BrowseTaxonomyEndpoint(session, '123456', 'fr', cache=cache)
        assert endpoint.cache == cache
        assert endpoint.session == session
        assert endpoint.sf_culture == 'fr'
        assert endpoint.api_key == '123456'

    def test_taxonomies_retrieved(self, monkeypatch):
        taxonomies = [
            {'name': 'Taxonomy 1'},
            {'name': 'Taxonomy 2'},
        ]
        monkeypatch.setattr(ExampleSession.AuthorizedSession.FakeResponse, 'json',
                            lambda _: taxonomies)

        session = ExampleSession('https://example.com')
        cache = InMemoryCache()
        endpoint = BrowseTaxonomyEndpoint(session, '123456', cache=cache)

        response = endpoint.get(1)

        assert response == taxonomies

    def test_taxonomies_cached(self, monkeypatch):
        taxonomies = [
            {'name': 'Taxonomy 1'},
            {'name': 'Taxonomy 2'},
        ]
        monkeypatch.setattr(ExampleSession.AuthorizedSession.FakeResponse, 'json',
                            lambda _: taxonomies)

        session = ExampleSession('https://example.com')
        cache = InMemoryCache()
        endpoint = BrowseTaxonomyEndpoint(session, '123456', cache=cache)

        _ = endpoint.get(1)

        assert endpoint.cache.last_object_cached == taxonomies

    def test_taxonomies_retrieved_from_cache(self, monkeypatch):
        taxonomies = [
            {'name': 'Taxonomy 1'},
            {'name': 'Taxonomy 2'},
        ]
        monkeypatch.setattr(ExampleSession.AuthorizedSession.FakeResponse, 'json',
                            lambda _: taxonomies)

        session = ExampleSession('https://example.com')
        cache = InMemoryCache()
        endpoint = BrowseTaxonomyEndpoint(session, '123456', cache=cache)

        result = endpoint.get(1)
        assert not endpoint.cache.hit
        result = endpoint.get(1)
        assert endpoint.cache.hit
        assert result == taxonomies

    def test_different_taxonomies_cached_separately(self, monkeypatch):
        taxonomies_1 = [
            {'name': 'Taxonomy 1'},
            {'name': 'Taxonomy 2'},
        ]

        taxonomies_2 = [
            {'name': 'Taxonomy 3'},
            {'name': 'Taxonomy 4'},
        ]

        session = ExampleSession('https://example.com')
        cache = InMemoryCache()
        endpoint = BrowseTaxonomyEndpoint(session, '123456', cache=cache)

        # Get taxonomies_1 cached
        monkeypatch.setattr(ExampleSession.AuthorizedSession.FakeResponse, 'json',
                            lambda _: taxonomies_1)
        _ = endpoint.get(1)
        assert endpoint.cache.last_object_cached == taxonomies_1

        # Get taxonomies_2 cached
        monkeypatch.setattr(ExampleSession.AuthorizedSession.FakeResponse, 'json',
                            lambda _: taxonomies_2)
        _ = endpoint.get(2)
        assert endpoint.cache.last_object_cached == taxonomies_2

        # Retrieve taxonomies_1 from cache
        cached_result = endpoint.get(1)
        assert endpoint.cache.hit
        assert cached_result == taxonomies_1

        # Retrieve taxonomies_2 from cache
        cached_result = endpoint.get(2)
        assert endpoint.cache.hit
        assert cached_result == taxonomies_2

    @pytest.mark.parametrize('error', [
        'Endpoint not found',
        'Not authorized',
        'Taxonomy not found',
        'Internal Server Error',
    ])
    def test_error_raised_if_message_in_json(self, error, monkeypatch):
        monkeypatch.setattr(ExampleSession.AuthorizedSession.FakeResponse, 'json',
                            lambda _: {'message': error})

        session = ExampleSession('https://example.com')
        cache = InMemoryCache()
        endpoint = BrowseTaxonomyEndpoint(session, '123456', cache=cache)

        with pytest.raises(ConnectionError):
            _ = endpoint.get(1)
