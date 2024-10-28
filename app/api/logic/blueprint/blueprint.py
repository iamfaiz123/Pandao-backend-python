import uuid
import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.api.forms import *
from app.api.utils import ApiError
from models import dbsession as conn, BluePrint, BluePrintTerms
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_blueprint(req: BlurPrintForm):
    try:
        # Create a new BluePrint instance using the validated data
        new_blueprint = BluePrint(
            slug=req.slug,
            description=req.description,
            price=req.price,
            package_addr=req.package_address
        )

        # Add terms if provided
        if req.terms:
            for term in req.terms:
                new_term = BluePrintTerms(
                    blueprint_slug=req.slug,
                    term=term.term,
                    description=term.description
                )
                new_blueprint.terms.append(new_term)

        # Add the new blueprint to the conn and commit
        conn.add(new_blueprint)
        conn.commit()
        logger.info(f"Successfully added new blueprint: {new_blueprint.slug}")
        return new_blueprint

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


# function to get all blueprints
def get_all_blueprints():
    try:
        result = conn.query(BluePrint).all()
        return result
    except SQLAlchemyError as e:
        conn.rollback()
        logger.error(f"SQLAlchemy error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_blueprint(slug: str):
    try:
        result = conn.query(BluePrint).options(joinedload(BluePrint.terms)).filter(BluePrint.slug == slug).first()
        return result
    except SQLAlchemyError as e:
        conn.rollback()
        logger.error(f"SQLAlchemy error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
