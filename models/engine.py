from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config.config import config

Base = declarative_base()
engine = create_engine(config.get('DATABASE_URL'))
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
dbsession = Session()
