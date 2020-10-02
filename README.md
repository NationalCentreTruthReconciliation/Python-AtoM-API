# Python AtoM API

This is a simple library for interacting with an [AtoM](https://accesstomemory.org) archive within Python. This library works with Python version 3, and has been tested with AtoM version 2.5. All of the API interactions specified in the [AtoM documentation](https://www.accesstomemory.org/en/docs/2.5/dev-manual/api/api-intro/#api-intro) all have easy-to-call python functions associated with them in
this library. This includes:

- Browsing Taxonomies
- Browsing Information Objects
- Reading Information Objects

This library also implements a virtual endpoint that can be used to retrieve all of the authorities stored in the archive. It does this by treating the front-end application as an API endpoint. For this reason, this operation is more fragile than calling the API directly and is not guaranteed to work with every version of AtoM and every theme.

## Install

```shell
python -m pip install atomapi
```

## Usage

To use the API, you will require an [AtoM API key](https://www.accesstomemory.org/fr/docs/2.5/dev-manual/api/api-intro/#generating-an-api-key-for-a-user). To use the virtual API, you do not need an API key, but please use it responsibly since the virtual API can easily make over 100 requests depending on how many items you have in AtoM. This may or may not put undue stress on the server.

There are three concrete API endpoint classes that use the actual API:

- `endpoints.BrowseTaxonomyEndpoint`
- `endpoints.BrowseInformationObjectEndpoint`
- `endpoints.ReadInformationObjectEndpoint`

There are also three concrete Virtual API endpoint classes that make use of the front end application and treat is as an API:

- `virtualendpoints.VirtualBrowseTaxonomyEndpoint`
- `virtualendpoints.VirtualBrowseAuthorityEndpoint`
- `virtualendpoints.VirtualBrowseAuthorityRefCodeEndpoint`

Note that the virtual endpoints have been tested on AtoM version 2.5, with the default arDominionPlugin theme. The virtual endpoints are not guaranteed to work with other versions of AtoM or highly customized themes. That being said, it would be easy to create a new endpoint that takes into account the modifed markup or CSS in a custom theme.

To view examples on how to use each endpoint, go to the [examples code documentation](https://github.com/danloveg/atom-api-python/tree/master/src/examples).

## Simple Example

To get data from the API, you will need to create a session object from the session factory. There are two types of sessions, `default`, and `f5`, for most AtoM instances, a `default` session will be sufficient.

```python
from atomapi.sessions import session_factory

my_session = session_factory.create(name='default', url='https://youratom.com')
```

Once you've created a session, you can use it with any of the real and virtual endpoints. You may also reuse this session variable with as many endpoints as you like.

```python
from atomapi.sessions import session_factory
from atomapi.endpoints import BrowseTaxonomyEndpoint
from atomapi.virtualendpoints import VirtualBrowseTaxonomyEndpoint

my_session = session_factory.create('default', 'https://youratom.com')

real_taxonomy_endpoint = BrowseTaxonomyEndpoint(my_session, api_key='1234567890')
virtual_taxonomy_endpoint = VirtualBrowseTaxonomyEndpoint(my_session)
```

Once your endpoints are set up, you can call the `get` function on them to get data.

```python
from atomapi.taxonomies import DefaultTaxonomyIds

subjects = real_taxonomy_endpoint.get(DefaultTaxonomyIds.SUBJECTS.value)
places = virtual_taxonomy_endpoint.get(DefaultTaxonomyIds.PLACES.value)
```

The virtual API will take a lot longer to fetch the same amount of data as the real API since it is scraping the web page.

For more examples, go to the [examples code documentation](https://github.com/danloveg/atom-api-python/tree/master/src/examples).
