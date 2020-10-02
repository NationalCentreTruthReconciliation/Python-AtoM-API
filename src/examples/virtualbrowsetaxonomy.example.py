''' Feel free to play around with this script and use your own AtoM instance and
API Key.

Virtual taxonomies fetch data from the front end, treating it as an API. As
such, this type of call can put stress on the server, so caching is mandatory.
If you disable the cache, you will get an exception.
'''
from atomapi.sessions import session_factory
from atomapi.taxonomies import DefaultTaxonomyIds
from atomapi.virtualendpoints import VirtualBrowseTaxonomyEndpoint

session = session_factory.create('default', 'https://youratom.ca')

# You don't need an API key to access the front end
taxonomies = VirtualBrowseTaxonomyEndpoint(session)

# You can still use the normal taxonomy IDs for the front end, just like with the API
subjects = taxonomies.get(DefaultTaxonomyIds.SUBJECTS.value)

print('Subjects:')
print(subjects)
