''' Feel free to play around with this script and use your own AtoM instance and
API Key.

The syntax for browsing information objects is complex. Visit this link for details:
https://www.accesstomemory.org/en/docs/2.5/dev-manual/api/browse-io/
'''
import atomapi

atom = atomapi.Atom('https://youratom.ca', api_key='1234567890')

# This call returns results with coffee OR chocolate in any field, with dates
# that match or overlap a range of January 1, 1990 - March 4, 2001, sorted by
# date:
browsed = atom.informationobjects.browse(
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
    }
)

print(len(browsed['results']), 'results found:')
for i, result in enumerate(browsed['results'], 1):
    print(f'{i}. {result}')
