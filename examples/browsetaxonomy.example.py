''' Feel free to play around with this script and use your own AtoM instance and
API Key.
'''
import atomapi
from atomapi.models.taxonomy import TaxonomyId

atom = atomapi.Atom('https://youratom.ca', api_key='1234567890')
places = atom.taxonomies.browse('places')

# Either of these will also work:
# places = atom.taxonomies.browse(TaxonomyId.PLACES)
# places = atom.taxonomies.browse(42)

print('Place taxonomies:')
for term in places:
    print(term['name'])
