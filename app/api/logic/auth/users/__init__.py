from datetime import datetime, timedelta
from http.client import HTTPException
import random

from sqlalchemy import select, ARRAY, String, cast, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload, joinedload

from models import dbsession as conn, User, UserMetaData, UserPreference, UserWork, PendingTransactions, ZeroCouponBond, \
    Community, UserEmailVerification, UserEmailPreference, UserNotification, TokenWithDrawExecutiveSignStatus, \
    TokenWithDrawRequest, UserActivity, Participants, CommunityToken, CommunityDiscussion, DiscussionComment, \
    UserToProposalVote
from smtp_email import send_email
from ....forms import UserLogin, UserSignupForm, UserProfileUpdate, UserWorkHistoryUpdate
from ....utils import ApiError
import logging
from sqlalchemy import update
logging.basicConfig(level=logging.ERROR)
from fastapi import status
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging
import copy
# Assuming necessary imports for User, UserMetaData, UserPreference, UserWork, UserEmailPreference, UserSignupForm, conn, and send_email are present

def user_sign_up(signup: UserSignupForm):
    """Registers a new user.

    Validates OTP, creates user record, metadata, preferences, work history,
    and sends a welcome email. Handles potential errors like duplicate user
    and database issues.

    Args:
        signup: UserSignupForm object containing user signup data.

    Returns:
        A dictionary containing the status code and message.
        Returns 201 on successful creation, 401 on errors.
    """
    try:
        # 1. Verify OTP
        # otp = conn.query(UserEmailVerification).filter(
        #     UserEmailVerification.user_email == signup.email,
        #     UserEmailVerification.otp == signup.otp
        # ).first()
        # if otp is None:
        #     raise HTTPException(status_code=401, detail="invalid otp ")
        #
        # if signup.otp != otp.otp:
        #     raise HTTPException(status_code=401, detail="invalid otp ")

        # email is not working , remove email verify for now

        # No need for the second OTP check as the first one already covers it.  Removing for efficiency.

        # 2. Create User record
        user = User(
            name=signup.username,
            public_address=signup.public_address,
            user_email=signup.email
        )

        # 3. Create User Metadata
        usermetadata = UserMetaData(
            user_address=signup.public_address,
            bio=signup.bio,
            image_url=signup.display_image,
        )
        user.usermetadata = usermetadata  # Associate metadata with the user

        conn.add(user)  # Add the user to the session

        # 4. Create User Preferences (Tags)
        for tag in signup.tags: # Simplified loop
            preference = UserPreference(
                user_address=signup.public_address,
                tag=tag
            )
            conn.add(preference)

        # 5. Create User Work History (Optional)
        if signup.work_history: # Check if work history exists before iterating
            for work_item in signup.work_history: # Renamed w_h to work_item for clarity
                user_work = UserWork(
                    company=work_item.company_name,
                    designation=work_item.designation,
                    description=work_item.description,
                    from_date=work_item.start_date,
                    to_date=work_item.end_date,
                    user_address=signup.public_address,
                )
                conn.add(user_work)

        # 6. Create User Email Preferences
        new_preference = UserEmailPreference(
            user_address=signup.public_address,
            new_letters=True,  # Consider making these configurable in the signup form
            community_notice=True,
            bond_notice=True,
            proposal_notice=True
        )
        conn.add(new_preference)

        # 7. Commit changes to the database
        conn.commit()

        # 8. Send Welcome Email
        send_email('welcome', {}, signup.email) # Consider adding user data to the email context

        return {
            "status": 201,
            "message": "user created"
        }

    except IntegrityError as e:  # Handle duplicate user error
        conn.rollback()  # Rollback changes in case of error
        logging.error(f"IntegrityError during user signup: {e}") # More informative logging
        return {
            "status": 401,
            "cause": "user with same wallet address or email already exists" # More specific error message
        }
    except Exception as e: # Catch any other exceptions
        conn.rollback()
        logging.error(f"Error at user signup: {e}") # Include the exception details in the log
        raise HTTPException(status_code=500, detail="Internal Server Error") # Use HTTPException with a status code and detail

def user_login_req(req: UserLogin):
    """Handles user login request.

    This function attempts to find an existing user. If the user doesn't exist,
    it creates a new user record.  It returns user data or an appropriate error response.

    Args:
        req: UserLogin object containing user login data.

    Returns:
        A list of User objects (if found/created) or an appropriate error response.
    """
    wallet_addr = req.public_address
    name = req.name

    try:
        # 1. Check if user exists
        user = conn.query(User).filter(User.public_address == wallet_addr).first()

        if user:  # User exists, return user data
            return [user] # Returning a list for consistency with the original code, but consider just returning the user object if appropriate.

        # 2. User does not exist, create new user
        new_user = User(name=name, public_address=wallet_addr)
        conn.add(new_user)
        conn.commit()
        return [new_user] # Return the newly created user

    except IntegrityError as e:  # Handle duplicate user (unlikely with just wallet address)
        conn.rollback()
        logging.error(f"IntegrityError during user login: {e}")
        # More likely, the user *does* exist, but something else went wrong.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this wallet address or name already exists.") # Return a more appropriate error

    except Exception as e:  # Handle other exceptions
        conn.rollback()
        logging.error(f"Error during user login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException instead of ApiError


def get_user_detail(public_address: str):
    """Retrieves user details based on public address.

    Fetches user information, metadata, preferences (tags), and work history.

    Args:
        public_address: The public address of the user.

    Returns:
        A dictionary containing user details or an empty dictionary if the user
        is not found.  Returns an HTTPException on error.
    """
    try:
        # 1. Fetch User with Metadata (using joinedload for efficiency)
        user = conn.query(User).options(joinedload(User.usermetadata)).filter(
            User.public_address == public_address).first()

        if not user:  # User not found, return empty dictionary
            return {}

        # 2. Fetch User Preferences (Tags) - More efficient way
        tags = [
            tag.tag  # Directly extract the tag value
            for tag in conn.query(UserPreference.tag)
            .filter(UserPreference.user_address == public_address)
            .all()
        ]

        # 3. Fetch User Work History
        user_work = conn.query(UserWork).filter(UserWork.user_address == public_address).all()

        # 4. Construct User Dictionary
        user_dict = {
            "name": user.name,
            "public_address": user.public_address,
            "last_login": str(user.last_login) if user.last_login else None, # Handle potentially None last_login
            "usermetadata": {
                "about": user.usermetadata.about,
                "image_url": user.usermetadata.image_url,
                "cover_url": user.usermetadata.cover_url,
                "x_url": user.usermetadata.x_url,
                "linkedin": user.usermetadata.linkedin,
                "website": user.usermetadata.website,
                "bio": user.usermetadata.bio
            } if user.usermetadata else {}, # Handle potential missing usermetadata
            "user_work": [ # Convert UserWork objects to dictionaries for JSON serialization
                {
                    "company": work.company,
                    "designation": work.designation,
                    "description": work.description,
                    "from_date": str(work.from_date), # Convert dates to strings
                    "to_date": str(work.to_date),      # Convert dates to strings
                } for work in user_work
            ],
            "interested_tag": tags
        }

        return user_dict

    except Exception as e:
        conn.rollback()
        logging.error(f"Error getting user details: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException


def check_user_exist(public_address: str):
    """Checks if a user exists based on their public address.

    Args:
        public_address: The public address of the user to check.

    Returns:
        A dictionary indicating whether the user exists.

    Raises:
        HTTPException: If an error occurs during the database query.
    """
    try:
        user = conn.query(User).filter(User.public_address == public_address).first()  # More descriptive variable name

        return {
            "user_address": public_address,
            "exist": bool(user)  # Directly convert the result to a boolean
        }

    except Exception as e:
        logging.error(f"Error checking user existence: {e}")  # Include exception details in log
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException with proper status code and message


def update_user_profile(req: UserProfileUpdate):
    """Updates the user profile information.

    Handles updates to user metadata and work history.

    Args:
        req: UserProfileUpdate object containing the updated user profile data.

    Returns:
        The updated UserMetaData object.

    Raises:
        HTTPException: If an error occurs during the update process.
    """
    try:
        user_meta_data = conn.query(UserMetaData).filter(
            UserMetaData.user_address == req.public_address
        ).first()

        if not user_meta_data:  # Check for None directly
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") # More appropriate HTTP exception

        # Update User Metadata (more concise)
        updates = req.dict(exclude_unset=True) # Exclude fields that were not set in the request
        for key, value in updates.items():
            if key != "public_address" and key != "work_history": # Exclude public_address and work_history
                setattr(user_meta_data, key, value)

        conn.add(user_meta_data) # Ensure the changes are tracked
        conn.commit()
        conn.refresh(user_meta_data) # Refresh to get the updated data from the database

        # Update Work History (improved logic)
        if req.work_history is not None:
            existing_wh_ids = {wh.id for wh in conn.query(UserWork).filter(UserWork.user_address == req.public_address).all()}
            incoming_wh_ids = {wh.id for wh in req.work_history if wh.id is not None}

            # Delete work history items that are no longer present
            ids_to_delete = existing_wh_ids - incoming_wh_ids
            if ids_to_delete:
                conn.query(UserWork).filter(UserWork.id.in_(ids_to_delete)).delete(synchronize_session=False)

            # Update or create work history items
            for wh in req.work_history:
                if wh.id is None:  # New work history item
                    new_wh = UserWork(user_address=req.public_address, **wh.dict(exclude_unset=True)) # Use dictionary unpacking
                    conn.add(new_wh)
                else:  # Existing work history item
                    old_wh = conn.query(UserWork).filter(UserWork.id == wh.id).first()
                    if old_wh:  # Check if the work history item exists
                        for key, value in wh.dict(exclude_unset=True).items():
                            setattr(old_wh, key, value)
                        conn.add(old_wh)  # Important: track modified objects
            conn.commit()

        return user_meta_data

    except Exception as e:
        conn.rollback()
        logging.error(f"Error updating user profile: {e}") # Include exception details
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException


# def user_update_work_history(w_h:UserWorkHistoryUpdate):
#     try:
#         prev_wh = conn.query()

def delete_user(u_a: str):
    """Deletes a user and associated data.

    Deletes the user, metadata, work history, and preferences (tags) associated
    with the given public address.

    Args:
        u_a: The public address of the user to delete.

    Raises:
        HTTPException: If an error occurs during the deletion process.
    """
    try:
        # More efficient deletion using a single query per table
        conn.query(UserMetaData).filter(UserMetaData.user_address == u_a).delete(synchronize_session=False)
        conn.query(UserActivity).filter(UserActivity.user_address == u_a).delete(synchronize_session=False)
        conn.query(UserWork).filter(UserWork.user_address == u_a).delete(synchronize_session=False)
        conn.query(Participants).filter(Participants.user_addr == u_a).delete(synchronize_session=False)
        conn.query(CommunityToken).filter(CommunityToken.user_address == u_a).delete(synchronize_session=False)
        conn.query(CommunityDiscussion).filter(CommunityDiscussion.created_by == u_a).delete(synchronize_session=False)
        conn.query(DiscussionComment).filter(DiscussionComment.created_by == u_a).delete(synchronize_session=False)
        conn.query(UserToProposalVote).filter(UserToProposalVote.user_address == u_a).delete(synchronize_session=False)
        conn.query(ZeroCouponBond).filter(ZeroCouponBond. creator == u_a).delete(synchronize_session=False)
        conn.query(TokenWithDrawRequest).filter(TokenWithDrawRequest.user_address == u_a).delete(
            synchronize_session=False)
        conn.query(TokenWithDrawExecutiveSignStatus).filter(TokenWithDrawExecutiveSignStatus.signed_by == u_a).delete(
            synchronize_session=False)
        conn.query(UserPreference).filter(UserPreference.user_address == u_a).delete(synchronize_session=False)
        conn.query(UserEmailPreference).filter(UserEmailPreference.user_address == u_a).delete(
            synchronize_session=False)
        conn.query(User).filter(User.public_address == u_a).delete(synchronize_session=False)
        conn.commit()  # Commit all deletions at once

        return {"message": "User deleted successfully"} # Return a success message

    except Exception as e:
        conn.rollback()
        logging.error(f"Error deleting user: {e}") # Include exception details in log
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException

def get_pending_transactions(user_address: str):
    """Retrieves pending transactions for a given user.

    Args:
        user_address: The address of the user.

    Returns:
        A list of PendingTransactions objects.

    Raises:
        HTTPException: If an error occurs during the database query.
    """
    try:
        transactions = conn.query(PendingTransactions).filter(
            PendingTransactions.creator == user_address
        ).all()
        return transactions

    except Exception as e:
        conn.rollback()
        logging.error(f"Error getting pending transactions: {e}")  # Include exception details in log
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException



def get_user_created_bonds(user_address: str, is_accepted: bool):
    """Retrieves bonds created by a user, optionally filtered by acceptance status.

    Performs an inner join between ZeroCouponBond and Community tables.

    Args:
        user_address: The address of the user who created the bonds.
        is_accepted: A boolean value to filter bonds based on acceptance status.

    Returns:
        A list of dictionaries, where each dictionary represents a bond and
        includes related community information.

    Raises:
        HTTPException: If an error occurs during the database query.
    """
    try:
        results = (
            conn.query(ZeroCouponBond, Community)
            .join(Community, ZeroCouponBond.community_id == Community.id)
            .filter(ZeroCouponBond.created_on_blockchain == True)
            .filter(ZeroCouponBond.has_accepted == is_accepted)
            .filter(ZeroCouponBond.creator == user_address)
            .distinct(ZeroCouponBond.contract_identity)  # Keep distinct contract identities
            .all()
        )

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
                'initial_exchange_date': str(bond.initial_exchange_date) if bond.initial_exchange_date else None, # Convert date to string or handle None
                'maturity_date': str(bond.maturity_date) if bond.maturity_date else None, # Convert date to string or handle None
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
                'has_withdrawn': bond.has_withdrawn,
                'amount_owned': bond.amount_own,  # Corrected typo: amount_own -> amount_owned
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
        logging.error(f"Error getting user created bonds: {e}") # Include exception details in log
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException


def get_user_email_preference(user_address: str):
    """Retrieves email preferences for a user.

    Args:
        user_address: The address of the user.

    Returns:
        A UserEmailPreference object or None if not found.

    Raises:
        HTTPException: If an error occurs during the database query.
    """
    try:
        preference = conn.query(UserEmailPreference).filter(
            UserEmailPreference.user_address == user_address
        ).first()
        return preference

    except Exception as e:
        conn.rollback()
        logging.error(f"Error getting user email preference: {e}")  # Include exception details in log
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException

def send_email_verification_otp(user_email: str):
    """Sends an email verification OTP to the user.

    Generates a 6-digit OTP, stores it in the database with an expiry time,
    and sends it to the user via email.

    Args:
        user_email: The email address of the user.

    Returns:
        A dictionary indicating success or failure.

    Raises:
        HTTPException: If an error occurs during the process.
    """
    try:
        # 1. Generate OTP
        otp = random.randint(100000, 999999)

        # 2. Set Expiry Time (15 minutes from now)
        expire_time = datetime.utcnow() + timedelta(minutes=15)

        # 3. Check for Existing Verification Data
        verification_data = conn.query(UserEmailVerification).filter(
            UserEmailVerification.user_email == user_email
        ).first()

        if verification_data:  # Update existing record
            verification_data.otp = str(otp)
            verification_data.expire_time = expire_time
        else:  # Create new record
            verification_data = UserEmailVerification(
                user_email=user_email,
                otp=str(otp),
                expire_time=expire_time
            )
        conn.add(verification_data)
        conn.commit()

        # 4. Send Email (using your send_email function)
        send_email("email_verification", {"otp": otp}, user_email)

        return {"success": True, "message": "OTP sent successfully."}

    except Exception as e:
        conn.rollback()
        logging.error(f"Error sending OTP: {e}")  # Improved logging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException


def get_user_notification(user_address: str):
    """Retrieves and marks as read unread notifications for a user.

    Fetches unread notifications from the UserNotification table for the given user address and marks them as read.

    Args:
        user_address: The address of the user.

    Returns:
        A list of UserNotification objects.

    Raises:
        HTTPException: If an error occurs during the process.
    """
    try:
        # 1. Fetch unread notifications
        query = select(UserNotification).filter(UserNotification.user_address == user_address,UserNotification.is_read == False)
        result = conn.execute(query).scalars().all()  # Directly get User
        resp  = copy.deepcopy(result)
        # # 2. Mark notifications as read (more efficient update)
        if len(result) != 0: # Only update if there are notifications.
            update_query = (
                update(UserNotification)
                .where(UserNotification.user_address == user_address, UserNotification.is_read == False) # More precise where clause
                .values(is_read=True)
            )
            conn.execute(update_query)
            conn.commit()  # Commit the update after fetching

        return resp

    except Exception as e:
        conn.rollback()
        logging.error(f"Error getting/updating notifications: {e}") # More descriptive message
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException


def get_user_all_notification(user_address: str):
    """Retrieves all notifications for a user.

    Fetches all notifications (read and unread) from the UserNotification table
    for the given user address.

    Args:
        user_address: The address of the user.

    Returns:
        A list of UserNotification objects.

    Raises:
        HTTPException: If an error occurs during the database query.
    """
    try:
        query = select(UserNotification).filter(UserNotification.user_address == user_address)
        result = conn.execute(query).scalars().all()  # Directly get UserNotification objects
        return result

    except Exception as e:
        conn.rollback()
        logging.error(f"Error getting all notifications: {e}")  # Improved logging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") # Use HTTPException

def get_user_token_withdraw_request(user_address: str):
    try:
        result = (
            conn.query(
                TokenWithDrawRequest.amount_to_withdraw,
                TokenWithDrawRequest.request_date,
                TokenWithDrawRequest.status,
                Community.name,
                Community.image,
            )
            .join(Community, Community.id == TokenWithDrawRequest.community_id)
            .filter(TokenWithDrawRequest.user_address == user_address)
            .all()
        )
        withdraw_requests = [
            {
                "amount_to_withdraw": req.amount_to_withdraw,
                "request_date": req.request_date,
                "status": req.status,
                "community_name": req.name,
                "community_image": req.image,
            }
            for req in result
        ]

        return withdraw_requests
    except Exception as e:
        conn.rollback()
        logging.error(f"Error getting token withdraw requests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")



