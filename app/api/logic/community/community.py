import uuid

import requests
from sqlalchemy import or_, select, func, desc, distinct
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.api.forms.blueprint import DeployCommunity
from app.api.forms.community import ProposalComment, CommunityDiscussionComment
from app.api.logic.external_apis.external_apis import get_price_conversion
# from app.api.forms.blueprint import DeployCommunity
from models import dbsession as conn, BluePrint, Community as Com, User, Participants, UserMetaData, \
    UserActivity, Community, CommunityToken, Proposal, ProposalComments, CommunityDiscussion, DiscussionComment, \
    CommunityTags, ZeroCouponBond, AnnTokens
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


def get_all_community_of_platform(sort: str):
    query = conn.query(Community, func.count(Participants.id).label('participants_count')) \
        .outerjoin(Participants, Community.id == Participants.community_id) \
        .group_by(Community.id)
    if sort == 'participants':
        query = query.order_by(func.count(Participants.id).desc())
    elif sort == 'funds':
        query = query.order_by(Community.funds.desc())
    elif sort == 'name':
        query = query.order_by(Community.name.asc())

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


class CommunityParticipant:
    pass


def user_participate_in_community(user_addr: str, community_id: uuid.UUID):
    try:
        # create new user participant
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
            community_id=community_id
        )
        conn.add(activity)
        conn.commit()
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


def get_community_participants(community_id: UUID):
    result = (
        conn.query(User.public_address, User.name, UserMetaData.image_url)
        .join(UserMetaData, User.public_address == UserMetaData.user_address)
        .join(Participants, Participants.user_addr == User.public_address)
        .filter(Participants.community_id == community_id)
        .all()
    )

    res = []
    for data in result:
        pa, un, dp = data
        res.append(
            {
                "participant": pa,
                "name": un,
                "image_url": dp,
            }
        )

    return res


def check_user_community_status(user_addr: str, community_id: uuid.UUID):
    try:
        user_data = conn.query(CommunityParticipant).filter(CommunityParticipant.community_id == community_id,
                                                            CommunityParticipant.participant == user_addr).first()
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

        raise HTTPException(status_code=400,
                            detail="Integrity error: possibly duplicate entry or foreign key constraint.")

    except SQLAlchemyError as e:
        conn.rollback()

        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        conn.rollback()

        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_community_comments(c_id: uuid.UUID):
    # Join the tables
    results = conn.query(CommunityDiscussion.created_at, CommunityDiscussion.id, CommunityDiscussion.title, User.name,
                         UserMetaData.image_url,
                         User.public_address).join(User,
                                                   CommunityDiscussion.created_by == User.public_address).join(
        UserMetaData, User.public_address == UserMetaData.user_address).filter(
        CommunityDiscussion.community_id == c_id).all()

    # Format the response
    comments = [
        {
            "title": row.title,
            "user_name": row.name,
            "user_image": row.image_url,
            "user_address": row.public_address,
            "id": row.id,
            "created_at": row.created_at
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
        "token_buy_back_price_in_usd": token_buy_back_price_in_usd

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
            community_id=discussion.community_id
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
            community_id=c_id
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
            user_address=proposal_data.community_id,
            community_id=req.user_addr
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


def get_community_all_proposal(community_id: uuid.UUID):
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


def get_community_all_zero_coupon_bonds(community_id: uuid.UUID):
    proposal = conn.query(ZeroCouponBond).filter(ZeroCouponBond.community_id == community_id).filter(ZeroCouponBond.created_on_blockchain == True).all()
    return proposal

def get_community_all_ann_tokens(community_id: uuid.UUID):
    ann = conn.query(AnnTokens).filter(AnnTokens.community_id == community_id).all()
    # .filter(AnnTokens.created_on_blockchain == True)
    return ann
