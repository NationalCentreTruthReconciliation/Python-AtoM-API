import re

from urllib3.util.url import parse_url

def parse_url_from_string(url):
    parsed_url = None
    if not url:
        raise ValueError('Url cannot be empty.')
    parsed_url = parse_url(url)
    if not parsed_url.scheme:
        raise ValueError(f'Could not find a url scheme in {url}. Make sure url has http or https')
    if parsed_url.scheme != 'http' and parsed_url.scheme != 'https':
        raise ValueError(f'Could not find http: or https: in "{url}"')
    return parsed_url


STR_PARAM = re.compile(r'\{(?P<name>[^\}:]+)(?P<ftype>:[^\}]+)?\}')
def partial_format(string, **kwargs):
    ''' Executes a partial string format - only substitutes the parameters specified in the kwargs,
    and leaves the other string parameters as-is.
    '''
    kwarg_dict = dict(kwargs)
    existing_keys = list(kwarg_dict.keys())
    new_kwargs = {}
    for param in STR_PARAM.finditer(string):
        name = param.group('name')
        ftype = param.group('ftype')
        if ftype:
            msg = f'partial_format does not work with string format types - got "{name + ftype}"'
            raise ValueError(msg)
        if name not in existing_keys:
            new_kwargs[name] = '{'+name+'}'
    new_kwargs.update(kwarg_dict)
    return string.format(**new_kwargs)
