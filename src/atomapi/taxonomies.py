from enum import Enum


class DefaultTaxonomyIds(Enum):
    ''' It is possible to change what IDs AtoM uses for these taxonomies, so use these only if
    you're sure the IDs have not been changed.
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


def _get_generic_taxonomies_from_soup(soup):
    for element in soup.find_all('td'):
        anchor_tag = element.find('a')
        if anchor_tag:
            yield anchor_tag.string

def _get_authorities_from_soup(soup):
    for element in soup.find_all('p', class_='title'):
        anchor_tag = element.find('a')
        if anchor_tag:
            yield anchor_tag.string

def _get_authorities_from_soup_with_ref_codes(soup):
    for element in soup.find_all('article', class_='search-result'):
        authority_name = ''
        reference_code = ''

        title_anchor_tag = element.find('p', class_='title').find('a')
        if not title_anchor_tag:
            continue
        else:
            authority_name = title_anchor_tag.string

        ref_code_li_tag = element.find('li', class_='reference-code')
        if ref_code_li_tag:
            reference_code = ref_code_li_tag.string

        yield (reference_code, authority_name)

# Add new virtual taxonomies here
virtual_taxonomies = {
    42: {
        'description': 'Gets all place taxonomies',
        'scrape_url': '{atom_url}/taxonomy/index/id/{id}?page={page}&limit={limit}',
        'parser': _get_generic_taxonomies_from_soup,
    },
    35: {
        'description': 'Gets all subject taxonomies',
        'scrape_url': '{atom_url}/taxonomy/index/id/{id}?page={page}&limit={limit}',
        'parser': _get_generic_taxonomies_from_soup,
    },
    78: {
        'description': 'Gets all genre taxonomies',
        'scrape_url': '{atom_url}/taxonomy/index/id/{id}?page={page}&limit={limit}',
        'parser': _get_generic_taxonomies_from_soup,
    },
    101: {
        'description': 'Gets all authority names',
        'scrape_url': '{atom_url}/actor/browse?page={page}&limit={limit}',
        'parser': _get_authorities_from_soup,
    },
    102: {
        'description': 'Gets all authority names and their reference codes (if they exist)',
        'scrape_url': '{atom_url}/actor/browse?page={page}&limit={limit}',
        'parser': _get_authorities_from_soup_with_ref_codes
    },
}
