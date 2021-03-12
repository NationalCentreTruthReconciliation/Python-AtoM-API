from atomapi.languages import ISO_639_1_LANGUAGES
from atomapi.utils import parse_url_from_string
from atomapi.models.taxonomy import Taxonomy
from atomapi.models.informationobject import InformationObject
from atomapi.authorizer import Authorizer, BasicAuthorizer


class Atom:
    def __init__(self, url: str, api_key: str = None, authorizer=None, **kwargs):
        parsed_url = parse_url_from_string(url.rstrip("/"))
        self.host = parsed_url.host
        self.url = str(parsed_url)
        self.api_key = api_key or ''

        self._lazy_session = None
        self._authorizer = authorizer
        self._taxonomies = None
        self._informationobjects = None

    def set_authorizer(self, authorizer: Authorizer):
        self._authorizer = authorizer

    def set_api_key(self, key: str):
        self.api_key = key

    @property
    def taxonomies(self) -> Taxonomy:
        ''' Access taxonomies with the browse() method. '''
        if self._taxonomies is None:
            self._taxonomies = Taxonomy(self)
        return self._taxonomies

    @property
    def informationobjects(self) -> InformationObject:
        ''' Read information objects with the read() method, or search for objects with the
        browse() method.
        '''
        if self._informationobjects is None:
            self._informationobjects = InformationObject(self)
        return self._informationobjects

    @property
    def _session(self):
        if self._lazy_session is None:
            if self._authorizer is None:
                self._authorizer = BasicAuthorizer(self.url)
            self._lazy_session = self._authorizer.authorize()
        return self._lazy_session

    def get(self, path: str, params: dict = None, sf_culture: str = 'en') -> tuple:
        ''' Make a request to the AtoM site.

        Args:
            path (str): The URL path to access. The path does not include the base URL
            params (dict): A dictionary of GET parameters to add to the request
            sf_culture (str): A two letter ISO 639-1 code used to select the language of results

        Returns:
            (tuple): A two-tuple containing the raw Response object and the URL requested
        '''
        if sf_culture not in ISO_639_1_LANGUAGES:
            raise ValueError(f'the language code "{sf_culture}" is not in the ISO 639-1 standard')
        if path.lstrip('/').startswith('api/'):
            if not self.api_key:
                raise ConnectionError('cannot access AtoM API without an API key set')
            headers = {'REST-API-Key': self.api_key}
        else:
            headers = {}
        if not params:
            params = {}
        if sf_culture:
            params['sf_culture'] = sf_culture
        request_url = self.url + '/' + path.lstrip('/')
        response = self._session.get(request_url, headers=headers, params=params)
        response.raise_for_status()
        return response, request_url
