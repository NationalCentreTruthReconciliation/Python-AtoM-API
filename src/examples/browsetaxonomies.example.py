''' Feel free to play around with this script and use your own AtoM instance and
API Key.
'''

from atomapi.sessions import session_factory
from atomapi.endpoints import BrowseTaxonomyEndpoint
from atomapi.taxonomies import DefaultTaxonomyIds

session = session_factory.create('default', 'https://youratom.ca')

taxonomies = BrowseTaxonomyEndpoint(session, api_key='1234567890')

# The default taxonomy IDs can be found in atomapi.taxonomies. You can use those
# or the raw IDs, whatever you like.
place_access_points = taxonomies.call(DefaultTaxonomyIds.PLACES.value)
level_of_descriptions = taxonomies.call(34)

print('Level of Descriptions:')
print(level_of_descriptions)
print()
print('Place Access Points:')
print(place_access_points)
