from . import Base
from catalog import Catalog
from user import User
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False)
    description = Column(Text, nullable=False)
    catalog_id = Column(Integer, ForeignKey('catalog.id'), nullable=False)
    catalog = relationship(Catalog, backref='items')
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User, backref='items')

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'catalog_id': self.catalog_id
        }

