from pathlib import Path
import datetime
import re
import sys
import tempfile

import pytest

sys.path.append(str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position,no-name-in-module
from cache import Cache


class TestCache:
    def setup_method(self):
        TestCache.written_location = {}
        TestCache.written_obj = {}

    @pytest.fixture(autouse=True)
    def mock_write_to_disk(self, monkeypatch):
        def mock(self, location, obj):
            TestCache.written_location = location
            TestCache.written_obj = obj
        monkeypatch.setattr(Cache, '_write_object_to_disk', mock)

    @pytest.fixture(autouse=True)
    def mock_read_from_disk(self, monkeypatch):
        def mock(self, location):
            if location == 'mock_location/does_not_exist':
                raise FileNotFoundError(location)
            elif location == 'mock_location/expired':
                return {
                    # Two hours prior to the present
                    Cache.EXPIRES_FIELD: str(datetime.datetime(2020, 1, 1, 10, 0, 0, 0)),
                    Cache.OBJECT_FIELD: 'expired_object'
                }
            elif location == 'mock_location/not_expired':
                return {
                    # One month after the present
                    Cache.EXPIRES_FIELD: str(datetime.datetime(2020, 2, 1, 12, 0, 0, 0)),
                    Cache.OBJECT_FIELD: 'not_expired_object'
                }
            else:
                raise FileNotFoundError(location)
        monkeypatch.setattr(Cache, '_read_object_from_disk', mock)

    @pytest.fixture
    def mock_get_location(self, monkeypatch):
        def mock(self, name):
            return f'mock_location/{name}'
        monkeypatch.setattr(Cache, 'get_storage_location', mock)

    @pytest.fixture(autouse=True)
    def mock_tempfile_gettempdir(self, monkeypatch):
        def mock():
            return 'temporary'
        monkeypatch.setattr(tempfile, 'gettempdir', mock)

    @pytest.fixture(autouse=True)
    def mock_datetime_now(self, monkeypatch):
        class MockDateTime(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.datetime(2020, 1, 1, 12, 0, 0, 0)
        monkeypatch.setattr(datetime, 'datetime', MockDateTime)

    def test_storage_location_no_prefix(self):
        test_cache = Cache()
        storage_loc = test_cache.get_storage_location('1000')
        assert re.match(r'^temporary(?:/|\\)pycache_1000\.json$', str(storage_loc)) is not None

    def test_storage_location_prefix(self):
        test_cache = Cache(prefix='prefix')
        storage_loc = test_cache.get_storage_location('ABCD')
        assert re.match(r'^temporary(?:/|\\)prefix_pycache_ABCD\.json$', str(storage_loc)) is not None

    @pytest.mark.parametrize('hours,minutes', [(0, 0), (1, 0), (12, 0), (0, 1), (0, 30), (2, 60)])
    def test_set_valid_hours_minutes(self, hours, minutes):
        test_cache = Cache(expire_hours=0, expire_minutes=0)
        test_cache.set_expire_hours(hours)
        test_cache.set_expire_minutes(minutes)
        assert test_cache.minutes == minutes
        assert test_cache.hours == hours

    @pytest.mark.parametrize('minutes', [-0.0001, -1, -200])
    def test_set_invalid_minutes(self, minutes):
        with pytest.raises(ValueError):
            test_cache = Cache()
            test_cache.set_expire_minutes(-1)

    @pytest.mark.parametrize('hours', [-1, -1.2, -1000])
    def test_set_invalid_hours(self, hours):
        with pytest.raises(ValueError):
            test_cache = Cache()
            test_cache.set_expire_hours(hours)


    @pytest.mark.parametrize('hours,minutes', [(0, 0), (1, 0), (11, 0), (0, 1), (0, 30), (2, 59)])
    def test_store(self, mock_get_location, hours, minutes):
        test_cache = Cache(expire_hours=hours, expire_minutes=minutes)
        test_cache.store('sample_name', 'stored_object')
        expiry_time = datetime.datetime.strptime(TestCache.written_obj[Cache.EXPIRES_FIELD], Cache.DATE_FORMAT)
        assert expiry_time == datetime.datetime(2020, 1, 1, (12 + hours), (0 + minutes), 0, 0)
        assert TestCache.written_obj[Cache.OBJECT_FIELD] == 'stored_object'

    def test_retrieve_does_not_exist(self, mock_get_location):
        test_cache = Cache()
        obj = test_cache.retrieve('does_not_exist')
        assert obj is None

    def test_retrieve_expired(self, mock_get_location):
        test_cache = Cache()
        obj = test_cache.retrieve('expired')
        assert obj is None

    def test_retrieve_not_expired(self, mock_get_location):
        test_cache = Cache()
        obj = test_cache.retrieve('not_expired')
        assert obj is not None
        assert obj == 'not_expired_object'
