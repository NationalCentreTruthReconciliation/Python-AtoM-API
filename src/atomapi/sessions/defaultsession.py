import requests

from atomapi.sessions.abstractsession import AbstractSession

class DefaultSession(AbstractSession):
    def _create_new_session(self):
        try:
            return requests.Session()
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError(f'Could not connect to {self.url}. Make sure you are connected '
                                  'to the proper network to access the web address.') from exc
