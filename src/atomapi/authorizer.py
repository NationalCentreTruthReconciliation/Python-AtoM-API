from abc import ABC, abstractmethod
from functools import lru_cache
from urllib.parse import urljoin
import getpass

from requests import Session


class Authorizer(ABC):
    ''' A base class used to create an authorized session to access AtoM '''
    def __init__(self, url: str, **kwargs):
        self.url = url.rstrip('/')

    @abstractmethod
    def authorize(self) -> Session:
        ''' Create an authorized session to access the AtoM instance '''


class BasicAuthorizer(Authorizer):
    ''' Create a session with an "open" AtoM instance. An open AtoM instance does not require any
    sort of pre-access log in credentials.
    '''
    def authorize(self) -> Session:
        return Session()


@lru_cache(maxsize=10)
def prompt_for_username_password(prompt: str):
    print(prompt)
    username = ''
    while username == '':
        username = input('Username: ').strip()
    password = getpass.getpass()
    return {
        'username': username,
        'password': password,
    }


class F5Authorizer(Authorizer):
    def __init__(self, url: str, **kwargs):
        super().__init__(url, **kwargs)
        cache_creds = kwargs.get('cache_credentials') or False
        self.cache_credentials = bool(cache_creds)

    def authorize(self) -> Session:
        ''' Log in to F5 before returning the session '''
        session = Session()

        # Get initial session cookies
        _ = session.post(self.url)

        login_url = urljoin(self.url, 'my.policy')
        if not self.cache_credentials:
            prompt_for_username_password.cache_clear()
        login_data = prompt_for_username_password(f'Enter F5 credentials for {login_url}:')

        # Get authorization cookies
        response = session.post(login_url, data=login_data)

        # Raise error if there's an issue
        response.raise_for_status()
        if 'maximum number of concurrent user sessions' in response.text:
            raise ConnectionError('Too many users are logged in. Could not establish connection.')
        if 'password is not correct' in response.text:
            raise ConnectionError('The username or password was not correct.')
        if 'Access was denied by the access policy' in response.text:
            raise ConnectionError('Access to the server was denied. Make sure you have access to '
                                  'this AtoM instance.')
        return session
