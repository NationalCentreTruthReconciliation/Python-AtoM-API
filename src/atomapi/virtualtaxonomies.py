''' Controls for the virtual taxonomies. Since these are not explicitly defined in the AtoM API, it
is necessary to keep them separate from the rest of the API code.

All virtual taxonomies leverage the front end to get data.
'''

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
virtual_endpoints = {
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
