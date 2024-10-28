from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
Base = declarative_base()

engine = create_engine(
    'postgresql://panda_live_user:Ebf671IFTQKo0cuZEl4zCW7t1CLizLoN@dpg-csfq3rpu0jms73fke3a0-a.oregon-postgres.render.com/panda_live')



# engine = create_engine(
#     'postgresql://postgres:123@localhost/pandao')
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)
dbsession = Session()

# run predefine query

