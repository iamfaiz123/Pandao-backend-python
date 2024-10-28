from http.client import HTTPException

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload

from models import dbsession as conn, User, UserMetaData, UserPreference, UserWork
from ....forms import UserLogin, UserSignupForm, UserProfileUpdate, UserWorkHistoryUpdate
from ....utils import ApiError
import logging

logging.basicConfig(level=logging.ERROR)


def user_sign_up(signup: UserSignupForm):
    try:
        # insert user details first
        user = User(
            name=signup.username,
            public_address=signup.public_address,
        )
        # create user meta data
        usermetadata = UserMetaData(
            user_address=signup.public_address,
            bio=signup.bio,
            image_url=signup.display_image,
        )
        user.usermetadata = usermetadata
        conn.add(user)

        # try to iter through tags that user send

        # tags will always present
        for t in signup.tags:
            preference = UserPreference(
                user_address=signup.public_address,
                tag=t
            )
            conn.add(preference)
        if signup.work_history is not None:
            for w_h in signup.work_history:
                u_wh = UserWork(
                    company=w_h.company_name,
                    designation=w_h.designation,
                    description=w_h.description,
                    from_date=w_h.start_date,
                    to_date=w_h.end_date,
                    user_address=signup.public_address,
                )
                conn.add(u_wh)
        conn.commit()
        return {
            "status": 201,
            "message": "user created "
        }
    except IntegrityError as e:
        conn.rollback()
        return {
            "status": 401,
            "cause": "user with same wallet address already exists"
        }
    except Exception as e:
        conn.rollback()
        logging.error("error at user signup : {}", e)
        raise HTTPException()


def user_login_req(req: UserLogin):
    # extract data from form
    wallet_addr = req.public_address
    name = req.name
    user = User(name=name, public_address=wallet_addr)
    conn.add(user)
    try:
        conn.commit()
        response = conn.query(User).all()
        return response
    except IntegrityError:
        conn.rollback()
        return {}
    except Exception as e:
        conn.rollback()
        logging.error(e)
        return ApiError("Something went wrong, we're working on it", 500).as_http_response()


def get_user_detail(public_address: str):
    try:
        user = conn.query(User).options(joinedload(User.usermetadata)).filter(
            User.public_address == public_address).first()

        if user:
            # get user work history
            user_wh = conn.query(UserWork).filter(UserWork.user_address == user.public_address).all()
            # If user exists, convert to dictionary
            user_dict = {
                "name": user.name,
                "public_address": user.public_address,
                "last_login": str(user.last_login),
                "usermetadata": {
                    "about": user.usermetadata.about,
                    "image_url": user.usermetadata.image_url,
                    "cover_url": user.usermetadata.cover_url,
                    "x_url": user.usermetadata.x_url,
                    "linkedin": user.usermetadata.linkedin,
                    "website": user.usermetadata.website,
                    "bio": user.usermetadata.bio
                },
                "user_work": user_wh
            }

            return user_dict
        else:
            return {}



    except Exception as e:
        conn.rollback()
        logging.error(e)
        return ApiError("Something went wrong, we're working on it", 500).as_http_response()


def check_user_exist(public_address: str):
    try:
        user_status = conn.query(User).filter(User.public_address == public_address).first()
        if user_status is not None:
            return {
                "user_address": public_address,
                "exist": True
            }
        else:
            return {
                "user_address": public_address,
                "exist": False
            }
    except Exception as e:
        logging.error("Error getting user signup status: %s", e)
        raise HTTPException()


def update_user_profile(req: UserProfileUpdate):
    try:
        user_meta_data = conn.query(UserMetaData).filter(UserMetaData.user_address == req.public_address).first()
        if user_meta_data is None:
            return {
                "status": 404,
                "cause": "user with these credentials does not exist"
            }

        if req.about is not None:
            user_meta_data.about = req.about
        if req.image_url is not None:
            user_meta_data.image_url = req.image_url
        if req.tiktok is not None:
            user_meta_data.tiktok = req.tiktok
        if req.x_url is not None:
            user_meta_data.x_url = req.x_url
        if req.website_url is not None:
            user_meta_data.website_url = req.website_url
        if req.linkedin is not None:
            user_meta_data.linkedin = req.linkedin
        if req.cover_url is not None:
            user_meta_data.cover_url = req.cover_url
        if req.bio is not None:
            user_meta_data.bio = req.bio
        if req.website_url is not None:
            user_meta_data.website = req.website_url
        wh_ids = []
        if req.work_history is not None:
            for wh in req.work_history:
                if wh.id is not None:
                    wh_ids.append(wh.id)
            conn.query(UserWork).filter(
                UserWork.user_address == req.public_address,
                UserWork.id.notin_(wh_ids)
            ).delete(synchronize_session=False)
            for wh in req.work_history:
                if wh.id is None:
                    new_wh = UserWork(
                        user_address=req.public_address,
                        company=wh.company,
                        from_date=wh.from_date,
                        to_date=wh.to_date,
                        designation=wh.designation,
                        description=wh.description,
                    )
                    conn.add(new_wh)
                    conn.commit()
                    continue
                wh_ids.append(wh.id)
                old_wh = conn.query(UserWork).filter(UserWork.id == wh.id).first()
                if wh.description is not None:
                    old_wh.description = wh.description
                if wh.designation is not None:
                    old_wh.designation = wh.designation
                if wh.from_date is not None:
                    old_wh.from_date = wh.from_date
                if wh.to_date is not None:
                    old_wh.to_date = wh.to_date
                if wh.company is not None:
                    old_wh.company = wh.company
                conn.commit()
        conn.commit()
        conn.refresh(user_meta_data)
        return user_meta_data

    except Exception as e:
        conn.rollback()
        logging.error(e)
        return ApiError("Something went wrong, we're working on it", 500).as_http_response()


# def user_update_work_history(w_h:UserWorkHistoryUpdate):
#     try:
#         prev_wh = conn.query()

def delete_user(u_a: str):
    try:
        u_m = conn.query(UserMetaData).filter(UserMetaData.user_address == u_a).first()
        u_w = conn.query(UserWork).filter(UserWork.user_address == u_a).all()
        u_f = conn.query(UserPreference).filter(UserPreference.user_address == u_a).all()
        u = conn.query(User).filter(User.public_address == u_a).first()
        if u_m is not None:
            conn.delete(u_m)
            conn.commit()
        if u_w is not None:
            for uw in u_w:
                conn.delete(uw)
                conn.commit()
        if u_f is not None:
            for uf in u_f:
                conn.delete(uf)
                conn.commit()
        if u is not None:
            conn.delete(u)
            conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(e)
        return ApiError("Something went wrong, we're working on it", 500).as_http_response()
