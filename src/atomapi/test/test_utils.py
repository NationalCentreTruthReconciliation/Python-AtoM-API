from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position,no-name-in-module,import-error
from utils import parse_url_from_string


class TestParseUrl:
    def test_raises_if_empty(self):
        with pytest.raises(ValueError):
            parse_url_from_string('')

    @pytest.mark.parametrize('url', [
        'GARBAGE',
        'google',
        'artefactual website'
    ])
    def test_raises_if_not_url(self, url):
        with pytest.raises(ValueError):
            parse_url_from_string(url)

    @pytest.mark.parametrize('url', [
        'google.com',
        'artefactual.com/',
        'example.ca',
    ])
    def test_raises_if_no_scheme(self, url):
        with pytest.raises(ValueError):
            parse_url_from_string(url)

    @pytest.mark.parametrize('url', [
        'ftp://google.com',
        'file://C:/Users/you/file.txt',
        'dns://127.0.0.1:8000/local',
    ])
    def test_raises_if_wrong_scheme(self, url):
        with pytest.raises(ValueError):
            parse_url_from_string(url)

    @pytest.mark.parametrize('url,scheme,host,full', [
        ('https://google.com', 'https', 'google.com', 'https://google.com'),
        ('http://youtube.com', 'http', 'youtube.com', 'http://youtube.com'),
        ('http://127.0.0.1:8000', 'http', '127.0.0.1', 'http://127.0.0.1:8000'),
        ('https://artefactual.com/software/', 'https', 'artefactual.com',
         'https://artefactual.com/software/'),
    ])
    def test_parses_host_url_scheme(self, url, scheme, host, full):
        parsed_url = parse_url_from_string(url)
        assert parsed_url.scheme == scheme
        assert parsed_url.host == host
        assert str(parsed_url) == full
