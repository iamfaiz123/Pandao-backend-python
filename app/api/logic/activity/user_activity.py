import uuid

from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.api.forms.blueprint import DeployCommunity
# from app.api.forms.blueprint import DeployCommunity
from models import dbsession as conn, BluePrint, Community as Com, User, Participants, UserActivity, UserMetaData
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.exc import SQLAlchemyError

from pydantic import BaseModel
from typing import List


class UserActivityModel(BaseModel):
    transaction_id: str
    user_address: str
    name: str
    image_url: str


def get_community_activity(community_id: uuid,user_address=None):
    try:
        response = []
        result = ""
        if user_address is not None:
            results = (conn.query(
                UserActivity.transaction_id,
                UserActivity.user_address,
                User.name,
                UserMetaData.image_url,
                UserActivity.transaction_info,
                UserActivity.created_at
            ).join(
                User, UserActivity.user_address == User.public_address
            ).join(
                UserMetaData, User.public_address == UserMetaData.user_address
            ).filter(
                UserActivity.community_id == community_id
            ).filter(
                UserActivity.user_address == user_address
            ).order_by(
                UserActivity.created_at.desc()
            ).all())
        else:
            results = (conn.query(
                UserActivity.transaction_id,
                UserActivity.user_address,
                User.name,
                UserMetaData.image_url,
                UserActivity.transaction_info,
                UserActivity.created_at
            ).join(
                User, UserActivity.user_address == User.public_address
            ).join(
                UserMetaData, User.public_address == UserMetaData.user_address
            ).filter(
                UserActivity.community_id == community_id
            ).order_by(
                UserActivity.created_at.desc()
            ).all())




        for data in results:
            activity = {
                'tx_id': data[0],
                'user_address': data[1],
                'user_name': data[2],
                'user_image_url': data[3],
                'info': data[4],
                'created_at': data[5]
            }
            response.append(activity)
        return response

    except SQLAlchemyError as e:
        # Log the error e
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_user_activity(user_address: str, page: int, limit: int,community_id=None):
    try:
        response = []
        offset = (page - 1) * limit
        total_rows = conn.query(func.count(UserActivity.transaction_id)).filter(
            UserActivity.user_address == user_address).scalar()

        if community_id is not None:
            results = (conn.query(
                UserActivity.transaction_id,
                UserActivity.user_address,
                User.name,
                UserMetaData.image_url,
                UserActivity.transaction_info,
                UserActivity.created_at
            ).join(
                User, UserActivity.user_address == User.public_address
            ).join(
                UserMetaData, User.public_address == UserMetaData.user_address
            ).filter(
                UserActivity.user_address == user_address
            ).filter(
                UserActivity.community_id == community_id
            ).order_by(
                UserActivity.created_at.desc()
            ).limit(limit).offset(offset).all())
        else:
            results = (conn.query(
                UserActivity.transaction_id,
                UserActivity.user_address,
                User.name,
                UserMetaData.image_url,
                UserActivity.transaction_info,
                UserActivity.created_at
            ).join(
                User, UserActivity.user_address == User.public_address
            ).join(
                UserMetaData, User.public_address == UserMetaData.user_address
            ).filter(
                UserActivity.user_address == user_address
            ).order_by(
                UserActivity.created_at.desc()
            ).limit(limit).offset(offset).all())



        for data in results:
            activity = {
                'tx_id': data[0],
                'user_address': data[1],
                'user_name': data[2],
                'user_image_url': data[3],
                'info': data[4],
                'created_at': data[5]
            }
            response.append(activity)

        response = {
            "total_rows": total_rows,
            "page": page,
            "page_size": limit,
            "data": response
        }
        return response

    except SQLAlchemyError as e:
        # Log the error e
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
