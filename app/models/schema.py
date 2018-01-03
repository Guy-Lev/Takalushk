from sqlalchemy import Column, Integer
from sqlalchemy.dialects import mysql

from . import DB


class Server(DB.Model):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True)
    name = Column(mysql.types.VARCHAR(128))


class Users(DB.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(mysql.types.VARCHAR(128))
    ip = Column(mysql.types.VARCHAR(18))


class Files(DB.Model):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    path = Column(mysql.types.VARCHAR(256))


class FileTestCount(DB.Model):
    __tablename__ = "file_test_count"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, DB.ForeignKey("files.id"))
    test_name = Column(mysql.types.VARCHAR(256))
    count = Column(Integer)