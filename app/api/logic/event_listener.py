import uuid
from datetime import datetime
from sqlite3 import IntegrityError

import requests
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from app.api.logic.community.community import generate_random_string
from app.api.logic.wallet import get_asset_details
from models import Community, dbsession as conn, UserActivity, CommunityToken, Proposal, Participants, CommunityTags, \
    ZeroCouponBond, AnnTokens, CommunityExpense, CommunityFunds, PendingTransactions, UserToProposalVote


## pending , add logger

def token_bucket_deploy_event_listener(tx_id: str, user_address: str):

        url = "https://babylon-stokenet-gateway.radixdlt.com/transaction/committed-details"
        data = {
            "intent_hash": tx_id,
            "receipt_events": True,
            "opt_ins": {
                "receipt_events": True
            }
        }

        # Send a POST request with the JSON dataxs

        response = requests.post(url, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            # create an empty dict to store data
            resources = {}
            metadata = {}
            # Parse the response JSON data
            response_data = response.json()
            # Print the response JSON data

            # Store the response data in a dictionary
            response_data = response_data
            tx_events = response_data['transaction']['receipt']['events']
            xrd_paid = float(response_data['transaction']['fee_paid'])
            # print(tx_events)
            community_tags = []
            for event in tx_events:
                if event['name'] == 'PandaoEvent':
                    for field in event['data']['fields']:
                        if field['field_name'] == 'meta_data':

                            for m_d in field['fields']:
                                for _m_d in m_d['fields']:

                                    if _m_d['field_name'] == 'tags':
                                        for tags in _m_d['elements']:
                                            community_tags.append(tags['value'])
                                    elif (_m_d['field_name'] == 'address_issued_bonds_to_sell' or
                                          _m_d['field_name'] == 'target_xrd_amount' or
                                          _m_d['field_name'] == 'proposal_creator_address'):

                                        metadata[_m_d['field_name']] = _m_d['fields'][0]['value']
                                    elif _m_d['field_name'] == 'amount_of_tokens_should_be_minted':
                                        pass
                                    elif _m_d['field_name'] == 'amount_of_tokens_should_be_minted':
                                        pass
                                    elif _m_d['field_name'] == 'proposal_creation_right':
                                        if _m_d['variant_name'] == 'TOKEN_HOLDER_THRESHOLD':
                                            metadata['minimum_token'] = _m_d['fields'][0]['value']
                                            pass
                                        else:
                                            metadata['minimum_token'] = 0
                                        metadata[_m_d['field_name']] = _m_d['variant_name']
                                    elif _m_d['field_name'] == 'token_type':
                                        metadata[_m_d['field_name']] = _m_d['variant_name']
                                    else:
                                        print(_m_d['field_name'])
                                        metadata[_m_d['field_name']] = _m_d['value']
                        else:
                            resources[field['field_name']] = field.get('value') or field.get('variant_name') or ''
            try:
                # check for all the events emitted from the blockchain , check event types
                if resources['event_type'] == 'DEPLOYMENT':
                    # create a new community
                    # store id for future purpose
                    community_id = uuid.uuid4()
                    # store community name as temp for further use
                    community_name = metadata['community_name']
                    # create new object for community to insert into table
                    community = Community(
                        id=community_id,
                        name=metadata['community_name'],
                        component_address=metadata['component_address'],
                        description=metadata['description'],
                        blueprint_slug=resources['dao_type'],
                        token_address=metadata['token_address'],
                        owner_token_address=metadata['owner_token_address'],
                        owner_address=user_address,
                        token_price=metadata['token_price'],
                        token_buy_back_price=metadata['token_buy_back_price'],
                        image=metadata['community_image'],
                        total_token=metadata['total_token'],
                        funds=0,
                        token_bought=0,
                        purpose=metadata['purpose'],
                        proposal_rights=metadata['proposal_creation_right'],
                        proposal_minimum_token=metadata['minimum_token']
                    )
                    # add created community object for batch insert state
                    conn.add(community)
                    # loop over the tags for community
                    for t in community_tags:
                        tag = CommunityTags(
                            community_id=community_id,
                            tag=t
                        )
                        conn.add(tag)
                    # create object for community participant
                    participant = Participants(
                        user_addr=user_address,
                        community_id=community_id,
                    )
                    conn.add(participant)

                    # create community create activity
                    activity = UserActivity(
                        transaction_id=tx_id,
                        transaction_info=f'created {community_name}',
                        user_address=user_address,
                        community_id=community_id,
                        activity_type='community_create'
                    )
                    conn.add(activity)

                    random_string = generate_random_string()
                    # add comment activity
                    participate_activity = UserActivity(
                        # since participating in community does not envole any blockchain effort , generate a random string for tx id
                        transaction_id=random_string,
                        transaction_info=f'participated in {community_name}',
                        user_address=user_address,
                        community_id=community_id ,
                        activity_type='participate'
                    )
                    conn.add(participate_activity)

                    # create a community expense object to insert into this data
                    community_expense = CommunityExpense(
                        community_id=community_id,
                        xrd_spent= -( xrd_paid ),
                        creator=user_address,
                        tx_hash=tx_id,
                        xrd_spent_on='This Community Creation',
                        date=datetime.now()  # You can omit this if you want to use the default value
                    )

                    conn.add(community_expense)
                    # finally commit
                    conn.commit()
                elif resources['event_type'] == 'TOKEN_BOUGHT':
                    # in case of token bought , get community details and add activity
                    community_address = resources['component_address']
                    # get community names and detail
                    community = conn.query(Community).filter(Community.component_address == community_address).first()
                    # current community funds at this given time
                    funds_added = float(metadata['amount_paid'])
                    # funds_added = float(metadata['amount_paid_faizal'])
                    current_community_funds = community.funds + float(metadata['amount_paid'])
                    community.funds = current_community_funds
                    community.token_bought += float(metadata['amount'])
                    token_bought = float(metadata['amount'])
                    current_time = datetime.now()
                    try:
                        # Attempt to retrieve the existing row
                        community_token = conn.query(CommunityToken).filter_by(
                            community_id=community.id,
                            user_address=user_address
                        ).one()
                        community_token.token_owned += float(token_bought)
                        conn.add(community_token)
                    except NoResultFound:
                        community_token = CommunityToken(
                            community_id=community.id,
                            user_address=user_address,
                            token_owned=float(token_bought)
                        )
                        conn.add(community_token)

                    activity = UserActivity(
                        transaction_id=tx_id,
                        transaction_info=f'bought {token_bought} tokens in {community.name}',
                        user_address=user_address,
                        community_id=community.id,
                        activity_type='token_bought'
                    )
                    conn.add(activity)

                    # create a community expense object to insert into this data
                    community_expense = CommunityExpense(
                        community_id=community.id,
                        # also add xrd send in this
                        xrd_spent= - (float(xrd_paid)+float(metadata['amount_paid'])),
                        creator=user_address,
                        tx_hash=tx_id,
                        xrd_spent_on='buy tokens in community',
                        date=current_time  # You can omit this if you want to use the default value
                    )
                    conn.add(community_expense)
                    # create a community funds chart
                    new_funds = CommunityFunds(
                        community_id=community.id,
                        xrd_added=funds_added,
                        current_xrd=current_community_funds,
                        creator=user_address,
                        tx_hash=tx_id,
                        date=current_time
                    )
                    conn.add(new_funds)
                    conn.commit()


                elif resources['event_type'] == 'TOKEN_SELL':
                    # in case of token bought , get community details and add activity
                    community_address = resources['component_address']
                    # get community names and detail
                    community = conn.query(Community).filter(Community.component_address == community_address).first()
                    funds_added = -(float(metadata['amount_paid']))
                    current_community_funds = community.funds - float(metadata['amount_paid'])
                    community.funds = current_community_funds
                    community.token_bought -= float(metadata['amount'])
                    token_bought = float(metadata['amount'])
                    current_time = datetime.now()
                    try:
                        # Attempt to retrieve the existing row
                        community_token = conn.query(CommunityToken).filter_by(
                            community_id=community.id,
                            user_address=user_address
                        ).one()
                        community_token.token_owned -= float(token_bought)
                        conn.add(community_token)
                    except NoResultFound:
                        pass
                    activity = UserActivity(
                        transaction_id=tx_id,
                        transaction_info=f'sold {token_bought} tokens in {community.name}',
                        user_address=user_address,
                        community_id=community.id,
                        activity_type='token_sold'
                    )
                    conn.add(activity)
                    community_expense = CommunityExpense(
                        community_id=community.id,
                        xrd_spent=  ( float(metadata['amount_paid']) - xrd_paid ),
                        creator=user_address,
                        tx_hash=tx_id,
                        xrd_spent_on='sold tokens in community',
                        date=current_time # You can omit this if you want to use the default value
                    )
                    conn.add(community_expense)
                    # create a community funds chart
                    new_funds = CommunityFunds(
                        community_id=community.id,
                        xrd_added=funds_added,
                        current_xrd=current_community_funds,
                        creator=user_address,
                        tx_hash=tx_id,
                        date=current_time  # You can omit this if you want to use the default value
                    )
                    conn.add(new_funds)
                    conn.commit()

                elif resources['event_type'] == 'PRAPOSAL':
                    community_address = resources['component_address']

                    # get community names and detail
                    community = conn.query(Community).filter(Community.component_address == community_address).first()
                    new_proposal = Proposal(
                        proposal=metadata['title'],
                        description=metadata['description'],
                        community_id=community.id,
                        voted_for=0,
                        voted_against=0,
                        is_active=True,
                        start_time=metadata['start_time_ts'],
                        ends_time=metadata['end_time_ts'],
                        minimum_quorum=metadata['minimum_quorum'],
                        proposal_address=metadata['component_address'],
                        proposal_id=metadata['proposal_id'],
                        creator=metadata['proposal_creator_address'],
                        result='' ,
                        zcb_bond_creator= metadata['address_issued_bonds_to_sell'],
                        proposal_vote_type = metadata['token_type'] ,
                        status = 1 ,
                        number_of_people_voted = 1
                    )
                    activity = UserActivity(
                        transaction_id=tx_id,
                        transaction_info=f'created a proposal',
                        user_address=user_address,
                        community_id=community.id,
                        activity_type='proposal_created'
                    )
                    conn.add(activity)
                    conn.add(new_proposal)
                    community_expense = CommunityExpense(
                        community_id=community.id,
                        xrd_spent=- ( xrd_paid ) ,
                        creator=user_address,
                        tx_hash=tx_id,
                        xrd_spent_on='created a proposal in community',
                        date=datetime.now() # You can omit this if you want to use the default value
                    )
                    conn.add(community_expense)
                    conn.commit()
                elif resources['event_type'] == 'VOTE':
                    ## take voter address from events
                    proposal_address = resources['component_address']
                    proposal_address = metadata['praposal_address']
                    proposal = conn.query(Proposal).filter(Proposal.proposal_address == proposal_address).first()
                    vote_against = metadata['againts']
                    if proposal.proposal_vote_type == 'Equality':
                        if vote_against:
                            proposal.voted_against += 1
                        else:
                            proposal.voted_for += 1
                    else:
                        if vote_against:
                            proposal.voted_against += float(metadata['voting_amount'])
                        else:
                            proposal.voted_for += float(metadata['voting_amount'])
                    if proposal.number_of_people_voted is None:
                        proposal.number_of_people_voted = 1
                    else:
                        proposal.number_of_people_voted += 1
                    user_proposal_vote = UserToProposalVote(
                        user_address = user_address,
                        proposal_id = proposal.id
                    )

                    conn.add( user_proposal_vote)
                    activity = UserActivity(
                        transaction_id=tx_id,
                        transaction_info=f'voted in a proposal',
                        user_address=user_address,
                        community_id=proposal.community_id,
                        activity_type='proposal_voted'
                    )
                    conn.add(activity)
                    community_expense = CommunityExpense(
                        community_id=proposal.community_id,
                        xrd_spent= - ( xrd_paid ),
                        creator=user_address,
                        tx_hash=tx_id,
                        xrd_spent_on='voted in a proposal',
                        date=datetime.now() # You can omit this if you want to use the default value
                    )
                    conn.add(community_expense)
                    conn.commit()
                elif resources['event_type'] == 'QUORUM_MET_AND_SUCCESS':
                    component_address = resources['component_address']
                    proposal_id = metadata['proposal_id']
                    community = conn.query(Community).filter(Community.component_address == component_address).first()
                    proposal = conn.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
                    zcb = conn.query(ZeroCouponBond).filter(
                        ZeroCouponBond.contract_identity == metadata['contract_identity']).first()

                    proposal.is_active = False
                    proposal.status = 0
                    zcb.amount_stored = zcb.price
                    zcb.has_accepted = True
                    proposal.result = f"executed successfully , number of people voted {metadata['number_of_voters']}. And bought {zcb.contract_identity}"
                    community.funds = community.funds - zcb.price
                    activity = UserActivity(
                        transaction_id=tx_id,
                        transaction_info=f'executed a proposal',
                        user_address=user_address,
                        community_id=proposal.community_id,
                        activity_type='proposal_executed'
                    )

                    community_expense = CommunityExpense(
                        community_id=proposal.community_id,
                        xrd_spent= - ( xrd_paid ),
                        creator=user_address,
                        tx_hash=tx_id,
                        xrd_spent_on='executed in a proposal',
                        date=datetime.now() # You can omit this if you want to use the default value
                    )

                    cf = CommunityFunds(
                            community_id = community.id,
                            xrd_added= - zcb.price,
                            current_xrd = community.funds ,
                            creator= user_address,
                            tx_hash= tx_id,
                            date=datetime.now() ,
                     )
                    conn.add(activity)
                    conn.add(cf)
                    conn.add(community_expense)
                    conn.commit()
                elif resources['event_type'] == 'ZERO_COUPON_BOND_CREATION':
                    community_address = resources['component_address']
                    # get community names and detail
                    asset_detail = get_asset_details(metadata['collateral_resource_address'])
                    community = conn.query(Community).filter(Community.component_address == community_address).first()
                    bond = (conn.query(ZeroCouponBond).filter(ZeroCouponBond.community_id == community.id)
                    .filter(
                        ZeroCouponBond.contract_identity == metadata['contract_identifier'])).first()
                    bond.contract_type = metadata['contract_type']
                    bond.contract_role = metadata['contract_role']
                    bond.contract_identity = metadata['contract_identifier']
                    bond.interest_rate = metadata['nominal_interest_rate']
                    bond.currency = metadata['currency']
                    bond.initial_exchange_date = datetime.fromtimestamp(int(metadata['initial_exchange_date']))
                    bond.maturity_date = datetime.fromtimestamp(int(metadata['maturity_date']))
                    bond.notional_principle = metadata['notional_principal']
                    bond.discount = metadata['discount']
                    bond.bond_position = metadata['bond_position']
                    bond.number_of_bonds = metadata['number_of_bonds']
                    bond.created_on_blockchain = True
                    bond.creator = metadata['creator_address']
                    bond.price = metadata['price']
                    bond.asset_address = asset_detail['resource_address']
                    bond.asset_url = asset_detail['icon_url']
                    bond.asset_name = asset_detail['name']
                    conn.add(bond)

                    community_expense = CommunityExpense(
                        community_id=community.id,
                        xrd_spent= - ( xrd_paid ),
                        creator=user_address,
                        tx_hash=tx_id,
                        xrd_spent_on='created a zero coupon bond',
                        date=datetime.now() # You can omit this if you want to use the default value
                    )
                    activity = UserActivity(
                        transaction_id=tx_id,
                        transaction_info=f'created a zero coupon bond',
                        user_address=user_address,
                        community_id=community.id,
                        activity_type='zero_coupon_bond_created'
                    )
                    conn.add(activity)
                    # create an activity for same
                    conn.add(community_expense)
                    conn.commit()

                elif resources['event_type'] == 'ANN_TOKEN_CREATION':
                    community_address = resources['component_address']
                    community = conn.query(Community).filter(Community.component_address == community_address).first()
                    ann = (conn.query(AnnTokens).filter(AnnTokens.community_id == community.id)
                    .filter(
                        AnnTokens.contract_identity == metadata['contract_identifier'])).first()

                    ann.contract_type = metadata['contract_type']
                    ann.contract_role = metadata['contract_role']
                    ann.contract_identity = metadata['contract_identifier']
                    ann.interest_rate = metadata['nominal_interest_rate']
                    ann.currency = metadata['currency']
                    ann.initial_exchange_date = datetime.fromtimestamp(int(metadata['initial_exchange_date']))
                    ann.maturity_date = datetime.fromtimestamp(int(metadata['maturity_date']))
                    ann.notional_principle = metadata['notional_principal']
                    ann.discount = metadata['discount']
                    ann.ann_position = metadata['annuity_position']
                    ann.number_of_ann_tokens = metadata['number_of_annuities_to_mint']
                    ann.created_on_blockchain = True
                    ann.creator = metadata['creator_address']
                    ann.price = metadata['price']
                    conn.add(ann)
                    community_expense = CommunityExpense(
                        community_id=community.id,
                        xrd_spent= - ( xrd_paid ),
                        creator=user_address,
                        tx_hash=tx_id,
                        xrd_spent_on='created an ANN token',
                        date=datetime.now() # You can omit this if you want to use the default value
                    )
                    conn.add(community_expense)
                    conn.commit()
                else:
                    pass
            except Exception as e:
                # in case of exceptions insert data in pending transactions table with error
                print(e)
                print('here we got execption')
                pending_transactions = PendingTransactions(
                        creator=user_address,
                        tx_hash=tx_id,
                        error='internal code error',
                        event_type=resources['event_type'],
                        date=datetime.now()  # You can also use func.now() if you want the database to handle the timestamp
                )
                try:
                    conn.add(pending_transactions)
                    conn.commit()
                except IntegrityError as ie:
                    # treate 504 as integratey error
                    raise HTTPException(status_code=504,
                                        detail="We get into some unrecoverable error , please keep your transactions-hash with you , and raise a complain in Pandao dashboard")
                except Exception as e:
                    raise HTTPException(status_code=500,
                                        detail="We get into some unrecoverable error , please keep your transactions-hash with you , and raise a complain in Pandao dashboard")
                # treat 503 as handled error
                raise HTTPException(status_code=503, detail="Seems like there are some internal errors , Don't worry we have record your transaction and it will be reelected once services are online")
            return resources

        else:
            print(f"Request failed with status code {response.status_code}")
    # except HTTPException as inner_block_error:
    #     print(inner_block_error.status_code)
    #     if inner_block_error.status_code != 504:
    #         raise HTTPException(status_code=500,
    #                             detail="Failing transaction , The transactions has been recorded already will get reelected in your community soon when the services goes online")
    #     if inner_block_error.status_code != 503:
    #         raise HTTPException(status_code=500,
    #                             detail="We get into some unrecoverable error , please keep your transactions-hash with you , and raise a complain in Pandao dashboard")
    #     raise HTTPException(status_code=503,
    #                         detail="Seems like there are some internal errors , Don't worry we have record your transaction and it will be reelected once services are online")
    # # this will catch all the errors from outer block
    # except Exception as e:
    #     print(e)
    #     pending_transactions = PendingTransactions(
    #         creator=user_address,
    #         tx_hash=tx_id,
    #         error="unknown error",
    #         event_type='Unknown',
    #         date=datetime.now()  # You can also use func.now() if you want the database to handle the timestamp
    #     )
    #     try:
    #         conn.add(pending_transactions)
    #         conn.commit()
    #     except Exception as e:
    #         print(e)
    #         raise HTTPException(status_code=500,
    #                             detail="We get into some unrecoverable error , please keep your transactions-hash with you and raise a complain in Pandao dashboard")
    #     raise HTTPException(status_code=500,
    #                         detail="Seems like there are some internal errors , Don't worry we have record your transaction and it will be reelected once services are online")


