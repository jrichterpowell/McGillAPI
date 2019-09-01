#Modified boilerplate from sqlalchemy documentation

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///test.db', convert_unicode=True)
DBSession = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
#Base.query = db_session.query_property()

def initDB():
    from models import course
    Base.metadata.create_all(bind=engine)