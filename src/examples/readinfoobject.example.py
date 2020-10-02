''' Feel free to play around with this script and use your own AtoM instance and
API Key.
'''

from atomapi.sessions import session_factory
from atomapi.endpoints import ReadInformationObjectEndpoint

session = session_factory.create('default', 'https://youratom.ca')

# Disable caching for endpoint, use English culture
read_info_objects = ReadInformationObjectEndpoint(
    session=session,
    api_key='1234567890',
    cache_hours=0,
    cache_minutes=0,
    sf_culture='en')

# The ID you use here will be dependent on your AtoM instance
some_object = read_info_objects.get('this-is-a-unique-slug-000')

print('Information Object:')
print(some_object)
