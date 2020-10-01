''' Facilitates fetching taxonomies and authority names from an AtoM database
'''

import re
import hashlib
import json
import concurrent.futures
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from atomapi.cache import Cache
from atomapi.sessions.abstractsession import AbstractSession
from atomapi.taxonomies import virtual_taxonomies
from atomapi.languages import ISO_639_1_LANGUAGES


class ApiEndpoint(ABC):
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


class SingleParameterApiEndpoint(ApiEndpoint):
    @property
    @abstractmethod
    def endpoint_name(self):
        ''' Unique name for API endpoint '''

    @property
    @abstractmethod
    def api_url(self):
        ''' API url segment used to access browse endpoint. Must start with a slash, and must have
        an unpopulated {identifier}.
        '''

    def get_cache_id(self, object_id):
        return f'{self.endpoint_name}_{object_id}'

    def call(self, object_id):
        if not self.api_key:
            raise ValueError('No API key is specified, cannot access API without it')
        object_id = str(object_id)
        if self.cache.hours + self.cache.minutes > 0:
            cached_object = self.cache.retrieve(self.get_cache_id(object_id))
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
            self.cache.store(self.get_cache_id(object_id), json_response)
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
        return 'read-information-object'


class BrowseInformationObjectEndpoint(ApiEndpoint):
    @property
    def api_url(self):
        return '/api/informationobjects'

    SQ_KEY = re.compile(r'^sq\d+$')
    def _validate_sq(self, sq: dict):
        for key, value in sq.items():
            if not self.SQ_KEY.match(key):
                raise ValueError(f'Query String "{key}" must start with "sq" and be followed by '
                                 'one or more numbers')
            if not value:
                raise ValueError('Query strings may not be empty')

    SF_KEY = re.compile(r'^sf\d+$')
    def _validate_sf(self, sf: dict):
        for key, value in sf.items():
            if not self.SF_KEY.match(key):
                raise ValueError(f'Field String "{key}" must start with "sf" and be followed by '
                                 'one or more numbers')
            if not value:
                raise ValueError('Field strings may not be empty')

    SO_KEY = re.compile(r'^so\d+$')
    def _validate_so(self, so: dict):
        for key, value in so.items():
            if not self.SO_KEY.match(key):
                raise ValueError(f'Operator String "{key}" must start with "so" and be followed by '
                                 'one or more numbers')
            if not value:
                raise ValueError('Operator strings may not be empty')

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
    def _validate_filters(self, filters: dict):
        for key, value in filters.items():
            if key not in self.VALID_FILTERS:
                raise ValueError(f'Filter Type "{key}" was not recognized')
            if not value:
                raise ValueError('Filter values may not be empty')

    def get_cache_id(self, sq: dict, sf: dict, so: dict, filters: dict):
        combined_dict = {
            **sq,
            **sf,
            **so,
            **filters
        }
        unique_string = json.dumps(combined_dict).encode('utf-8')
        md5_hash = hashlib.md5()
        md5_hash.update(unique_string)
        return f'browse-information-object_{md5_hash.hexdigest()}'

    def call(self, sq: dict, sf: dict, so: dict, filters: dict):
        if not self.api_key:
            raise ValueError('No API key is specified, cannot access API without it')
        self._validate_sq(sq)
        self._validate_sf(sf)
        self._validate_so(so)
        self._validate_filters(filters)

        if self.cache.hours + self.cache.minutes > 0:
            cached_object = self.cache.retrieve(self.get_cache_id(sq, sf, so, filters))
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
            self.cache.store(self.get_cache_id(sq, sf, so, filters), json_response)

        return json_response


class VirtualBrowseTaxonomyEndpoint(BrowseTaxonomyEndpoint):
    ''' Represents a front-end endpoint that is being treated as an API endpoint. '''

    RESULT_LIMIT = 10
    RESULTS = re.compile(r'Results\s(?P<start>\d+)\sto\s(?P<end>\d+)\sof\s(?P<total>\d+)')

    def __init__(self, session: AbstractSession, api_key=None, cache_hours=1, cache_minutes=0):
        # No API Key is necessary for virtual endpoints
        super().__init__(session, None, cache_hours, cache_minutes)
        self.api_url = None

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
