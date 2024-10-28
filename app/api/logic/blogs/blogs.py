import uuid
import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.api.forms import *
from app.api.forms.blogs import BlogCreate
from app.api.utils import ApiError
from models import dbsession as conn, BluePrint, BluePrintTerms, Blog
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_blogs(req: BlogCreate):
    try:
        db_blog = Blog(
            id=str(uuid.uuid4()),  # Generate a unique ID for the blog post
            title=req.title,
            description=req.description,
            thumbnail_image=req.thumbnail_image,
            published_by=req.published_by,
            url=req.url
        )
        conn.add(db_blog)
        conn.commit()
        return db_blog
    except IntegrityError as e:
        conn.rollback()
        logger.error(f"Integrity error occurred: {e}")
        raise HTTPException(status_code=400,
                            detail="Integrity error: possibly duplicate entry or foreign key constraint.")

    except SQLAlchemyError as e:
        conn.rollback()
        logger.error(f"SQLAlchemy error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        conn.rollback()
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def get_blogs():
    blogs = conn.query(Blog).all()
    return blogs