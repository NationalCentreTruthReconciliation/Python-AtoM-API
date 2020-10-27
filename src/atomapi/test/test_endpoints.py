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
