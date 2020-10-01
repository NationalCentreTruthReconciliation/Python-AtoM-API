from abc import ABC, abstractmethod
from atomapi.utils import parse_url_from_string

class AbstractSession(ABC):
    def __init__(self, url: str, cache_credentials: bool = False):
        parsed_url = parse_url_from_string(url.rstrip("/"))
        self.host = parsed_url.host
        self.url = str(parsed_url)
        self.cache_credentials = cache_credentials
        self.session_is_authorized = False
        self.__auth_session = None

    @abstractmethod
    def get_authorized_session(self):
        ''' Get an authorized session to interact with the AtoM instance '''