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

To use the API, you will require an [AtoM API key](https://www.accesstomemory.org/fr/docs/2.5/dev-manual/api/api-intro/#generating-an-api-key-for-a-user). To get data from the API, create an instance of the `Atom` class:

```python
import atomapi

atom = atomapi.Atom('https://youratom.com', api_key='1234567890')
```

Fetch taxonomies, and view information objects like so:

```python
subjects = atom.taxonomies.browse('subjects')
info_obj = atom.taxonomies.read('some-reference-code')
results = atom.taxonomies.browse(sq={'sq0': 'School'}, so={}, sf={'sf0': 'title'}, filters={})
```

For more examples, check out the `examples` folder.
