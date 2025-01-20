import uuid

import requests
import sqlalchemy
from sqlalchemy import or_, select, func, desc, distinct
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.api.forms.blueprint import DeployCommunity
from app.api.forms.community import ProposalComment, CommunityDiscussionComment, CommunityFilter
from app.api.logic.external_apis.external_apis import get_price_conversion
from app.api.logic.wallet import get_asset_details
# from app.api.forms.blueprint import DeployCommunity
from models import dbsession as conn, BluePrint, Community as Com, User, Participants, UserMetaData, \
    UserActivity, Community, CommunityToken, Proposal, ProposalComments, CommunityDiscussion, DiscussionComment, \
    CommunityTags, ZeroCouponBond, AnnTokens, CommunityFunds, CommunityExpense, CommunityNotice, UserPreference, \
    UserToProposalVote
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.exc import SQLAlchemyError

# define models
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

import random
import string


def generate_random_string(length=12):
    # Define the characters to choose from (letters and digits)
    characters = string.ascii_letters + string.digits
    # Generate a random string of the specified length
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def get_community(sort: str):
    query = conn.query(Community, func.count(Participants.id).label('participants_count')) \
        .outerjoin(Participants, Community.id == Participants.community_id) \
        .group_by(Community.id)
    if sort == 'participants':
        query = query.order_by(func.count(Participants.id).desc())
    elif sort == 'funds':
        query = query.order_by(Community.funds.desc())
    elif sort == 'name':
        query = query.order_by(Community.name.asc())

    communities_with_participants = query.limit(6).all()

    # Now you can iterate over the result
    response = []
    for community, participant_count in communities_with_participants:
        response.append(
            {
                "component_address": community.component_address,
                "id": community.id,
                "blueprint_slug": community.blueprint_slug,
                "owner_token_address": community.owner_token_address,
                "token_price": community.token_price,
                "total_token": community.total_token,
                "owner_address": community.owner_address,
                "name": community.name,
                "number_of_participants": participant_count,
                "image": community.image,
                "funds": community.funds,
                "description": community.description
            }
        )
    return response


def get_all_community_of_platform(name,sort,tag):
    query = (
        conn.query(
            Community,
            func.count(func.distinct(Participants.id)).label('participants_count')
        )
        .outerjoin(Participants, Community.id == Participants.community_id)
        .outerjoin(CommunityTags, Community.id == CommunityTags.community_id)
        .group_by(Community.id)
    )

    if sort is not None:
        if sort == 'participants':
            query = query.order_by(func.count(Participants.id).desc())
        elif sort == 'funds':
           query = query.order_by(Community.funds.desc())
        elif sort == 'name':
            query = query.order_by(Community.name.asc())
    if name is not None:
        query = query.filter(Community.name.ilike(f"%{name}%"))
    if tag is not None:
        query = query.filter(CommunityTags.tag == sqlalchemy.any_(tag) )
    communities_with_participants = query.limit(1000).all()
    # Now you can iterate over the result
    # Now you can iterate over the result
    response = []
    for community, participant_count in communities_with_participants:
        # get all the tags of the community
        c_tags = conn.query(CommunityTags).filter(CommunityTags.community_id == community.id).all()
        tags = []
        if c_tags is not None:
            for ct in c_tags:
                tags.append(ct.tag)
        response.append(
            {
                "component_address": community.component_address,
                "id": community.id,
                "blueprint_slug": community.blueprint_slug,
                "owner_token_address": community.owner_token_address,
                "token_price": community.token_price,
                "total_token": community.total_token,
                "owner_address": community.owner_address,
                "name": community.name,
                "number_of_participants": participant_count,
                "image": community.image,
                "funds": community.funds,
                "description": community.description,
                "tags": tags,
                "purpose": community.purpose
            }
        )
    return response


def get_user_community(user_addr: str):
    communities = conn.query(Com).join(
        Participants, Com.id == Participants.community_id, isouter=True
    ).filter(
        or_(
            Com.owner_address == user_addr,
            Participants.user_addr == user_addr
        )
    ).all()
    return communities


def create_community(community: DeployCommunity):
    pass
    # try:
    #     # get events emitted from the blueprint
    #     tx_deploy_events = token_bucket_deploy_event_listener(community.tx_id)
    #     # create a new community with data
    #     db_community = Com(
    #         name=community.name,
    #         component_address=tx_deploy_events['component_address'],
    #         token_address=tx_deploy_events['token_address'],
    #         owner_token_address=tx_deploy_events['owner_token_address'],
    #         description=community.description,
    #         owner_address=community.user_address
    #     )
    #
    #     conn.add(db_community)
    #     conn.commit()
    #     conn.refresh(db_community)
    #     return db_community
    # except SQLAlchemyError as e:
    #     # Log the error e
    #     print(e)
    #     raise HTTPException(status_code=500, detail="Internal Server Error")




def user_participate_in_community(user_addr: str, community_id: uuid.UUID):
    try:
        # create new user participant

        # first check if user exist in the community or not
        already_participated =  conn.query(Participants).filter(Participants.user_addr == user_addr).filter(Participants.community_id == community_id).first()
        if already_participated is not None:
            raise HTTPException(status_code=401, detail="user is already part of community")
        participant = Participants(
            user_addr=user_addr,
            community_id=community_id,
        )

        conn.add(participant)
        community = conn.query(Community).filter(Community.id == community_id).first()
        community_name = community.name
        random_string = generate_random_string()
        # add comment activity
        activity = UserActivity(
            transaction_id=random_string,
            transaction_info=f'participated in {community_name}',
            user_address=user_addr,
            community_id=community_id,
            activity_type='participate'
        )
        conn.add(activity)

        # create a community notice
        # c_n = CommunityNotice(
        #     creator = user_addr ,
        #     date = datetime.now() ,
        #     notice = 'welcome new member !',
        #     community_id = community_id
        # )
        # conn.add(c_n)
        conn.commit()
        return {
            "participated":True
        }
    except IntegrityError as e:
        print(e)
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


def get_community_participants(community_id: UUID):
    from sqlalchemy import func, case, distinct, and_
    try:
        result = (
            conn.query(
                User.name.label("name"),
                User.public_address,
                UserMetaData.image_url,
                func.count(distinct(UserActivity.transaction_id)).label("activities"),
                func.coalesce(func.sum(CommunityExpense.xrd_spent), 0).label("total_invested"),
                func.coalesce(
                    func.sum(
                        case(
                            (UserActivity.activity_type == "token_bought", 1),
                            else_=0
                        )
                    ),
                    0,
                ).label("token_bought"),
                func.coalesce(
                    func.sum(
                        case(
                            (UserActivity.activity_type == "token_sold", 1),
                            else_=0
                        )
                    ),
                    0,
                ).label("token_sold"),
                func.coalesce(
                    func.sum(
                        case(
                            (UserActivity.activity_type == "proposal_voted", 1),
                            else_=0
                        )
                    ),
                    0,
                ).label("proposal_voted"),
                func.coalesce(
                    func.sum(
                        case(
                            (UserActivity.activity_type == "commented on a proposal", 1),
                            else_=0
                        )
                    ),
                    0,
                ).label("commented_on_proposal"),
                func.coalesce(
                    func.sum(
                        case(
                            (UserActivity.activity_type == "discussion_comment", 1),
                            else_=0
                        )
                    ),
                    0,
                ).label("discussion_comment"),
                func.coalesce(
                    func.sum(
                        case(
                            (UserActivity.activity_type == "proposal_created", 1),
                            else_=0
                        )
                    ),
                    0,
                ).label("proposal_created"),
                func.coalesce(
                    func.sum(
                        case(
                            (UserActivity.activity_type == "zero_coupon_bond_created", 1),
                            else_=0
                        )
                    ),
                    0,
                ).label("zero_coupon_bond_created"),
                func.coalesce(
                    func.sum(
                        case(
                            (UserActivity.activity_type == "discussion", 1),
                            else_=0
                        )
                    ),
                    0,
                ).label("discussion"),
            )
            .join(UserMetaData, UserMetaData.user_address == User.public_address)
            .join(
                Participants,
                and_(
                    Participants.user_addr == User.public_address,
                    Participants.community_id == community_id,
                ),
            )
            .join(
                UserActivity,
                and_(
                    UserActivity.user_address == User.public_address,
                    UserActivity.community_id == Participants.community_id,
                ),
            )
            .outerjoin(
                CommunityExpense,
                and_(
                    CommunityExpense.creator == UserActivity.user_address,
                    CommunityExpense.community_id == UserActivity.community_id,
                    CommunityExpense.tx_hash == UserActivity.transaction_id,
                ),
            )
            .group_by(User.public_address, User.name, UserMetaData.image_url)
            .all()
        )

        # Return the result as a list of dictionaries
        return [
            {
                "name": row.name,
                "public_address": row.public_address,
                "image_url": row.image_url,
                "activities": row.activities,
                "total_invested": row.total_invested,
                "token_bought": row.token_bought,
                "token_sold": row.token_sold,
                "proposal_voted": row.proposal_voted,
                "commented_on_proposal": row.commented_on_proposal,
                "discussion_comment": row.discussion_comment,
                "proposal_created": row.proposal_created,
                "zero_coupon_bond_created": row.zero_coupon_bond_created,
                "discussion": row.discussion,
            }
            for row in result
        ]
    except IntegrityError as e:
        conn.rollback()
        print(e)

        raise HTTPException(status_code=400,
                            detail="Integrity error: possibly duplicate entry or foreign key constraint.")

    except SQLAlchemyError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(e)
        conn.rollback()

        raise HTTPException(status_code=500, detail="Internal Server Error")



def check_user_community_status(user_addr: str, community_id: uuid.UUID):
    try:
        user_data = conn.query(Participants).filter(Participants.community_id == community_id,
                                                            Participants.user_addr == user_addr).first()
        if user_data is None:
            return {
                "user_participated": False
            }
        else:
            return {
                "user_participated": True
            }
    except IntegrityError as e:
        conn.rollback()
        print(e)

        raise HTTPException(status_code=400,
                            detail="Integrity error: possibly duplicate entry or foreign key constraint.")

    except SQLAlchemyError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(e)
        conn.rollback()

        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_community_comments(c_id: uuid.UUID):
    # Join the tables
    latest_comment_subquery = (
        conn.query(
            DiscussionComment.discussion_id,
            func.max(DiscussionComment.created_at).label('last_comment_at')
        )
        .group_by(DiscussionComment.discussion_id)
        .subquery()
    )

    # Alias the subquery for joining
    LatestComment = latest_comment_subquery

    # Main query
    results = (
        conn.query(
            distinct(CommunityDiscussion.id).label('id'),
            CommunityDiscussion.created_at,
            CommunityDiscussion.title,
            User.name,
            UserMetaData.image_url,
            User.public_address,
            LatestComment.c.last_comment_at
        )
        .join(User, CommunityDiscussion.created_by == User.public_address)
        .join(UserMetaData, User.public_address == UserMetaData.user_address)
        .join(LatestComment, LatestComment.c.discussion_id == CommunityDiscussion.id)
        .filter(CommunityDiscussion.community_id == c_id)
        .order_by(LatestComment.c.last_comment_at)
        .all()
    )


    # Format the response
    comments = [
        {
            "title": row.title,
            "user_name": row.name,
            "user_image": row.image_url,
            "user_address": row.public_address,
            "id": row.id,
            "created_at": row.created_at,
            "last_comment":row.last_comment_at
        }
        for row in results
    ]

    return comments


def get_discussion_comments(d_id: uuid.UUID):
    # Join the tables
    results = (conn.query(DiscussionComment.comment, DiscussionComment.image, DiscussionComment.created_at, User.name,
                          UserMetaData.image_url,
                          User.public_address).join(User,
                                                    DiscussionComment.created_by == User.public_address).join(
        UserMetaData, User.public_address == UserMetaData.user_address).filter(
        DiscussionComment.discussion_id == d_id)
               .order_by(
        desc(DiscussionComment.created_at)  # Order by created_at in descending order
    )
               .all())

    # Format the response
    comments = [
        {
            "comment": row.comment,
            "user_name": row.name,
            "user_image": row.image_url,
            "user_address": row.public_address,
            "created_at": row.created_at,
            "image": row.image
        }
        for row in results
    ]

    return comments


def get_single_community(community_id: uuid.UUID):
    communities = conn.query(Com).filter(Com.id == community_id).first()
    funds_in_usd = 0
    if communities.funds != 0:
        funds_in_usd = get_price_conversion(communities.funds, 'USD')
    token_price_in_usd = get_price_conversion(communities.token_price, 'USD')
    token_buy_back_price_in_usd = get_price_conversion(communities.token_buy_back_price, 'USD')
    community_token_data = get_asset_details(communities.token_address)
    resp = {
        "id": communities.id,
        "name": communities.name,
        "component_address": communities.component_address,
        "description": communities.description,
        "blueprint_slug": communities.blueprint_slug,
        "token_address": communities.token_address,
        "owner_token_address": communities.owner_token_address,
        "image": communities.image,
        "token_image": communities.token_image,
        "token_price": communities.token_price,
        "token_buy_back_price": communities.token_buy_back_price,
        "total_token": communities.total_token,
        "token_bought": communities.token_bought,
        "owner_address": communities.owner_address,
        "funds": communities.funds,
        "purpose": communities.purpose,
        "proposal_rights": communities.proposal_rights,
        "proposal_minimum_token": communities.proposal_minimum_token,
        "funds_in_usd": funds_in_usd,
        "token_price_in_usd": token_price_in_usd,
        "token_buy_back_price_in_usd": token_buy_back_price_in_usd,
        "token_details":community_token_data

    }
    return resp


def add_community_discussion_comment(req: CommunityDiscussionComment):
    try:
        user_address = req.user_addr
        discussion_id = req.discussion_id
        comment = req.comment
        image = req.image

        new_comment = DiscussionComment(
            discussion_id=discussion_id,
            created_by=user_address,
            comment=comment,
            image=image
        )
        # get user data and community data

        # get community id
        discussion = conn.query(CommunityDiscussion).filter(CommunityDiscussion.id == discussion_id).first()
        random_string = generate_random_string()
        community = conn.query(Community).filter(Community.id == discussion.community_id).first()
        community_name = community.name
        does_user_exist = conn.query(Participants).filter(Participants.community_id == discussion.community_id,
                                                          Participants.user_addr == user_address).first()
        if not does_user_exist:
            raise HTTPException(status_code=401, detail="not a community participant")
        # add comment activity
        activity = UserActivity(
            transaction_id=random_string,
            transaction_info=f'added a new comment in {discussion.title}',
            user_address=user_address,
            community_id=discussion.community_id,
            activity_type='discussion_comment'
        )
        conn.add(new_comment)
        conn.add(activity)
        conn.commit()

    except IntegrityError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=400,
                            detail="Integrity error: possibly duplicate entry or foreign key constraint.")

    except SQLAlchemyError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        conn.rollback()
        return e


def get_community_tags(community_id: uuid.UUID):
    c_tags = conn.query(CommunityTags).filter(CommunityTags.community_id == community_id).all()
    tags = []
    if c_tags is not None:
        for ct in c_tags:
            tags.append(ct.tag)
    return {
        'tags': tags
    }


def add_community_comment(req: CommunityDiscussion):
    try:
        c_id = req.community_id
        u_adr = req.user_addr
        c = req.discussion_title

        new_comment = CommunityDiscussion(
            community_id=c_id,
            created_by=u_adr,
            title=c
        )
        # get user data and community data
        random_string = generate_random_string()
        community = conn.query(Community).filter(Community.id == c_id).first()
        community_name = community.name
        does_user_exist = conn.query(Participants).filter(Participants.community_id == c_id,
                                                          Participants.user_addr == u_adr).first()
        if not does_user_exist:
            raise HTTPException(status_code=401, detail="not a community participant")
        # add comment activity
        activity = UserActivity(
            transaction_id=random_string,
            transaction_info=f'created a new discussion in {community_name}',
            user_address=u_adr,
            community_id=c_id,
            activity_type='discussion'
        )
        conn.add(new_comment)
        conn.add(activity)
        conn.commit()
        return new_comment

    except IntegrityError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=400,
                            detail="Integrity error: possibly duplicate entry or foreign key constraint.")

    except SQLAlchemyError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        conn.rollback()
        print(e)
        raise e


def get_community_metadata_details(community_id: uuid.UUID):
    try:
        # https://babylon-stokenet-gateway.radixdlt.com/state/entity/details
        # get community component address
        community = conn.query(Community).filter(Community.id == community_id).first()
        url = "https://babylon-stokenet-gateway.radixdlt.com/state/entity/details"

        # Define the JSON data
        data = {
            "addresses": [community.component_address],
            "aggregation_level": "Vault",
            "opt_ins": {
                "ancestor_identities": False,
                "component_royalty_vault_balance": False,
                "explicit_metadata": [],
                "non_fungible_include_nfids": True,
                "package_royalty_vault_balance": False
            }
        }

        # Make the request
        tokens = {}

        response = requests.post(url, json=data)
        response = response.json()
        fungible_resources = response['items'][0]['fungible_resources']
        for data in fungible_resources:
            pass
    finally:
        pass


class CommentResponse(BaseModel):
    user_name: str
    image_url: str
    public_address: str
    comment: str
    timestamp: datetime


def get_proposal_comment(proposal_id: uuid.UUID):
    comments = conn.execute(
        select(
            ProposalComments.comment,
            ProposalComments.timestamp,
            User.name,
            UserMetaData.image_url,
            User.public_address
        ).join(
            User, ProposalComments.user_id == User.public_address
        ).join(
            UserMetaData, User.public_address == UserMetaData.user_address
        ).where(
            ProposalComments.proposal_id == proposal_id
        )
    ).all()

    result = [
        CommentResponse(
            user_name=comment.name,
            image_url=comment.image_url,
            public_address=comment.public_address,
            comment=comment.comment,
            timestamp=comment.timestamp
        )
        for comment in comments
    ]

    if result is None:
        return []

    return result


class Praposalomment:
    pass


def add_proposal_comment(req: ProposalComment):
    try:
        new_comment = ProposalComments(
            proposal_id=req.proposal_id,
            comment=req.comment,
            user_id=req.user_addr
        )

        conn.add(new_comment)
        # create a new activity
        proposal_data = conn.query(Proposal).filter(Proposal.id == req.proposal_id).first()
        user_data = user = conn.query(User).options(joinedload(User.usermetadata)).filter(
            User.public_address == req.user_addr).first()
        # create a new activity
        community = conn.query(Community).filter(Community.id == proposal_data.community_id).first()
        community_name = community.name
        random_string = generate_random_string()
        activity = UserActivity(
            transaction_id=random_string,
            transaction_info=f'commented on a proposal in {community.name} community',
            user_address=req.user_addr,
            community_id=proposal_data.community_id,
            activity_type ='proposal_comment'
        )
        conn.add(activity)
        conn.commit()
        return new_comment
    except IntegrityError as e:
        conn.rollback()

        raise HTTPException(status_code=400,
                            detail="Integrity error: possibly duplicate entry or foreign key constraint.")

    except SQLAlchemyError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_community_tokens(community_id: uuid.UUID):
    # Query the database for tokens owned by users in the community
    stmt = (
        select(
            CommunityToken.token_owned,
            User.name,
            UserMetaData.image_url,
            User.public_address
        )
        .join(User, User.public_address == CommunityToken.user_address)
        .join(UserMetaData, UserMetaData.user_address == CommunityToken.user_address)
        .filter(CommunityToken.community_id == community_id)
    )

    result = conn.execute(stmt)
    if not result:
        raise HTTPException(status_code=404, detail="Community not found")
    response = []
    for data in result:
        response.append(
            {
                "user_name": data[1],
                "token_owned": data[0],
                "image": data[2],
                "public_address": data[3]
            }
        )
    return response


def get_community_active_proposal(community_id: uuid.UUID):
    proposal = conn.query(Proposal).filter(Proposal.community_id == community_id, Proposal.is_active == True).all()
    return proposal


def get_community_all_proposal(community_id: uuid.UUID,status:str):
    proposal = None
    if status == 'PENDING':
        proposal = conn.query(Proposal).filter(Proposal.community_id == community_id).filter(Proposal.status == 1).all()
    elif status == 'EXECUTED':
        proposal = conn.query(Proposal).filter(Proposal.community_id == community_id).filter(Proposal.status != 1).all()
    else:
        proposal = conn.query(Proposal).filter(Proposal.community_id == community_id).all()
    return proposal


def get_user_communities(user_addr: str, owner: bool):
    try:
        if not owner:
            results = (
                conn.query(Community.id, Community.name, Community.component_address, Community.image)
                .join(Participants, Community.id == Participants.community_id)
                .filter(Participants.user_addr == user_addr)
                .distinct(Community.id)
                .all()
            )
        else:
            results = (
                conn.query(Community.id, Community.name, Community.component_address, Community.image)
                .join(Participants, Community.id == Participants.community_id)
                .filter(Community.owner_address == user_addr)
                .distinct(Community.id)
                .all()
            )

        communities = [
            {
                "community_id": row.id,
                "community_name": row.name,
                "component_address": row.component_address,
                "community_image": row.image

            }
            for row in results
        ]
        return communities
    except SQLAlchemyError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="dssdrror")
    except Exception as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="Internal Servesvsvsvsdvr Error")


def get_community_all_zero_coupon_bonds(community_id: uuid.UUID,purchased:bool):
    proposal = conn.query(ZeroCouponBond).filter(ZeroCouponBond.community_id == community_id).filter(ZeroCouponBond.created_on_blockchain == True).filter(ZeroCouponBond.has_accepted ==purchased ).all()
    return proposal

def get_community_all_ann_tokens(community_id: uuid.UUID):
    ann = conn.query(AnnTokens).filter(AnnTokens.community_id == community_id).all()
    # .filter(AnnTokens.created_on_blockchain == True)
    return ann

def get_bonds_name(community_id: uuid.UUID):
    try:
        query = conn.query(ZeroCouponBond.creator, ZeroCouponBond.name,ZeroCouponBond.price).filter(
            ZeroCouponBond.community_id == community_id,
            ZeroCouponBond.created_on_blockchain == True,
            ZeroCouponBond.has_accepted == False
        )

        results = query.all()

        if results is None:
            return []

        response = [
            {
                "bond_name": row.name,
                "creator_address": row.creator,
                "price":row.price

            }
            for row in results
        ]

        return response
    except SQLAlchemyError as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="dssdrror")
    except Exception as e:
        conn.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


def community_funds_history(community_id: uuid.UUID):
    try:
        # Perform the left join query
        query = conn.query(
            CommunityFunds.id,
            CommunityFunds.community_id,
            CommunityFunds.xrd_added,
            CommunityFunds.current_xrd,
            CommunityFunds.creator,
            CommunityFunds.tx_hash,
            CommunityFunds.date,
            UserMetaData.user_address,
            UserMetaData.image_url,
            User.name
        ).outerjoin(
            UserMetaData,
            CommunityFunds.creator == UserMetaData.user_address
        ).outerjoin(
            User,
            CommunityFunds.creator == User.public_address
        ).filter(
            CommunityFunds.community_id == community_id
        ).order_by(
            CommunityFunds.date.desc()
        )
        # Execute the query and fetch the results
        results = query.all()
        response = []
        for result in results:
            response.append({
                "id": str(result.id),
                "community_id": str(result.community_id),
                "xrd_added": result.xrd_added,
                "current_xrd": result.current_xrd,
                "creator": result.creator,
                "tx_hash": result.tx_hash,
                "date": result.date.isoformat(),
                "user_address": result.user_address,
                "image_url": result.image_url,
                "user_name":result.name
            })
        return response
    except SQLAlchemyError as e:
        conn.rollback()
        print(f"SQLAlchemy error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        conn.rollback()
        print(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_user_expense(user_addr: str):
    try:
        query = conn.query(
            CommunityExpense.id,
            CommunityExpense.community_id,
            CommunityExpense.xrd_spent,
            CommunityExpense.creator,
            CommunityExpense.tx_hash,
            CommunityExpense.xrd_spent_on,
            CommunityExpense.date,
            Community.name.label('community_name'),
            Community.image.label('community_image')
        ).join(
            Community,
            CommunityExpense.community_id == Community.id
        ).filter(
            CommunityExpense.creator == user_addr
        ).order_by(
            CommunityExpense.date.desc()
        )

        # Execute the query and fetch the results
        results = query.all()

        # Store the results in a list of dictionaries
        response = []
        for result in results:
            response.append({
                "id": str(result.id),
                "community_id": str(result.community_id),
                "xrd_spent": result.xrd_spent,
                "creator": result.creator,
                "tx_hash": result.tx_hash,
                "xrd_spent_on": result.xrd_spent_on,
                "date": result.date.isoformat(),
                "community_name": result.community_name,
                "community_image":result.community_image
            })
        return response
    except SQLAlchemyError as e:
        conn.rollback()
        print(f"SQLAlchemy error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        conn.rollback()
        print(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def get_proposal_bond(proposal_id:uuid):
    try:
        proposal = conn.query(Proposal).filter(
            Proposal.id == proposal_id
        ).first()
        if proposal is not None:
            bond = conn.query(ZeroCouponBond).filter(ZeroCouponBond.community_id == proposal.community_id).filter(ZeroCouponBond.creator == proposal.zcb_bond_creator).first()
            return bond
        else:
            raise HTTPException(status_code=401, detail="invalid proposal id")
    except SQLAlchemyError as e:
        conn.rollback()
        print(f"SQLAlchemy error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        conn.rollback()
        print(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_communities_user_might_be_int_in(user_address:str):
    try:
        query = (
            conn.query(UserPreference.tag)
            .filter(UserPreference.user_address == user_address)
        )

        # Execute the query and fetch all results
        tags = query.all()
        # Extract tags from the result (tags will be a list of tuples, so we extract the first element from each)
        tag_list = [tag[0] for tag in tags]
        query = (
            conn.query(CommunityTags.community_id)
            .join(UserPreference, CommunityTags.tag == UserPreference.tag)
            .outerjoin(Participants,Participants.community_id == CommunityTags.community_id )
            .filter(UserPreference.user_address == user_address)
            .filter(Participants.user_addr is None)
            .filter(UserPreference.tag.in_(query))  # Check if the tag is in the user's preference list
            .distinct()  # Ensure no duplicates
        )
        # Execute the query
        result = query.all()
        community_ids = [community_id[0] for community_id in result]
        query = (
            conn.query(Community)
            .filter(Community.id.in_(community_ids))
        )

        resp = query.all()
        return resp
    finally:
        pass


def check_user_has_voted(proposal_id:uuid, user_address:str):
    try:
        vote = conn.query(UserToProposalVote).filter(UserToProposalVote.proposal_id == proposal_id).filter(UserToProposalVote.user_address == user_address).first()
        if vote is None:
            return {
                'voted':False
            }
        else:
            return {
                'voted':True
            }
    except SQLAlchemyError as e:
        conn.rollback()
        print(f"SQLAlchemy error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        conn.rollback()
        print(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")