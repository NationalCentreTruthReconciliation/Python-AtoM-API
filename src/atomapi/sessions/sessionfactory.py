class SessionFactory:
    def __init__(self):
        self._session_types = {}

    def register_session_type(self, name, klass):
        self._session_types[name] = klass

    def create(self, name: str, url: str, cache_credentials: bool):
        if name not in self._session_types:
            raise ValueError(f'The session type "{name}" does not exist.')
        klass = self._session_types[name]
        return klass(url=url, cache_credentials=cache_credentials)

    @property
    def session_types(self):
        return list(self._session_types.keys())