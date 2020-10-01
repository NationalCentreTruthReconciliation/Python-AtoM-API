''' Facilitates fetching taxonomies and authority names from an AtoM database
'''

import re
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
        if sf_culture not in ISO_639_1_LANGUAGES:
            raise ValueError(f'The language code "{sf_culture}" does not appear in ISO 639-1')
        self.sf_culture = sf_culture


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
    pass


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
