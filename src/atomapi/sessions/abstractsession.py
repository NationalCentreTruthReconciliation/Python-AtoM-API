from abc import ABC, abstractmethod

class AbstractSession(ABC):
    def __init__(self, url: str, cache_credentials: bool = False):
        self.url = url.rstrip("/")
        self.cache_credentials = cache_credentials

    @abstractmethod
    def get_authorized_session(self):
        ''' Get an authorized session to interact with the AtoM instance '''
