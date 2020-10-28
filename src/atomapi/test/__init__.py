from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position,no-name-in-module,import-error
from sessions.abstractsession import AbstractSession
from cache import Cache


class ExampleSession(AbstractSession):
    ''' A new session type that is used for testing purposes only '''

    class AuthorizedSession:
        class FakeResponse:
            def raise_for_status(self):
                pass
            def json(self):
                return {}

        def get(self, url, **kwargs):
            return self.FakeResponse()

    def __init__(self, url: str, **kwargs):
        super().__init__(url, **kwargs)
        self.last_session_created = None
        self.user = kwargs.get('user')

    def _create_new_session(self):
        session = self.AuthorizedSession()
        self.last_session_created = session
        return session

class InMemoryCache(Cache):
    def __init__(self, expire_hours=1, expire_minutes=0, prefix=None):
        super().__init__(expire_hours, expire_minutes, prefix)
        self.memory_cache = {}
        self.last_object_cached = None

    def _write_object_to_disk(self, location, obj):
        self.memory_cache[location] = obj
        self.last_object_cached = obj[self.OBJECT_FIELD]

    def _read_object_from_disk(self, location):
        if location in self.memory_cache:
            return self.memory_cache[location]
        raise FileNotFoundError(f'Path not found: "{location}"')

    def get_storage_location(self, name):
        return f'{self.prefix}_name' if self.prefix else name