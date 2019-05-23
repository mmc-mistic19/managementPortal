from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

engine = create_engine('sqlite:///identityManagement.db', echo=True)
Base = declarative_base()

########################################################################
class User(Base):
    """"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    salt = Column(String)

#----------------------------------------------------------------------
def __init__(self, username, password):
    """"""
    self.username = username
    self.password = password

########################################################################
class Company(Base):
    """"""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    companyName = Column(String)
    termsLimit = Column(Integer)

########################################################################
class UsersCompany(Base):
    """"""
    __tablename__ = "usersCompany"

    id = Column(Integer, primary_key=True)
    userID = Column(Integer, ForeignKey('users.id'))
    companyID = Column(Integer, ForeignKey('companies.id'))

# create tables
Base.metadata.create_all(engine)
