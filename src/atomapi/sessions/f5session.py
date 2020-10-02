from functools import lru_cache

from atomapi.sessions.defaultsession import DefaultSession
from atomapi.credentials import prompt_for_username_password

@lru_cache(maxsize=10)
def get_credentials(login_url):
    ''' Get a username and password to log in to F5 '''
    login_data = prompt_for_username_password(f'Enter F5 credentials for {login_url}:')
    return login_data

class F5Session(DefaultSession):
    def __init__(self, url: str, **kwargs):
        super().__init__(url)
        cache_creds = kwargs.get('cache_credentials')
        self.cache_credentials = bool(cache_creds)

    def _create_new_session(self):
        ''' Log in to F5 before returning the session '''
        session = super()._create_new_session()

        # Get initial session cookies
        _ = session.post(self.url)

        login_url = f'{self.url}/my.policy'
        if not self.cache_credentials:
            get_credentials.cache_clear()
        login_data = get_credentials(login_url)

        # Get authorization cookies
        response = session.post(login_url, data=login_data)

        response.raise_for_status()
        if 'maximum number of concurrent user sessions' in response.text:
            raise ConnectionError('Too many users are logged in. Could not establish connection.')
        if 'password is not correct' in response.text:
            raise ConnectionError('The username or password was not correct.')
        if 'Access was denied by the access policy' in response.text:
            raise ConnectionError('Access to the server was denied. Make sure you have access to '
                                  'this AtoM instance.')
        return session
