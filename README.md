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

There are four concrete API endpoint classes that you can use:

- `BrowseTaxonomyEndpoint`
- `VirtualBrowseTaxonomyEndpoint`
- `BrowseInformationObjectEndpoint`
- `ReadInformationObjectEndpoint`

To view examples for each, go to the [examples folder](/src/examples/).
