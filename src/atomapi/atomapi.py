''' Facilitates fetching taxonomies and authority names from an AtoM database
'''

import re
import concurrent.futures
from abc import ABC
from enum import Enum
from typing import Union

from bs4 import BeautifulSoup

from atomapi.cache import Cache
from atomapi.sessions.abstractsession import AbstractSession
from atomapi.virtualtaxonomies import virtual_endpoints


class ApiEndpoint(ABC):
    def __init__(self, session: AbstractSession, api_key, cache_hours=1, cache_minutes=0):
        self.cache = Cache(expire_hours=cache_hours, expire_minutes=cache_minutes,
                           prefix=session.host)
        self.api_key = api_key
        self.session = session


class TaxonomyEndpoint(ApiEndpoint):
    class Ids(Enum):
        PLACES = 42
        SUBJECTS = 35
        GENRES = 78
        LEVEL_OF_DESCRIPTION = 34
        ACTOR_ENTITY_TYPE = 32
        THEMATIC_AREA = 72
        GEOGRAPHIC_SUBREGION = 73
        MEDIA_TYPE = 46
        RAD_TITLE_NOTE_TYPE = 52
        RAD_OTHER_NOTE_TYPE = 51
        MATERIAL_TYPE = 50
        DACS_NOTE_TYPE = 74
        RIGHTS_ACT = 67
        RIGHTS_BASIS = 68

    def __init__(self, session: AbstractSession, api_key, cache_hours=1, cache_minutes=0):
        super().__init__(session, api_key, cache_hours, cache_minutes)
        self.api_url = f'{self.session.url}/api/taxonomies/' + '{id}'

    def get_terms(self, taxonomy_id: Union[Ids, int]):
        if not self.api_key:
            raise ValueError('No API key is specified, cannot access API without it')
        if isinstance(taxonomy_id, TaxonomyEndpoint.Ids):
            taxonomy_id = taxonomy_id.value
        cached_terms = self.cache.retrieve(taxonomy_id)
        if cached_terms:
            return cached_terms
        url = self.api_url.format(id=taxonomy_id)
        response = self.session.authorized_session.get(url, headers={'REST-API-Key': self.api_key})
        response.raise_for_status()
        json_response = response.json()
        if 'message' in json_response and ('Taxonomy not found' in json_response['message'] or \
            'Endpoint not found' in json_response['message']):
            return []
        taxonomies = [item['name'] for item in json_response]
        self.cache.store(taxonomy_id, taxonomies)
        return taxonomies


class VirtualTaxonomyEndpoint(TaxonomyEndpoint):
    ''' Represents a front-end endpoint that is being treated as an API endpoint. '''

    RESULT_LIMIT = 10
    RESULTS = re.compile(r'Results\s(?P<start>\d+)\sto\s(?P<end>\d+)\sof\s(?P<total>\d+)')

    def __init__(self, session: AbstractSession, api_key=None, cache_hours=1, cache_minutes=0):
        # No API Key is necessary for virtual endpoints
        super().__init__(session, None, cache_hours, cache_minutes)
        self.api_url = None

    def get_terms(self, taxonomy_id):
        if self.cache.hours == 0:
            raise ValueError('You may call a virtual API endpoint with cache_hours set to zero, '
                             'since scraping the front-end puts a heavy load on the server.')
        if taxonomy_id not in virtual_endpoints:
            raise ValueError(f'The virtual taxonomy with id {taxonomy_id} has not been registered')
        cached_items = self.cache.retrieve(taxonomy_id)
        if cached_items:
            return cached_items
        all_items = self._scrape_items_from_frontend(taxonomy_id)
        self.cache.store(taxonomy_id, all_items)
        return all_items

    def _get_virtual_scrape_url(self, taxonomy_id):
        if taxonomy_id not in virtual_endpoints:
            raise ValueError(f'The virtual taxonomy with id {taxonomy_id} has not been registered')
        return virtual_endpoints[taxonomy_id]['scrape_url']

    def _get_virtual_soup_parser(self, taxonomy_id):
        if taxonomy_id not in virtual_endpoints:
            raise ValueError(f'The virtual taxonomy with id {taxonomy_id} has not been registered')
        return virtual_endpoints[taxonomy_id]['parser']

    def _scrape_items_from_frontend(self, taxonomy_id):
        all_items = []
        result = self._get_page_urls_and_first_page_content(taxonomy_id)
        first_page_contents = result['response_text']
        urls = result['urls_for_page_2+']
        parser = self._get_virtual_soup_parser(taxonomy_id)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            web_requests = [executor.submit(self._get_page_content, u) for u in urls]
            web_requests.append(executor.submit(lambda: first_page_contents))
            for future in concurrent.futures.as_completed(web_requests):
                html_soup = BeautifulSoup(future.result(), 'html.parser')
                for item in parser(html_soup):
                    all_items.append(item)
        return all_items

    def _get_page_urls_and_first_page_content(self, taxonomy_id):
        unpopulated_url = self._get_virtual_scrape_url(taxonomy_id)

        first_page_url = unpopulated_url.format(
            atom_url=self.session.url,
            id=taxonomy_id,
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
                id=taxonomy_id,
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
