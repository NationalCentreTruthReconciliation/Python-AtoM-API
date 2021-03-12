from enum import Enum
from typing import Union

from atomapi.models.base import BaseModel, VirtualBaseModel
from atomapi.utils import partial_format


class TaxonomyId(Enum):
    ''' AtoM's default ID number for each taxonomy type

    See:
    https://www.accesstomemory.org/fr/docs/2.6/dev-manual/api/browse-taxonomies/#api-browse-taxonomies
    '''
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

    @staticmethod
    def from_str(label: str):
        clean_label = label.strip().upper()
        parsed = getattr(TaxonomyId, clean_label, None)
        if parsed is None:
            raise ValueError(f'Could not parse taxonomy ID from "{label}"')
        return parsed


class Taxonomy(BaseModel):
    ''' Browse a list of taxonomy terms. Terms can be viewed with the browse() method.

    Each has the following attributes:

    +-------------+--------------------------------+
    |**Attribute**|**Description**                 |
    +-------------+--------------------------------+
    |name         |The name of a taxonomy term     |
    +-------------+--------------------------------+
    '''

    @property
    def api_url(self):
        return '/api/taxonomies/{identifier}'

    def raise_for_json_error(self, json_response, request_url):
        if 'message' in json_response:
            if 'taxonomy not found' in json_response['message'].lower():
                raise ConnectionError(f'No taxonomies found at "{request_url}"')
        super().raise_for_json_error(json_response, request_url)

    def _parse_id(self, id_: Union[str, TaxonomyId, int]):
        if isinstance(id_, str):
            object_id = TaxonomyId.from_str(id_).value
        elif isinstance(id_, TaxonomyId):
            object_id = id_.value
        else:
            object_id = id_
        return object_id

    def browse(self, id_: Union[str, TaxonomyId, int], sf_culture: str = 'en') -> list:
        ''' Get a complete list of taxonomies of one type from AtoM.

        To browse the place taxonomies, for example, you can do one of three things:

        1. Pass the name of the taxonomy, with: browse('places')
        2. Pass the TaxonomyId for places, with: browse(TaxonomyId.PLACES)
        3. Pass the raw integer ID of the taxonomy, with: browse(42)

        Args:
            id_ (Union[str, int, TaxonomyId]): The taxonomy selector
            sf_culture (str): The language to fetch taxonomies in, default to 'en'

        Returns:
            (list): A list of taxonomy terms. Each term is a dictionary with a "name" key
        '''
        object_id = self._parse_id(id_)
        request_path = self.api_url.format(identifier=object_id)
        return self.get_json(request_path, None, sf_culture)


class VirtualTaxonomy(VirtualBaseModel):
    @property
    def raw_page_path(self):
        return '/taxonomy/index/id/{identifier}?page={page}&limit={limit}'

    def _parse_id(self, id_: Union[str, TaxonomyId, int]):
        if isinstance(id_, str):
            object_id = TaxonomyId.from_str(id_).value
        elif isinstance(id_, TaxonomyId):
            object_id = id_.value
        else:
            object_id = id_
        return object_id

    def browse(self, id_: Union[str, TaxonomyId, int], sf_culture: str = 'en') -> list:
        ''' Get a complete list of taxonomies of one type from AtoM.

        To browse the place taxonomies, for example, you can do one of three things:

        1. Pass the name of the taxonomy, with: browse('places')
        2. Pass the TaxonomyId for places, with: browse(TaxonomyId.PLACES)
        3. Pass the raw integer ID of the taxonomy, with: browse(42)

        Args:
            id_ (Union[str, int, TaxonomyId]): The taxonomy selector
            sf_culture (str): The language to fetch taxonomies in, default to 'en'

        Returns:
            (list): A list of taxonomy terms. Each term is a dictionary with a "name" key
        '''
        object_id = self._parse_id(id_)
        page_path = partial_format(self.raw_page_path, identifier=object_id)
        return self.get_list_from_ui(page_path, sf_culture)

    def parse_data_from_soup(self, html_soup):
        for element in html_soup.find_all('td'):
            anchor_tag = element.find('a')
            if anchor_tag:
                yield {'name': anchor_tag.string}
