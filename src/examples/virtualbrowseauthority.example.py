''' Feel free to play around with this script and use your own AtoM instance and
API Key.

Virtual taxonomies fetch data from the front end, treating it as an API. As
such, this type of call can put stress on the server, so caching is mandatory.
If you disable the cache, you will get an exception.
'''
from atomapi.sessions import session_factory
from atomapi.virtualendpoints import VirtualBrowseAuthorityEndpoint, \
    VirtualBrowseAuthorityRefCodeEndpoint

session = session_factory.create('default', 'https://youratom.ca')

# You don't need an API key to access the front end
authorities = VirtualBrowseAuthorityEndpoint(session, cache_hours=2, cache_minutes=0)

# Authorities don't require any parameters to retrieve
names = authorities.get()

print('Authority names:')
print(names)


# To get the authority names with their associated reference codes:

# authorities_ref_codes = VirtualBrowseAuthorityRefCodeEndpoint(session)
# names_with_codes = authorities_ref_codes.get()
# print('Authority names with ref codes:')
# print(names_with_codes)
