from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position,no-name-in-module,import-error
from sessions import session_factory
from . import ExampleSession

class TestSession:
    def test_instance_variables_set(self):
        new_session = ExampleSession('https://example.com')
        assert new_session.host == 'example.com'
        assert new_session.url == 'https://example.com'
        assert not new_session.session_is_authorized

    def test_duplicate_sessions_not_created(self):
        new_session = ExampleSession('https://example.com')
        authorized_sess_1 = new_session.authorized_session
        authorized_sess_2 = new_session.authorized_session
        authorized_sess_3 = new_session.authorized_session
        assert authorized_sess_1 == new_session.last_session_created
        assert authorized_sess_2 == new_session.last_session_created
        assert authorized_sess_3 == new_session.last_session_created

class TestSessionFactory:
    def teardown_method(self, method):
        session_factory.de_register_session_type('example')

    def test_register_session_type(self):
        session_factory.register_session_type('example', ExampleSession)
        assert 'example' in session_factory.session_types

    def test_example_session_created(self):
        session_factory.register_session_type('example', ExampleSession)
        new_session = session_factory.create('example', 'https://example.com')
        assert new_session is not None
        assert new_session.host == 'example.com'
        assert new_session.url == 'https://example.com'

    def test_kwargs_passed_to_session(self):
        session_factory.register_session_type('example', ExampleSession)
        user = object()
        new_session = session_factory.create('example', 'https://example.org/test', user=user)
        assert new_session is not None
        assert new_session.host == 'example.org'
        assert new_session.url == 'https://example.org/test'
        assert new_session.user == user
