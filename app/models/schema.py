from sqlalchemy import Column, Integer, Table, ForeignKey
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declarative_base

from . import DB
Base = declarative_base()

class Server(DB.Model):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True)
    name = Column(mysql.types.VARCHAR(128))


class File(DB.Model):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    path = Column(mysql.types.VARCHAR(512))
    repo_id = Column(Integer, ForeignKey('repos.id', ondelete='CASCADE'))


class Test(DB.Model):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True)
    name = Column(mysql.types.VARCHAR(256))
    type = Column(mysql.types.VARCHAR(256))
    repo_id = Column(Integer, ForeignKey('repos.id', ondelete='CASCADE'))


class TestCount(DB.Model):
    __tablename__ = "test_count"
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), primary_key=True)
    test_id = Column(Integer, ForeignKey('tests.id', ondelete='CASCADE'), primary_key=True)
    count = Column(Integer)


class HandledPull(DB.Model):
    __tablename__ = "handled_pulls"
    pull_id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey('repos.id', ondelete='CASCADE'))


class Repo(DB.Model):
    __tablename__ = "repos"
    id = Column(Integer, primary_key=True)
    name = Column(mysql.types.VARCHAR(256))