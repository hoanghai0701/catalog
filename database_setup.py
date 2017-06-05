from app.models import Base
from sqlalchemy import create_engine

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
