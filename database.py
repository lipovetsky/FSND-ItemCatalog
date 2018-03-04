import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))

class Author(Base):
    __tablename__ = 'author'

    id = Column(Integer, primary_key = True)
    last_name = Column(String(250), nullable = False)
    bio = Column(String)
    photo = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
        'Name' : self.last_name,
        'Bio' : self.bio,
        'Photo' : self.photo,
        'ID' : self.id,
        }

class Book(Base):
    __tablename__ = 'book'

    id = Column(Integer, primary_key = True)
    name = Column(String(500))
    image = Column(String(250))
    amazon = Column(String(250))
    description = Column(String)
    author_id = Column(Integer, ForeignKey('author.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    author = relationship(Author)
    user = relationship(User)

    @property
    def serialize(self):
        return {
        'Name' : self.name,
        'Image' : self.image,
        'Amazon' : self.amazon,
        'Description' : self.description,
        'ID' : self.id,
        'Author' : self.author.last_name,
        }


engine = create_engine('sqlite:///greatbookswithusers.db')

Base.metadata.create_all(engine)
