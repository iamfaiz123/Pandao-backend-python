import uuid
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from starlette import status

from app.api.forms.admin_forms import UpdateCommunityFunctions
from models import dbsession as conn, Community, CommunityFunctions


def mark_community_as_feature(community_id: uuid.UUID, feature: bool) -> dict[str, UUID | bool] | None:
    """
    Marks a community as featured or unfeatured.

    Args:
        community_id: The UUID of the community.
        feature: True to mark as featured, False to unfeature.
        conn: SQLAlchemy database session.

    Raises:
        HTTPException: 404 if the community is not found.
        HTTPException: 500 for database errors.
    """
    try:
        community = conn.query(Community).filter(Community.id == community_id).first()

        if community is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

        community.is_featured = feature
        conn.add(community) # use add instead of save, in modern sqlalchemy.
        conn.commit()
        return {
            "community_id": community_id,
            "is_featured": feature,
        }

    except SQLAlchemyError as e:
        conn.rollback()  # Rollback on error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    except HTTPException as http_ex:
        conn.rollback()
        raise http_ex

    except Exception as general_ex: #catch all other unexpected exceptions.
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(general_ex)}")



def disable_community(community_id: uuid.UUID, disable: bool) -> dict[str, UUID | bool] | None:
    """
    Disables a community.

    Args:
        community_id: The UUID of the community.

    Raises:
        HTTPException: 404 if the community is not found.
        HTTPException: 500 for database errors.
        :param community_id:
        :param disable:
    """
    try:
        community = conn.query(Community).filter(Community.id == community_id).first()

        if community is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

        community.is_disabled_by_admin = disable
        conn.add(community)
        conn.commit()
        return {
            "community_id": community_id,
            "is_disabled": True,
        }

    except SQLAlchemyError as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    except HTTPException as http_ex:
        conn.rollback()
        raise http_ex

    except Exception as general_ex:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(general_ex)}")

def get_community_config(community_id: uuid.UUID):
    try:
        config = conn.query(CommunityFunctions).filter(CommunityFunctions.id == community_id).first()
        return config

    except SQLAlchemyError as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    except HTTPException as http_ex:
        conn.rollback()
        raise http_ex

    except Exception as general_ex:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An unexpected error occurred: {str(general_ex)}")

def update_community_config(req: UpdateCommunityFunctions):
    try:
        if req:
            community_functions = conn.query(CommunityFunctions).filter(
                CommunityFunctions.community_id == req.community_id).first()
            # Update the object's attributes
            for key, value in req.items():
                setattr(community_functions, key, value)
            # Commit the changes to the database
            conn.commit()
            return community_functions

    except SQLAlchemyError as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    except HTTPException as http_ex:
        conn.rollback()
        raise http_ex

    except Exception as general_ex:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An unexpected error occurred: {str(general_ex)}")

