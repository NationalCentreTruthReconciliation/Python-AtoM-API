''' Feel free to play around with this script and use your own AtoM instance and
API Key.
'''
import atomapi
from atomapi.authorizer import F5Authorizer

# Use the F5 authorizer. You will need to log in the first time data is fetched
atom = atomapi.Atom('https://youratom.ca', api_key='1234567890')
f5 = F5Authorizer(atom.url, cache_credentials=True)
atom.set_authorizer(f5)

# Read object in French
info_obj = atom.informationobjects.read('some-reference-code-000', sf_culture='fr')

print('Information Object:')
print(info_obj)
