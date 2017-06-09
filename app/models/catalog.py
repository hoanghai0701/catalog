from . import Base
from user import User
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Catalog(Base):
    __tablename__ = 'catalog'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User, backref='catalogs')

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id
            # 'items': [item.serialize for item in self.items]
        }
