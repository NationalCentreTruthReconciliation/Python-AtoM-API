''' Feel free to play around with this script and use your own AtoM instance and
API Key.

The syntax for browsing information objects is complex. Visit this link for details:
https://www.accesstomemory.org/en/docs/2.5/dev-manual/api/browse-io/
'''
from atomapi.sessions import session_factory
from atomapi.endpoints import BrowseInformationObjectEndpoint

# Using an F5 session, not a default one.
session = session_factory.create(
    name='f5',
    url='https://youratom.com',
    cache_credentials=True) # kwargs are session-type dependent

# Set cache expiry time to 2h 30m
browse_info_objects = BrowseInformationObjectEndpoint(
    session=session,
    api_key='1234567890',
    cache_hours=2,
    cache_minutes=30)

# This call returns results with coffee OR chocolate in any field, with dates
# that match or overlap a range of January 1, 1990 - March 4, 2001, sorted by
# date:
browse_result = browse_info_objects.get(
    sq={
        'sq0': 'coffee',
        'sq1': 'chocolate'
    },
    sf={}, # Empty since "any field"
    so={
        'so1': 'or'
    },
    filters={
        'startDate': '1990-01-01',
        'endDate': '2001-03-04',
        'rangeType': 'inclusive',
        'sort': 'date'
    })

print('Browse Result:')
print(browse_result)
