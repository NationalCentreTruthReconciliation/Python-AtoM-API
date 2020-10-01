''' Feel free to play around with this script and use your own AtoM instance and
API Key.

Virtual taxonomies fetch data from the front end, treating it as an API. As
such, this type of call can put stress on the server, so caching is mandatory.
If you disable the cache, you will get an exception.
'''
from atomapi.sessions import session_factory
from atomapi.endpoints import VirtualBrowseTaxonomyEndpoint
from atomapi.taxonomies import virtual_taxonomies

session = session_factory.create('default', 'https://nctrpublic.ad.umanitoba.ca')

# You don't need an API key to access the front end
taxonomies = VirtualBrowseTaxonomyEndpoint(session)

print('These are the registered virtual taxonomies:')
for key, value_dict in virtual_taxonomies.items():
    print(f'ID: {key}, Description: {value_dict["description"]}')

authority_names = taxonomies.call(101)

print('Authority names:')
print(authority_names)
