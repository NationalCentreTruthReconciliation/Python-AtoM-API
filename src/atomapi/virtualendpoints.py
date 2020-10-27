from abc import abstractmethod
from typing import Union
import re
import concurrent.futures
import urllib.parse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

from atomapi.endpoints import ApiEndpoint
from atomapi.sessions.abstractsession import AbstractSession


class VirtualApiEndpoint(ApiEndpoint):
    ''' A generic virtual API endpoint with caching capabilities. The virtual API is made to scrape
    data from an AtoM list view.
    '''

    RESULT_LIMIT = 10
    MAX_THREAD_POOL_EXECUTORS = 5
    USER_AGENT = 'Python requests v2'
    RESULTS = re.compile(r'Results\s(?P<start>\d+)\sto\s(?P<end>\d+)\sof\s(?P<total>\d+)')

    def __init__(self, session: AbstractSession, api_key: str = None,
                 sf_culture: str = None, **kwargs):
        super().__init__(session, None, sf_culture, **kwargs)
        if self.cache.cache_hours + self.cache.cache_minutes == 0:
            raise ValueError('You may not call a virtual API endpoint without caching, since '
                             'scraping the front-end puts a heavy load on the server.')
        robots_url = urllib.parse.urljoin(self.session.url, 'robots.txt')
        self.robots = RobotFileParser(robots_url)
        self._ignore_robots = False

    @property
    @abstractmethod
    def compatibility(self):
        ''' Explicitly define which version of AtoM and which themes the endpoint is compatible
        with.

        Returns:
            (str): A compatibility description
        '''

    @abstractmethod
    def parse_data_from_soup(self, html_soup):
        ''' Parse front end data from HTML soup.

        Args:
            html_soup: A BeautifulSoup HTML page

        Returns:
            The objects parsed from the page. May be any type of object.
        '''

    def _get_page_content(self, url: str):
        ''' Get the raw HTML from a GET request to a URL. Checks if the site allows web crawlers
        (like ourselves) to parse the page.

        Args:
            url (str): A url to a webpage

        Returns:
            The raw HTML webpage content
        '''
        if not self._ignore_robots: # I leave this decision to you
            if self.robots.last_checked == 0:
                self.robots.read()
            if not self.robots.can_fetch(self.USER_AGENT, url):
                raise ConnectionError(f'The robots.txt file for {self.session.url} does not permit '
                                      'web scraping by this application.')
        response = self.session.authorized_session.get(url, headers={'Accept': 'text/html'})
        response.raise_for_status()
        return response.text

    def _enumerate_list_urls(self, **url_kwargs):
        ''' Get the URL for every unique page in an AtoM list.

        Args:
            url_kwargs: A set of keyword arguments to apply to each URL generated. There is no
            need to pass the parameters for {page} or {limit} as those are automatically populated

        Returns:
            (list): A list of all the URLs required to access every item in the AtoM list
        '''
        first_page_url = urllib.parse.urljoin(
            self.session.url,
            self.api_url.format(
                limit=self.RESULT_LIMIT,
                page=1,
                **url_kwargs)
        )
        total_items = self._get_total_list_items(first_page_url)
        all_urls = [first_page_url]
        # Start at page 2, go up by 10 items each time until total_items is reached
        for page_num, _ in enumerate(range(self.RESULT_LIMIT, total_items, self.RESULT_LIMIT), 2):
            new_url = urllib.parse.urljoin(
                self.session.url,
                self.api_url.format(
                    limit=self.RESULT_LIMIT,
                    page=page_num,
                    **url_kwargs)
            )
            all_urls.append(new_url)
        return all_urls

    def _get_total_list_items(self, url: str):
        ''' Get the total number of items in a list from AtoM. Searches for a div element with the
        class 'result_count', and parses the total from the text in the div. The text in the result
        element should look like:

            Result 1 to 10 of 130

        The number 130 is returned as the total.

        Args:
            url (str): A url to an AtoM list page

        Returns:
            (int): The total number of items AtoM reported are in the list
        '''
        response_text = self._get_page_content(url)
        text_soup = BeautifulSoup(response_text, 'html.parser')
        result_tag = text_soup.find('div', class_='result-count')
        results_match = self.RESULTS.search(str(result_tag))
        if not results_match:
            raise ConnectionError(f'Could not find total results in tag: {result_tag}')
        total_items = int(results_match.group('total'))
        return total_items

    def _get_list_items(self, **url_kwargs):
        ''' Parse all data item from an AtoM list.

        Args:
            url_kwargs: Keyword arguments to apply to the api_url.

        Returns:
            (list): A list of parsed objects from the page. The type of objects depends on what the
            parse_data_from_soup() function returns.
        '''
        urls = self._enumerate_list_urls(**url_kwargs)
        all_items = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_THREAD_POOL_EXECUTORS) as \
            executor:
            # Get the text from the webpage for each URL asynchronously
            web_requests = [executor.submit(self._get_page_content, u) for u in urls]
            # Process the HTML strings as they come in
            for future in concurrent.futures.as_completed(web_requests):
                response_text = future.result()
                html_soup = BeautifulSoup(response_text, 'html.parser')
                for item in self.parse_data_from_soup(html_soup):
                    all_items.append(item)
        return all_items


class VirtualNoParameterApiEndpoint(VirtualApiEndpoint):
    ''' Represents a virtual API endpoint that does not require any parameters to fetch data '''
    def _get_cache_id(self, **kwargs):
        return self.endpoint_name

    def get(self):
        if self.cache.hours + self.cache.minutes == 0:
            raise ValueError('You may not call a virtual API endpoint without caching, since '
                             'scraping the front-end puts a heavy load on the server.')
        cached_items = self.cache.retrieve(self._get_cache_id())
        if cached_items:
            return cached_items
        all_items = self._get_list_items()
        self.cache.store(self._get_cache_id(), all_items)
        return all_items


class VirtualSingleParameterApiEndpoint(VirtualApiEndpoint):
    ''' Represents a virtual API endpoint that requires a single parameters to fetch data '''
    def _get_cache_id(self, **kwargs):
        object_id = kwargs.get('object_id')
        return f'{self.endpoint_name}_{object_id}'

    def get(self, object_id: Union[str, int]):
        if self.cache.hours + self.cache.minutes == 0:
            raise ValueError('You may not call a virtual API endpoint without caching, since '
                             'scraping the front-end puts a heavy load on the server.')
        cached_items = self.cache.retrieve(self._get_cache_id(object_id=object_id))
        if cached_items:
            return cached_items
        all_items = self._get_list_items(id=object_id)
        self.cache.store(self._get_cache_id(object_id=object_id), all_items)
        return all_items


class VirtualBrowseAuthorityEndpoint(VirtualNoParameterApiEndpoint):
    @property
    def compatibility(self):
        return ''' Verified to be compatible with AtoM Version 2.5, using the default
        arDominionPlugin theme.
        '''

    @property
    def api_url(self):
        return '/actor/browse?page={page}&limit={limit}'

    @property
    def endpoint_name(self):
        return 'authority_names'

    def parse_data_from_soup(self, html_soup):
        for element in html_soup.find_all('p', class_='title'):
            anchor_tag = element.find('a')
            if anchor_tag:
                yield {'name': anchor_tag.string}


class VirtualBrowseAuthorityRefCodeEndpoint(VirtualNoParameterApiEndpoint):
    @property
    def compatibility(self):
        return ''' Verified to be compatible with AtoM Version 2.5, using the default
        arDominionPlugin theme.
        '''

    @property
    def api_url(self):
        return '/actor/browse?page={page}&limit={limit}'

    @property
    def endpoint_name(self):
        return 'authority_names_with_ref_codes'

    def parse_data_from_soup(self, html_soup):
        for element in html_soup.find_all('article', class_='search-result'):
            authority_name = ''
            reference_code = ''

            title_anchor_tag = element.find('p', class_='title').find('a')
            if not title_anchor_tag:
                continue
            authority_name = title_anchor_tag.string

            ref_code_li_tag = element.find('li', class_='reference-code')
            if ref_code_li_tag:
                reference_code = ref_code_li_tag.string

            yield {'name': authority_name, 'code': reference_code}


class VirtualBrowseTaxonomyEndpoint(VirtualSingleParameterApiEndpoint):
    @property
    def compatibility(self):
        return ''' Verified to be compatible with AtoM Version 2.5, using the default
        arDominionPlugin theme.
        '''

    @property
    def api_url(self):
        return '/taxonomy/index/id/{id}?page={page}&limit={limit}'

    @property
    def endpoint_name(self):
        return 'virtual_browse_taxonomy'

    def parse_data_from_soup(self, html_soup):
        for element in html_soup.find_all('td'):
            anchor_tag = element.find('a')
            if anchor_tag:
                yield {'name': anchor_tag.string}
