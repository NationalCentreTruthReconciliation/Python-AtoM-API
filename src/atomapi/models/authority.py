from atomapi.models.base import VirtualBaseModel

class VirtualAuthority(VirtualBaseModel):
    ''' Browse a list of all of the authorities in AtoM. AtoM does not have an API to fetch
    authorities, so they must be scraped from the front-end. Authorities can be fetched with the
    browse() method.

    Each authority has the following attributes:

    +--------------+-------------------------------------------------+
    |**Attribute** |**Description**                                  |
    +--------------+-------------------------------------------------+
    |name          |The name of an authority                         |
    +--------------+-------------------------------------------------+
    |reference_code|The reference code of an authority, if it has one|
    +--------------+-------------------------------------------------+
    '''

    @property
    def raw_page_path(self):
        return '/actor/browse?page={page}&limit={limit}'

    def browse(self, sf_culture: str = 'en'):
        ''' Get a complete list of all authorities from the AtoM frontend.

        Args:
            sf_culture (str): The language to fetch results in, defaults to 'en'

        Returns:
            (list): A list of authorities. Each authority is a dict with a name, and a
            reference_code. The reference_code may be empty if the authority doesn't have one.
        '''
        return self.get_list_from_ui(self.raw_page_path, sieve_soup=self._extract_authorities,
                                     sf_culture=sf_culture)

    def _extract_authorities(self, html_soup):
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

            yield {'name': authority_name, 'reference_code': reference_code}
