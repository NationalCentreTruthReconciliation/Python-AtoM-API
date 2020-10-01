from pathlib import Path
import datetime
import os
import json
import tempfile
import hashlib
import pickle


class Cache:
    ''' Simple caching class that stores cached files in the temporary directory. '''
    EXPIRES_FIELD = 'expires'
    OBJECT_FIELD = 'object'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, expire_hours=1, expire_minutes=0, prefix=None):
        if expire_hours < 0:
            raise ValueError('Hours for cached files to expire can''t be negative.')
        if expire_minutes < 0:
            raise ValueError('Minutes for cached files to expire can''t be negative')
        self.hours = expire_hours
        self.minutes = expire_minutes
        self.prefix = prefix
        self.hit = False

    def set_expire_hours(self, hours):
        if hours < 0:
            raise ValueError('Hours for cached files to expire can''t be negative.')
        self.hours = hours

    def set_expire_minutes(self, minutes):
        if minutes < 0:
            raise ValueError('Minutes for cached files to expire can''t be negative')
        self.minutes = minutes

    def get_storage_location(self, name):
        file_name = f'{self.prefix}_pycache_{name}.json' if self.prefix else f'pyache_{name}.json'
        return Path(tempfile.gettempdir()) / file_name

    def store(self, name, obj):
        """
        Stores an object, set to expire after a number of hours and minutes. The time can be set in
        the constructor or with the setters.
        """
        expire_time = (datetime.datetime.now() + \
            datetime.timedelta(hours=self.hours, minutes=self.minutes)).strftime(self.DATE_FORMAT)

        structure = {
            self.EXPIRES_FIELD: expire_time,
            self.OBJECT_FIELD: obj
        }

        location = self.get_storage_location(name)
        self._write_object_to_disk(location, structure)

    def retrieve(self, name):
        """
        In case of cache miss, returns None.
        In case of cache hit, returns cached object.
        """
        location = None
        try:
            location = self.get_storage_location(name)
            obj = self._read_object_from_disk(location)
            expire_datetime = datetime.datetime.strptime(obj[self.EXPIRES_FIELD], self.DATE_FORMAT)
            if expire_datetime < datetime.datetime.now():
                self.hit = False
                return None
            self.hit = True
            return obj[self.OBJECT_FIELD]
        except FileNotFoundError:
            self.hit = False
            return None
        except json.decoder.JSONDecodeError:
            if location is not None and location.exists():
                os.remove(location)
            self.hit = False
            return None

    def _write_object_to_disk(self, location, obj):
        with open(location, 'w') as file_handle:
            json.dump(obj, file_handle, indent=2)

    def _read_object_from_disk(self, location):
        with open(location, 'r') as file_handle:
            return json.load(file_handle)


class ObfuscatedCache(Cache):
    ''' Hash file name and obfuscate file contents. Not secure, but better than nothing. '''

    def get_storage_location(self, name: str):
        file_name = f'{self.prefix}_{name}' if self.prefix else name
        md5 = hashlib.md5()
        md5.update(file_name.encode('utf-8'))
        return Path(tempfile.gettempdir()) / f'{md5.hexdigest()}.tmp'

    def _write_object_to_disk(self, location, obj):
        ''' Write object as a binary pickle '''
        with open(location, 'wb') as file_handle:
            pickle.dump(obj, file_handle, protocol=2)

    def _read_object_from_disk(self, location):
        with open(location, 'rb') as file_handle:
            return pickle.load(file_handle)
