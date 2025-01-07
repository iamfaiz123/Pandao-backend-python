from datetime import datetime, timedelta
from http.client import HTTPException
import random

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload, joinedload

from models import dbsession as conn, User, UserMetaData, UserPreference, UserWork, PendingTransactions, ZeroCouponBond, \
    Community, UserEmailVerification, UserEmailPreference
from smtp_email import send_email
from ....forms import UserLogin, UserSignupForm, UserProfileUpdate, UserWorkHistoryUpdate
from ....utils import ApiError
import logging

logging.basicConfig(level=logging.ERROR)


def user_sign_up(signup: UserSignupForm):
    try:
        # first match the otp
        otp = conn.query(UserEmailVerification).filter(UserEmailVerification.user_email == signup.email).filter(UserEmailVerification.otp == signup.otp).first()
        if otp is None:
            return {
            "status": 401,
            "cause": "invalid otp"
        }
        user = User(
            name=signup.username,
            public_address=signup.public_address,
            user_email=signup.email
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
        new_preference = UserEmailPreference(
            user_address=signup.public_address,
            new_letters=True,
            community_notice=True,
            bond_notice=True,
            proposal_notice=True
        )
        conn.add(new_preference)
        conn.commit()
        send_email('welcome',{},signup.email)
        return {
            "status": 201,
            "message": "user created "
        }
    except IntegrityError as e:
        print(e)
        conn.rollback()
        return {
            "status": 401,
            "cause": "user with same wallet address already exists"
        }
    except Exception as e:
        print(e)
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

        query = (
            conn.query(UserPreference.tag)
            .filter(UserPreference.user_address == public_address)
        )

        # Execute the query and fetch all results
        tags = query.all()
        # Extract tags from the result (tags will be a list of tuples, so we extract the first element from each)
        tag_list = [tag[0] for tag in tags]

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
                "user_work": user_wh,
                "interested_tag":tag_list
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

def get_pending_transactions(user_address: str):
    try:
        transactions = conn.query(PendingTransactions).filter(PendingTransactions.creator == user_address).all()
        return transactions
    except Exception as e:
        conn.rollback()
        logging.error(e)
        return ApiError("Something went wrong, we're working on it", 500).as_http_response()



def get_user_created_bonds(user_address:str,is_accepted:bool):
    try:
        # Perform an inner join between ZeroCouponBond and Community
        results = (conn.query(ZeroCouponBond, Community).join(Community,
                                                                ZeroCouponBond.community_id == Community.id).filter(ZeroCouponBond.created_on_blockchain == True)
                   .filter(ZeroCouponBond.has_accepted == is_accepted).filter(ZeroCouponBond.creator == user_address).distinct(ZeroCouponBond.contract_identity).all())

        # Convert the results to a list of dictionaries
        bond_data = []
        for bond, community in results:
            bond_dict = {
                'bond_id': bond.id,
                'name': bond.name,
                'symbol': bond.symbol,
                'description': bond.description,
                'creator': bond.creator,
                'bond_price': bond.bond_price,
                'interest_rate': bond.interest_rate,
                'contract_type': bond.contract_type,
                'contract_role': bond.contract_role,
                'contract_identity': bond.contract_identity,
                'currency': bond.currency,
                'initial_exchange_date': bond.initial_exchange_date,
                'maturity_date': bond.maturity_date,
                'notional_principle': bond.notional_principle,
                'discount': bond.discount,
                'bond_position': bond.bond_position,
                'price': bond.price,
                'number_of_bonds': bond.number_of_bonds,
                'created_on_blockchain': bond.created_on_blockchain,
                'asset_address': bond.asset_address,
                'asset_url': bond.asset_url,
                'asset_name': bond.asset_name,
                'amount_stored': bond.amount_stored,
                'has_withdrawn':bond.has_withdrawn,
                'amount_owned':bond.amount_own,
                'community': {
                    'community_id': community.id,
                    'name': community.name,
                    'component_address': community.component_address,
                    'description': community.description,
                    'blueprint_slug': community.blueprint_slug,
                    'token_address': community.token_address,
                    'owner_token_address': community.owner_token_address,
                    'image': community.image,
                    'token_image': community.token_image,
                    'token_price': community.token_price,
                    'token_buy_back_price': community.token_buy_back_price,
                    'total_token': community.total_token,
                    'token_bought': community.token_bought,
                    'owner_address': community.owner_address,
                    'funds': community.funds,
                    'purpose': community.purpose,
                    'proposal_rights': community.proposal_rights,
                    'proposal_minimum_token': community.proposal_minimum_token
                }
            }
            bond_data.append(bond_dict)

        return bond_data

    except Exception as e:
        conn.rollback()
        logging.error(e)
        return ApiError("Something went wrong, we're working on it", 500).as_http_response()
def get_user_email_preference(user_address:str):
    try:
        preference = conn.query(UserEmailPreference).filter(UserEmailPreference.user_address == user_address).first()
        return preference
    except Exception as e:
        conn.rollback()
        logging.error(e)
        return ApiError("Something went wrong, we're working on it", 500).as_http_response()

def send_email_verification_otp(user_email: str):
    try:
        # Generate a random 6-digit OTP
        otp = random.randint(100000, 999999)
        # Set the expiration time to 15 minutes from now
        expire_time = datetime.utcnow() + timedelta(minutes=15)
        verification_data = conn.query(UserEmailVerification).filter(UserEmailVerification.user_email == user_email).first()
        if verification_data is None:
            # Create a new verification record
            verification_data = UserEmailVerification(
                user_email=user_email,
                otp=str(otp),
                expire_time=expire_time
            )
        else:
            verification_data.otp = str(otp)
            verification_data.expire_time = expire_time

        conn.add(verification_data)
        # Commit the transaction to save the record
        conn.commit()
        # Send the OTP via email (pseudo-function, implement your email-sending logic)
        send_email("email_verification",{"otp":otp},user_email)
        return {"success": True, "message": "OTP sent successfully."}

    except Exception as e:
        # Rollback in case of any failure
        conn.rollback()
        print(f"Error: {e}")
        return {"success": False, "message": f"Error sending OTP: {e}"}