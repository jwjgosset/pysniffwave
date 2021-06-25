'''
Database handle
===============

..  codeauthor:: Charles Blais
'''
import os

from sqlalchemy import create_engine
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(
    os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///:memory:'),
    connect_args={'check_same_thread': False},
    poolclass=SingletonThreadPool)
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
