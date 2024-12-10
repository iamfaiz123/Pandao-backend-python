from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
Base = declarative_base()

engine = create_engine(
    'postgresql://pandao_cy1u_user:m5DrP4ymkKMKTxOtns0POf658qoNOILH@dpg-ctc5jjdumphs73b17sjg-a.oregon-postgres.render.com/pandao_cy1u')




# engine = create_engine(
#     'postgresql://postgres:123@localhost/pandao')
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)
dbsession = Session()

# run predefine query

