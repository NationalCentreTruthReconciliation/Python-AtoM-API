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
