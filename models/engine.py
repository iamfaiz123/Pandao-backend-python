from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
Base = declarative_base()
#
engine = create_engine(
    'postgresql://pandao_backend_i1ff_user:tFTAwV9CUv1s0yfTQ57QYFFHBFGJkMDC@dpg-cto07c5ds78s73c8j1ig-a.oregon-postgres.render.com/pandao_backend_i1ff')




# engine = create_engine(
#     'postgresql://postgres:123@localhost/nintendo')
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)
dbsession = Session()

# run predefine query

