from sqlalchemy.exc import IntegrityError
from models import dbsession as conn, Tag
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


def get_all_tags_query():
    try:
        result = conn.query(Tag).all()
        return result
    except IntegrityError as e:
        conn.rollback()
        print(f"Integrity error occurred: {e}")
        raise HTTPException(status_code=400,
                            detail="Integrity error: possibly duplicate entry or foreign key constraint.")

    except SQLAlchemyError as e:
        conn.rollback()
        print(f"SQLAlchemy error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        conn.rollback()
        print(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
