from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
Base = declarative_base()

engine = create_engine(
    'postgresql://pandao_test_user:mye0K26a11SmrIBrsxXaMPnm3yR2QVGS@dpg-ct2u6slsvqrc738gu7lg-a.oregon-postgres.render.com/pandao_test')



# engine = create_engine(
#     'postgresql://postgres:123@localhost/pandao')
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)
dbsession = Session()

# run predefine query

