from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests

from atomapi.languages import ISO_639_1_LANGUAGES
from atomapi.utils import parse_url_from_string
from atomapi.models.taxonomy import Taxonomy, VirtualTaxonomy
from atomapi.models.authority import VirtualAuthority
from atomapi.models.informationobject import InformationObject
from atomapi.authorizer import Authorizer, BasicAuthorizer


class Atom:
    ''' The top-level class that manages access to an AtoM instance '''

    USER_AGENT = 'Python requests v2'

    def __init__(self, url: str, api_key: str = None, authorizer=None):
        parsed_url = parse_url_from_string(url.rstrip("/"))
        self.host = parsed_url.host
        self.url = str(parsed_url)
        self.api_key = api_key or ''
        self._ignore_robots = False
        self.robots = RobotFileParser(urljoin(self.url, 'robots.txt'))
        self._authorizer = authorizer

        # Lazily-evaluated objects
        self._session = None
        self._taxonomies = None
        self._informationobjects = None
        self._virtual_taxonomies = None
        self._virtual_authorities = None

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
    def v_taxonomies(self) -> VirtualTaxonomy:
        ''' Scrape taxonomies from the frontend with the browse() method. '''
        if self._virtual_taxonomies is None:
            self._virtual_taxonomies = VirtualTaxonomy(self)
        return self._virtual_taxonomies

    @property
    def v_authorities(self) -> VirtualAuthority:
        ''' Scrape authorities from the frontend with the browse() method. '''
        if self._virtual_authorities is None:
            self._virtual_authorities = VirtualAuthority(self)
        return self._virtual_authorities

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            if self._authorizer is None:
                self._authorizer = BasicAuthorizer(self.url)
            self._session = self._authorizer.authorize()
        return self._session

    def get(self, path: str, params: dict = None, headers: dict = None,
            sf_culture: str = 'en') -> tuple:
        ''' Make a GET request to the AtoM site.

        Args:
            path (str): The URL path to access. The path does not include the base URL
            params (dict): A dictionary of GET parameters to add to the request
            headers (dict): A dictionary of headers (other than the REST-API-Key header) to send
            with the GET request
            sf_culture (str): A two letter ISO 639-1 code used to select the language of results

        Returns:
            (tuple): A two-tuple containing the raw Response object and the URL requested
        '''
        if sf_culture not in ISO_639_1_LANGUAGES:
            raise ValueError(f'the language code "{sf_culture}" is not in the ISO 639-1 standard')

        request_url = urljoin(self.url, path)
        request_headers = headers or {}
        request_params = params or {}
        if sf_culture:
            request_params['sf_culture'] = sf_culture

        if path.lstrip('/').startswith('api/'):
            if not self.api_key:
                raise ConnectionError('cannot access AtoM API without an API key set')
            request_headers['REST-API-Key'] = self.api_key
        elif not self._ignore_robots:
            if self.robots.last_checked == 0:
                self.robots.read()
            if not self.robots.can_fetch(self.USER_AGENT, request_url):
                raise ConnectionError(f'The robots.txt file for {self.url} does not permit '
                                      'web scraping by this application.')

        response = self.session.get(request_url, headers=request_headers, params=request_params)
        response.raise_for_status()
        return response, request_url

    def reset_connection(self):
        ''' Reset the connection to the AtoM instance. The authorizer will be asked for a new
        session when the the next request is made.
        '''
        self._session = None
