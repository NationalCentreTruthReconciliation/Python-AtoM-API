from abc import ABC, abstractmethod
from atomapi.utils import parse_url_from_string

class AbstractSession(ABC):
    def __init__(self, url: str, **kwargs):
        parsed_url = parse_url_from_string(url.rstrip("/"))
        self.host = parsed_url.host
        self.url = str(parsed_url)
        self.session_is_authorized = False
        self.__auth_session = None

    @property
    def authorized_session(self):
        ''' Get an authorized session to interact with the AtoM instance '''
        if not self.session_is_authorized:
            self.__auth_session = self._create_new_session()
            self.session_is_authorized = True
        return self.__auth_session

    @abstractmethod
    def _create_new_session(self):
        pass
