from .sessionfactory import SessionFactory
from .defaultsession import DefaultSession
from .f5session import F5Session

# Register session types here
session_factory = SessionFactory()
session_factory.register_session_type('default', DefaultSession)
session_factory.register_session_type('f5', F5Session)
