import re
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Union

from atomapi.cache import Cache
from atomapi.sessions.abstractsession import AbstractSession
from atomapi.languages import ISO_639_1_LANGUAGES


class ApiEndpoint(ABC):
    ''' A generic API endpoint with caching capabilities '''
    def __init__(self, session: AbstractSession, api_key: str,
                 cache_hours: int = 1, cache_minutes: int = 0,
                 sf_culture: str = None):
        self.cache = Cache(expire_hours=cache_hours, expire_minutes=cache_minutes,
                           prefix=session.host)
        self.api_key = api_key
        self.session = session
        if sf_culture and sf_culture not in ISO_639_1_LANGUAGES:
            raise ValueError(f'The language code "{sf_culture}" does not appear in ISO 639-1')
        self.sf_culture = sf_culture or None

    @property
    @abstractmethod
    def endpoint_name(self):
        ''' Unique name for this API endpoint '''

    @property
    @abstractmethod
    def api_url(self):
        ''' API url segment used to access endpoint. Must start with a slash '''

    @abstractmethod
    def _get_cache_id(self, **kwargs):
        ''' Create a unique identifier for caching API result '''


class SingleParameterApiEndpoint(ApiEndpoint):
    ''' Represents an API endpoint that only requires a single unique identifier to fetch a piece of
    data.
    '''
    def _get_cache_id(self, **kwargs):
        object_id = kwargs.get('object_id')
        return f'{self.endpoint_name}_{object_id}'

    def get(self, object_id: Union[str, int]):
        ''' Make a GET request to the API, using the object_id to populate the {identifier} in the
        api_url.

        Args:
            object_id (Union[str, int]): The identifier used to fetch an object from the API

        Returns:
            (dict): The object received from the API.
        '''
        if not self.api_key:
            raise ValueError('No API key is specified, cannot access API without it')
        object_id = str(object_id)
        if self.cache.hours + self.cache.minutes > 0:
            cached_object = self.cache.retrieve(self._get_cache_id(object_id=object_id))
            if cached_object:
                return cached_object
        url = self.session.url + self.api_url.format(identifier=object_id)
        headers = {'REST-API-Key': self.api_key}
        params = {'sf_culture': self.sf_culture} if self.sf_culture else {}
        response = self.session.authorized_session.get(url, headers=headers, params=params)
        response.raise_for_status()
        json_response = response.json()
        if 'message' in json_response:
            if 'Endpoint not found' in json_response['message']:
                raise ConnectionError(f'Endpoint at "{url}" does not exist')
            return json_response
        if self.cache.hours + self.cache.minutes > 0:
            self.cache.store(self._get_cache_id(object_id=object_id), json_response)
        return json_response


class BrowseTaxonomyEndpoint(SingleParameterApiEndpoint):
    @property
    def api_url(self):
        return '/api/taxonomies/{identifier}'

    @property
    def endpoint_name(self):
        return 'browse-taxonomies'


class ReadInformationObjectEndpoint(SingleParameterApiEndpoint):
    @property
    def api_url(self):
        return '/api/informationobjects/{identifier}'

    @property
    def endpoint_name(self):
        return 'read-object'


class BrowseInformationObjectEndpoint(ApiEndpoint):
    QUERY_VALIDATORS = {
        'sq': {
            'verbose_name': 'Query String',
            'regex': re.compile(r'^sq(?P<index>\d+)$')
        },
        'sf': {
            'verbose_name': 'Field String',
            'regex': re.compile(r'^sf(?P<index>\d+)$'),
        },
        'so': {
            'verbose_name': 'Operator String',
            'regex': re.compile(r'^so(?P<index>\d+)$'),
        },
    }

    VALID_FILTERS = (
        'limit'
        'skip'
        'sort'
        'lastUpdated'
        'topLod'
        'onlyMedia'
        'copyrightStatus',
        'materialType',
        'languages',
        'levels',
        'mediatypes',
        'repos',
        'places',
        'subjects',
        'genres',
        'creators',
        'names',
        'collection',
        'startDate',
        'endDate',
        'rangeType'
    )

    @property
    def api_url(self):
        return '/api/informationobjects'

    @property
    def endpoint_name(self):
        return 'browse-objects'

    def _get_cache_id(self, **kwargs):
        sq = kwargs.get('sq') or {}
        sf = kwargs.get('sf') or {}
        so = kwargs.get('so') or {}
        filters = kwargs.get('filters') or {}
        combined_dict = {
            **sq,
            **sf,
            **so,
            **filters
        }
        unique_string = json.dumps(combined_dict).encode('utf-8')
        md5_hash = hashlib.md5()
        md5_hash.update(unique_string)
        return f'browse-objects_{md5_hash.hexdigest()}'

    def _validate_sq(self, sq: dict):
        self._validate_query_parameters(sq, two_letter_code='sq')

    def _validate_sf(self, sf: dict):
        self._validate_query_parameters(sf, two_letter_code='sf')

    def _validate_so(self, so: dict):
        self._validate_query_parameters(so, two_letter_code='so')
        for value in so.values():
            if value not in ('and', 'or', 'not'):
                name = self.QUERY_VALIDATORS['so']['verbose_name']
                raise ValueError(f'{name} "{value}" was not one of: and, or, not')

    def _validate_query_parameters(self, queries: dict, two_letter_code: str):
        indices = set()
        regex = self.QUERY_VALIDATORS[two_letter_code]['regex']
        name = self.QUERY_VALIDATORS[two_letter_code]['verbose_name']
        for key, value in queries.items():
            match_obj = regex.match(key)
            if not match_obj:
                raise ValueError(f'{name} "{key}" did not start with "{two_letter_code}", followed '
                                 'by one or more numbers')
            curr_index = int(match_obj.group('index'))
            if curr_index in indices:
                raise ValueError(f'{name} with index "{curr_index}" was specified more than once')
            indices.add(curr_index)
            if not value:
                raise ValueError(f'{name}s may not be empty')

    def _validate_filters(self, filters: dict):
        for key, value in filters.items():
            if key not in self.VALID_FILTERS:
                raise ValueError(f'Filter Type "{key}" was not recognized')
            if not value:
                raise ValueError('Filter values may not be empty')

    def get(self, sq: dict, sf: dict, so: dict, filters: dict):
        ''' Make a GET request to the API to search for information objects matching the queries
        and filters.

        Args:
            sq (dict): Query strings, used to select objects containing a certain string in a field.
            Each should be in the form 'sqX': 'Some String', where X is an int
            sf (dict): Field strings, used to select which fields the query strings apply to. Each
            should be in the form 'sfX': 'Some Field', where F is an int
            so (dict): Operator strings, used to logically combine multiple queries. Each should be
            in the form 'soX': 'Some Operator', where X is an int. Valid operators are and, or, not
            filters (dict): Additional filters, used to filter the objects in ways that are not
            possible with query strings alone, e.g., by date. Each should be in the form
            'filterName': 'value'

        Returns:
            (dict): The selected information objects
        '''
        if not self.api_key:
            raise ValueError('No API key is specified, cannot access API without it')
        self._validate_sq(sq)
        self._validate_sf(sf)
        self._validate_so(so)
        self._validate_filters(filters)

        if self.cache.hours + self.cache.minutes > 0:
            cached_object = self.cache.retrieve(self._get_cache_id(
                sq=sq,
                sf=sf,
                so=so,
                filters=filters)
            )
            if cached_object:
                return cached_object

        url = self.session.url + self.api_url
        headers = {'REST-API-Key': self.api_key}
        params = {
            **sq,
            **sf,
            **so,
            **filters
        }
        if self.sf_culture:
            params['sf_culture'] = self.sf_culture

        response = self.session.authorized_session.get(url, headers=headers, params=params)
        response.raise_for_status()
        json_response = response.json()
        if 'message' in json_response:
            if 'Endpoint not found' in json_response['message']:
                raise ConnectionError(f'Endpoint at "{url}" does not exist')
            return json_response

        if self.cache.hours + self.cache.minutes > 0:
            self.cache.store(self._get_cache_id(
                sq=sq,
                sf=sf,
                so=so,
                filters=filters
            ), json_response)

        return json_response


class VirtualBrowseTaxonomyEndpoint(BrowseTaxonomyEndpoint):
    ''' Represents a front-end endpoint that is being treated as an API endpoint. '''

    RESULT_LIMIT = 10
    RESULTS = re.compile(r'Results\s(?P<start>\d+)\sto\s(?P<end>\d+)\sof\s(?P<total>\d+)')

    def __init__(self, session: AbstractSession, api_key=None, cache_hours=1, cache_minutes=0):
        # No API Key is necessary for virtual endpoints
        super().__init__(session, None, cache_hours, cache_minutes)

    def call(self, object_id):
        if self.cache.hours + self.cache.minutes == 0:
            raise ValueError('You may not call a virtual API endpoint without caching, since '
                             'scraping the front-end puts a heavy load on the server.')
        if object_id not in virtual_taxonomies:
            raise ValueError(f'The virtual taxonomy with id "{object_id}" has not been registered')
        cached_items = self.cache.retrieve(object_id)
        if cached_items:
            return cached_items
        all_items = self._scrape_items_from_frontend(object_id)
        self.cache.store(object_id, all_items)
        return all_items

    def _get_virtual_scrape_url(self, object_id):
        if object_id not in virtual_taxonomies:
            raise ValueError(f'The virtual taxonomy with id "{object_id}" has not been registered')
        return virtual_taxonomies[object_id]['scrape_url']

    def _get_virtual_soup_parser(self, object_id):
        if object_id not in virtual_taxonomies:
            raise ValueError(f'The virtual taxonomy with id "{object_id}" has not been registered')
        return virtual_taxonomies[object_id]['parser']

    def _scrape_items_from_frontend(self, object_id):
        all_items = []
        result = self._get_page_urls_and_first_page_content(object_id)
        first_page_contents = result['response_text']
        urls = result['urls_for_page_2+']
        parser = self._get_virtual_soup_parser(object_id)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            web_requests = [executor.submit(self._get_page_content, u) for u in urls]
            web_requests.append(executor.submit(lambda: first_page_contents))
            for future in concurrent.futures.as_completed(web_requests):
                html_soup = BeautifulSoup(future.result(), 'html.parser')
                for item in parser(html_soup):
                    all_items.append(item)
        return all_items

    def _get_page_urls_and_first_page_content(self, object_id):
        unpopulated_url = self._get_virtual_scrape_url(object_id)

        first_page_url = unpopulated_url.format(
            atom_url=self.session.url,
            id=object_id,
            limit=self.RESULT_LIMIT,
            page=1)

        response_text = self._get_page_content(first_page_url)
        text_soup = BeautifulSoup(response_text, 'html.parser')
        result_tag = text_soup.find('div', class_='result-count')
        results_match = self.RESULTS.search(str(result_tag))
        if not results_match:
            raise ConnectionError(f'Could not find total results in tag: {result_tag}')

        total_items = int(results_match.group('total'))
        items_accounted_for = 10
        page_num = 2
        all_urls = []
        while items_accounted_for < total_items:
            all_urls.append(unpopulated_url.format(
                atom_url=self.session.url,
                id=object_id,
                limit=self.RESULT_LIMIT,
                page=page_num)
            )
            items_accounted_for += self.RESULT_LIMIT
            page_num += 1

        return {
            'urls_for_page_2+': all_urls,
            'response_text': response_text
        }

    def _get_page_content(self, url):
        response = self.session.authorized_session.get(url, headers={'Accept': 'text/html'})
        response.raise_for_status()
        if 'maximum number of concurrent user sessions' in response.text:
            raise ConnectionError('Too many users are logged in, could not establish connection.')
        return response.text
