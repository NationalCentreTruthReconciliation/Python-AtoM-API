# Python AtoM API

This is a simple library for interacting with an [AtoM](https://accesstomemory.org) archive within Python. This library works with Python version 3, and has been tested with AtoM version 2.5. All of the API interactions specified in the [AtoM documentation](https://www.accesstomemory.org/en/docs/2.5/dev-manual/api/api-intro/#api-intro) all have easy-to-call python functions associated with them in
this library. This includes:

- Browsing Taxonomies
- Browsing Information Objects
- Reading Information Objects

This library also implements a virtual endpoint that can be used to retrieve all of the authorities stored in the archive. It does this by treating the front-end application as an API endpoint. For this reason, this operation is more fragile than calling the API directly.

## Install

To install, download or clone this repository and run the included setup script.

```shell
python setup.py install
```

## Usage

Before you start calling any of the API endpoints, you first need a session set up. To do so, import the session factory and create a new session. New types of sessions are able to be added depending on what you AtoM/Server requires for credentials or cookies.

Once you have a session, you can use any of the four concrete taxonomy endpoint classes:

- `BrowseTaxonomyEndpoint`
- `VirtualBrowseTaxonomyEndpoint`
- `BrowseInformationObjectEndpoint`
- `ReadInformationObjectEndpoint`

```python
from atomapi.sessions import session_factory
from atomapi.endpoints import BrowseTaxonomyEndpoint, VirtualBrowseTaxonomyEndpoint \
    BrowseInfomrationObjectEndpoint, ReadInformtionObjectEndpoint

session = session_factory.create('default', url='https://youratom.com')

# Each endpoint requires a session and an API key (*)
browse_taxonomies = BrowseTaxonomyEndpoint(session, '1234567890')

# Set cache expiry to 10 minutes (default is 1 hour, 0 minutes)
read_info_objects = ReadInformationObjectEndpoint(
    session=session,
    api_key='1234567890',
    cache_hours=0,
    cache_minutes=10)

# Disable caching, set sf_culture to French
browse_info_objects = BrowseInformationObjectEndpoint(
    session=session,
    api_key='1234567890',
    cache_hours=0,
    cache_minutes=0,
    sf_culture='fr')

# (*) Virtual taxonomy endpoint does not require an API key
browse_virtual_taxonomies = VirtualBrowseTaxonomyEndpoint(session)

# Taxonomy endpoint requires a numeric taxonomy ID
place_access_points = taxonomy_endpoint.call(42)
genre_access_points = taxonomy_endpoint.call(78)

# Read information object endpoint requires a unique slug
obj_999 = read_info_objects.call('id-999')

# The syntax for browsing information objects is complex. Visit this link for details:
# https://www.accesstomemory.org/en/docs/2.5/dev-manual/api/browse-io/
# This call returns results with coffee OR chocolate in any field, with dates
# that match or overlap a range of January 1, 1990 - March 4, 2001, sorted by
# date:
browse_result = browse_info_objects.call(
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

# Get all authority names (see taxonomies.py for virtual endpoint IDs)
authorities = browse_virtual_taxonomies.call(100)
```
