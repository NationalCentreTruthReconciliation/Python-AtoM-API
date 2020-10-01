from atomapi.sessions.defaultsession import DefaultSession
from atomapi.credentials import prompt_for_username_password
from atomapi.cache import ObfuscatedCache

class F5Session(DefaultSession):
    def __init__(self, url: str, **kwargs):
        super().__init__(url)
        cache_creds = kwargs.get('cache_credentials')
        if not cache_creds:
            self.cache_credentials = False
        else:
            self.cache_credentials = True
        if self.cache_credentials:
            self.cache = ObfuscatedCache(expire_hours=8, expire_minutes=0, prefix='f5session')
        else:
            self.cache = None

    def _create_new_session(self):
        ''' Log in to F5 before returning the session '''
        session = super()._create_new_session()

        _ = session.post(self.url)

        login_url = f'{self.url}/my.policy'

        if self.cache:
            login_data = self.cache.retrieve('f5_user_pass')
        if not self.cache or not self.cache.hit:
            login_data = prompt_for_username_password(f'Enter F5 credentials for {login_url}:')

        response = session.post(login_url, data=login_data)
        response.raise_for_status()

        if 'maximum number of concurrent user sessions' in response.text:
            raise ConnectionError('Too many users are logged in. Could not establish connection.')
        if 'password is not correct' in response.text:
            raise ConnectionError('The username or password was not correct.')
        if 'Access was denied by the access policy' in response.text:
            raise ConnectionError('Access to the server was denied. Make sure you have access to '
                                  'this AtoM instance.')

        if self.cache and not self.cache.hit:
            self.cache.store('f5_user_pass', login_data)
        return session
