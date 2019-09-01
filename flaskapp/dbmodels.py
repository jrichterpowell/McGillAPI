from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine

Base = declarative_base()
#define a class for the course data (rows of the courses table)
#TODO:Figure out how to make multiple tables with this one class
class Course(Base):
    __tablename__ = 'courselist'
    code = Column(String, primary_key=True)
    terms = Column(String)
    profs = Column(String)
    prereqs = Column(String)
    credits = Column(Integer)
    desc = Column(String)
    extend_existing=True
    def __repr__(self):
        return f'Course {self.code}'