from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
Base = declarative_base()
#
engine = create_engine(
    'postgresql://pandaoabackend_user:zhBguMlEKa0aWblbk3gB9zOiaJjugeCe@dpg-cubpq7l6l47c73a3n91g-a.oregon-postgres.render.com/pandaoabackend')




# engine = create_engine(
#     'postgresql://postgres:123@localhost/nintendo')
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)
dbsession = Session()

# run predefine query