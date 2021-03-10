import re

from atomapi.models.base import BaseModel


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
    'collection',
    'copyrightStatus',
    'creators',
    'endDate',
    'genres',
    'languages',
    'lastUpdated',
    'levels',
    'limit',
    'materialType',
    'mediatypes',
    'names',
    'onlyMedia',
    'places',
    'rangeType',
    'repos',
    'skip',
    'sort',
    'startDate',
    'subjects',
    'topLod',
)


class InformationObject(BaseModel):
    ''' Browse for or read information objects. Browsing involves searching for information objects,
    while reading involves fetching the metadata for a single object.
    '''

    def raise_for_json_error(self, json_response, request_url):
        if 'message' in json_response:
            if 'information object not found' in json_response['message'].lower():
                raise ConnectionError(f'No information object found at "{request_url}"')
        super().raise_for_json_error(json_response, request_url)

    @property
    def read_api_url(self):
        return '/api/informationobjects/{identifier}'

    def read(self, id_: str, sf_culture: str = 'en'):
        request_path = self.read_api_url.format(identifier=id_)
        response, url = self.atom.get(request_path, params=None, sf_culture=sf_culture)
        json_response = response.json()
        self.raise_for_json_error(json_response, url)
        return json_response

    @property
    def browse_api_url(self):
        ''' Use GET parameters to browse objects '''
        return '/api/informationobjects'

    def browse(self, sq: dict, sf: dict, so: dict, filters: dict, sf_culture: str = 'en'):
        self._validate_sq(sq)
        self._validate_sf(sf)
        self._validate_so(so)
        self._validate_filters(filters)
        params = {
            **sq,
            **sf,
            **so,
            **filters
        }
        response, url = self.atom.get(self.browse_api_url, params=params, sf_culture=sf_culture)
        json_response = response.json()
        self.raise_for_json_error(json_response, url)
        return json_response

    def _validate_sq(self, sq: dict):
        self._validate_query_parameters(sq, two_letter_code='sq')

    def _validate_sf(self, sf: dict):
        self._validate_query_parameters(sf, two_letter_code='sf')

    def _validate_so(self, so: dict):
        self._validate_query_parameters(so, two_letter_code='so')
        for value in so.values():
            if value not in ('and', 'or', 'not'):
                name = QUERY_VALIDATORS['so']['verbose_name']
                raise ValueError(f'{name} "{value}" was not one of: and, or, not')

    def _validate_query_parameters(self, queries: dict, two_letter_code: str):
        indices = set()
        regex = QUERY_VALIDATORS[two_letter_code]['regex']
        name = QUERY_VALIDATORS[two_letter_code]['verbose_name']
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
            if key not in VALID_FILTERS:
                raise ValueError(f'Filter Type "{key}" was not recognized')
            if not value:
                raise ValueError('Filter values may not be empty')
