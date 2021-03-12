from abc import ABC, abstractmethod
import concurrent.futures
import re

from bs4 import BeautifulSoup


class BaseModel(ABC):
    ''' The base class for all API models '''
    def __init__(self, atom):
        self.atom = atom

    def raise_for_json_error(self, json_response, request_url):
        ''' Check json response for error '''
        if 'message' in json_response:
            message = json_response['message']
            message_lower = message.lower()
            if 'endpoint not found' in message_lower:
                raise ConnectionError(f'Endpoint at "{request_url}" does not exist')
            if 'not authorized' in message_lower:
                raise ConnectionError(
                    f'You are not authorized to access "{request_url}" '
                    f'with the API Key "{self.atom.api_key}"'
                )
            raise ConnectionError(f'Error connecting to "{request_url}": {message}')


class VirtualBaseModel(ABC):
    ''' The base class for all virtual models. Virtual models scrape the AtoM front end as if it
    was an API.

    Since virtual models scrape the front end, they are prone to breaking if the HTML structure of
    AtoM's templates are changed, or if CSS class names are changed. This code has been tested for
    AtoM version 2.5 and 2.6 with the default theme, but may not work with other custom themes.

    The virtual models all work on the principle of scraping from an AtoM list. Lists are
    identifiable in AtoM by there being a page change element at the bottom of the list that shows
    the number of results.
    '''

    RESULT_LIMIT = 10
    MAX_THREAD_POOL_EXECUTORS = 5
    ACCEPTED_LANGUAGES = ('en', 'fr', 'es', 'nl', 'pt')
    RESULTS = re.compile(
        r'(?:Results|Résultats|Resultados|Resultaten)\s+'
        r'(?P<start>\d+)'
        r'\s+(?:to|à|a|tot)\s+'
        r'(?P<end>\d+)'
        r'\s+(?:of|sur|de|van)\s+'
        r'(?P<total>\d+)'
    )

    def __init__(self, atom):
        self._atom = atom

    @abstractmethod
    def parse_data_from_soup(self, html_soup):
        ''' Parse front end data from HTML soup. This is called for every page requested in
        scrape_html_list().

        Args:
            html_soup: A BeautifulSoup HTML page

        Returns:
            The objects parsed from the page. May be any type of object.
        '''

    def get_list_from_ui(self, path: str, sf_culture: str = 'en'):
        ''' Parse all data item from an AtoM list.

        Args:
            path (str): The generic path used to access the front end. This path string should have
            an unformatted {page} and {limit} parameter.

        Returns:
            (list): A list of parsed objects from the page. The type of objects depends on what the
            parse_data_from_soup() function returns.
        '''
        if sf_culture not in self.ACCEPTED_LANGUAGES:
            msg = (f'the language "{sf_culture}" is not supported for front-end scraping. '
                   f'Only these languages are supported: {", ".join(self.ACCEPTED_LANGUAGES)}')
            raise ValueError(msg)
        for param in (r'{page}', r'{limit}'):
            if param not in path:
                msg = 'the requested path does not have a '+param+' parameter - this is mandatory'
                raise ValueError(msg)

        urls = self._enumerate_list_urls(path, sf_culture)
        all_items = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_THREAD_POOL_EXECUTORS) as \
            executor:
            # Get the text from the webpage for each URL asynchronously
            web_requests = [executor.submit(self._get_page_content, u, sf_culture) for u in urls]
            # Process the HTML strings as they come in
            for future in concurrent.futures.as_completed(web_requests):
                response_text = future.result()
                html_soup = BeautifulSoup(response_text, 'html.parser')
                for item in self.parse_data_from_soup(html_soup):
                    all_items.append(item)
        return all_items

    def _enumerate_list_urls(self, raw_path: str, sf_culture: str) -> list:
        ''' Get the URL for every unique page in an AtoM list.

        Returns:
            (list): A list of all the URLs required to access every item in the AtoM list
        '''
        first_page_url = raw_path.format(page=1, limit=self.RESULT_LIMIT)
        total_items = self._get_total_list_items(first_page_url, sf_culture)
        all_urls = [first_page_url]
        # Start at page 2, go up by 10 items each time until total_items is reached
        for page_num, _ in enumerate(range(self.RESULT_LIMIT, total_items, self.RESULT_LIMIT), 2):
            new_url = raw_path.format(page=page_num, limit=self.RESULT_LIMIT)
            all_urls.append(new_url)
        return all_urls

    def _get_total_list_items(self, path: str, sf_culture: str):
        ''' Get the total number of items in a list from AtoM. Searches for a div element with the
        class 'result_count', and parses the total from the text in the div. The text in the result
        element should look like:

            Result 1 to 10 of 130

        The number 130 is returned as the total.

        Args:
            path (str): A path to an AtoM list page
            sf_culture (str): The language to get the content in

        Returns:
            (int): The total number of items AtoM reported are in the list
        '''
        response_text = self._get_page_content(path, sf_culture)
        text_soup = BeautifulSoup(response_text, 'html.parser')
        result_tag = text_soup.find('div', class_='result-count')
        results_match = self.RESULTS.search(str(result_tag))
        if not results_match:
            raise ConnectionError(f'Could not find total results in tag: {result_tag}')
        total_items = int(results_match.group('total'))
        return total_items

    def _get_page_content(self, path: str, sf_culture: str):
        ''' Get the raw HTML from a GET request to a URL.

        Args:
            url (str): A path to a web page.

        Returns:
            The raw HTML webpage content
        '''
        response, _ = self._atom.get(path, {}, {'Accept': 'text/html'}, sf_culture)
        return response.text
