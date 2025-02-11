from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.api.forms.transaction_manifest import DeployTokenWeightedDao, BuyTokenWeightedDaoToken, DeployProposal, \
    ProposalVote, ExecuteProposal, ZeroCouponBond, IssueAnnTokenRequest, WithDrawMoneyFromBond, AddMoneyInBond, \
    ClaimBond, MintExecutiveToken
from models import Community, Participants, Proposal, CommunityToken, ZeroCouponBond as ZcpModel, AnnTokens
from models import dbsession as conn


#
def transaction_manifest_routes(app):
    @app.post('/manifest/build/deploy_token_weighted_dao', tags=(['manifest_builder']))
    def build_token_weight_deploy_manifest(req: DeployTokenWeightedDao):
        organization_name = req.communityName
        token_supply = req.tokenSupply
        token_price = req.tokenPrice
        token_withdraw_price = req.tokenWithDrawPrice
        proposal_right = ""
        if req.proposal_right == 'EveryOne':
            proposal_right = 'Enum<0u8>()'
        if req.proposal_right == 'Admin':
            proposal_right = 'Enum<2u8>()'
        if req.proposal_right == 'TokenHolder':
            proposal_right = f'Enum<1u8>(Decimal("{req.proposal_minimum_token}"))'

        if token_withdraw_price > token_price:
            error_message = {
                "error": "token buy back price can never be lower then token price",
                "message": "token buy back price can never be lower then token price"
            }
            raise HTTPException(status_code=400, detail=error_message)
        organization_image = req.communityImage
        organization_token_image = req.tokenImage
        description = req.description
        user_account = req.userAddress
        purpose = req.purpose
        # create tags
        if req.tags is None:
            raise HTTPException(status_code=400, detail="tags are required while creating a community")
        tags_array = f'Array<String>(\n'
        tags_array += ",\n".join(f'    "{tag}"' for tag in req.tags)
        tags_array += "\n)"

        manifest  = (
            f'CALL_FUNCTION\n'
            f'Address("{req.package_addr}")\n'
            f'"TokenWeigtedDao"\n'
            f'"initiate"\n'
            f'"{organization_name}"\n'
            f'{token_supply}i32\n'
            f'0u8\n'
            f'Decimal("{token_price}")\n'
            f'Decimal("{token_withdraw_price}")\n'
            f'"{organization_image}"\n'
            f'"{organization_token_image}"\n'
            f'"{description}"\n'
            f'{tags_array}\n'
            f'"{purpose}"\n'
            f'{proposal_right}'
            f'"{req.community_token_name}"'
            f';\n'
            f'CALL_METHOD\n'
            f'    Address("{user_account}")\n'
            f'    "deposit_batch"\n'
            f'    Expression("ENTIRE_WORKTOP")\n'
            f';'
        )
        return manifest

    @app.post('/manifest/build/buy_token/token_weighted_dao', tags=(['manifest_builder']))
    def buy_token_token_weighted_dao(req: BuyTokenWeightedDaoToken):
        try:
            community = conn.query(Community).filter(Community.id == req.community_id).first()
            account_address = req.userAddress
            XRD_take = req.tokenSupply * community.token_price + 1
            community_address = community.component_address
            token_take = req.tokenSupply
            does_user_exist = conn.query(Participants).filter(Participants.community_id == community.id,
                                                              Participants.user_addr == account_address).first()
            if not does_user_exist:
                raise HTTPException(status_code=401, detail="not a community participant")

            transaction_string = f"""
        CALL_METHOD
            Address("{account_address}")
            "withdraw"
            Address("resource_tdx_2_1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxtfd2jc")
            Decimal("{XRD_take}")
        ;

        TAKE_FROM_WORKTOP
            Address("resource_tdx_2_1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxtfd2jc")
            Decimal("{XRD_take}")
            Bucket("bucket1")
        ;

        CALL_METHOD
        Address("{community_address}")
        "obtain_community_token"
        Bucket("bucket1")
        Decimal("{token_take}")
        Address("{account_address}")
        ;

        CALL_METHOD
            Address("{account_address}")
            "deposit_batch"
            Expression("ENTIRE_WORKTOP")
        ;
        """
            return transaction_string

        except SQLAlchemyError as e:
            # Log the error e
            print(e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @app.post('/manifest/build/sell_token/token_weighted_dao', tags=(['manifest_builder']))
    def sell_token_token_weighted_dao(req: BuyTokenWeightedDaoToken):
        try:
            community = conn.query(Community).filter(Community.id == req.community_id).first()
            account_address = req.userAddress
            XRD_take = req.tokenSupply
            community_address = community.component_address
            token_address = community.token_address
            token_take = req.tokenSupply

            transaction_string = f"""
           CALL_METHOD
               Address("{account_address}")
               "withdraw"
               Address("{token_address}")
               Decimal("{XRD_take}")
           ;

           TAKE_FROM_WORKTOP
               Address("{token_address}")
               Decimal("{XRD_take}")
               Bucket("bucket1")
           ;

           CALL_METHOD
               Address("{community_address}")
               "withdraw_power"
               Bucket("bucket1")
           ;

           CALL_METHOD
               Address("{account_address}")
               "deposit_batch"
               Expression("ENTIRE_WORKTOP")
           ;
           """
            return transaction_string

        except SQLAlchemyError as e:
            # Log the error e
            print(e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @app.post('/manifest/build/praposal', tags=(['manifest_builder']))
    def build_proposal(req: DeployProposal):
        try:
            community = conn.query(Community).filter(Community.id == req.community_id).first()
            user_token = conn.query(CommunityToken).filter(CommunityToken.community_id == community.id,
                                                           CommunityToken.user_address == req.userAddress).first()
            proposal_right = community.proposal_rights
            token_amount = 1
            token_address = community.token_address
            if proposal_right == 'TOKEN_HOLDER_THRESHOLD':
                token_amount = community.proposal_minimum_token
                if user_token is None:
                    error_message = {
                        "error": f"user does not hold minimum token to create proposal , at least {community.proposal_minimum_token} token required",
                        "message": f"user does not hold minimum token to create proposal , at least {community.proposal_minimum_token} token required"
                    }
                    raise HTTPException(status_code=400, detail=error_message)
                elif user_token.token_owned < community.proposal_minimum_token:
                    error_message = {
                        "error": f"user does not hold minimum token to create proposal , at least {community.proposal_minimum_token} token required",
                        "message": f"user does not hold minimum token to create proposal , at least {community.proposal_minimum_token} token required"
                    }
                    raise HTTPException(status_code=400, detail=error_message)

            if proposal_right == 'ADMIN':
                token_address = community.owner_token_address
                if community.owner_address != req.userAddress:
                    error_message = {
                        "error": f"only admins can create proposal in this community",
                        "message": f"only admins can create proposal in this community",
                    }
                    raise HTTPException(status_code=400, detail=error_message)
            vote_type = ""

            if req.vote_type == 'Equality':
                vote_type = 'Enum<1u8>()'
            if req.vote_type == 'ResourceOwned':
                vote_type = 'Enum<0u8>()'

            start_time = req.start_time
            end_time = req.end_time
            account_address = req.userAddress
            end_time_unix = int(end_time)  # Convert string to integer Unix timestamp
            end_time_dt = datetime.utcfromtimestamp(end_time_unix)

            # Extract year, month, day, hour, minute, second
            end_year = end_time_dt.year
            end_month = end_time_dt.month
            end_day = end_time_dt.day
            end_hour = end_time_dt.hour
            end_minute = end_time_dt.minute
            end_second = end_time_dt.second

            start_time_unix = int(start_time)  # Convert string to integer Unix timestamp
            start_time_dt = datetime.utcfromtimestamp(start_time_unix)

            # Extract year, month, day, hour, minute, second
            start_year = start_time_dt.year
            start_month = start_time_dt.month
            start_day = start_time_dt.day
            start_hour = start_time_dt.hour
            start_minute = start_time_dt.minute
            start_second = start_time_dt.second

            transaction_string = f"""
               CALL_METHOD
               Address("{req.userAddress}")
               "withdraw"
                Address("{token_address}")
                Decimal("{token_amount}")
        ;
        
               TAKE_FROM_WORKTOP
               Address("{token_address}")
               Decimal("{token_amount}")
               Bucket("bucket1")
        ;
                                    CALL_METHOD
                                    Address("{community.component_address}")
                                    "create_praposal"
                                    "{req.proposal}"
                                    "{req.description}"
                                    {req.minimumquorum}u8
                                    Tuple(
                                    {start_year}u32 ,
                                    {start_month}u8 ,
                                    {start_day}u8 ,
                                    {start_hour}u8 ,
                                    {start_minute}u8 ,
                                    {start_second}u8)
                                    Tuple(
                                    {end_year}u32 ,
                                    {end_month}u8 ,
                                    {end_day}u8 ,
                                    {end_hour}u8 ,
                                    {end_minute}u8 ,
                                    {end_second}u8)
                                    Enum<1u8>(
                                    Address("{req.bond_issuer_address}"))
                                    Enum<1u8>(
                                    Decimal("40")
                                    )Enum<1u8>(
                                    Address("{account_address}")
                                    )
                                    Bucket("bucket1")
                                    {vote_type}

                                    ;
                                    
                                CALL_METHOD
                                       Address("{req.userAddress}")
    "try_deposit_batch_or_refund"
    Expression("ENTIRE_WORKTOP")
    Enum<0u8>()
;
            """
            return transaction_string

        except SQLAlchemyError as e:
            # Log the error e
            print(e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @app.post('/manifest/proposal/vote', tags=(['manifest_builder']))
    def vote_in_proposal(req: ProposalVote):
        proposal = conn.query(Proposal).filter(Proposal.proposal_address == req.proposal_address).first()
        community_id = proposal.community_id
        community = conn.query(Community).filter(Community.id == community_id).first()
        user_token = conn.query(CommunityToken).filter(CommunityToken.community_id == community_id,
                                                       CommunityToken.user_address == req.userAddress).first()
        if user_token is None:
            error_message = {
                "error": "does not hold any token",
                "message": "Please buy some token first before voting"
            }
            raise HTTPException(status_code=400, detail=error_message)
        token_supply = user_token.token_owned
        vote_against = "true" if req.vote_against else "false"
        transaction_string = f"""
        CALL_METHOD
            Address("{req.userAddress}")
            "withdraw"
            Address("{community.token_address}")
            Decimal("{token_supply}")
        ;
        
        TAKE_FROM_WORKTOP
            Address("{community.token_address}")
            Decimal("{token_supply}")
            Bucket("bucket1")
        ;


        CALL_METHOD
            Address("{community.component_address}")
            "vote"
            Bucket("bucket1")
            {vote_against}
            Address("{req.userAddress}")
            {proposal.proposal_id}u64
        
        ;

        CALL_METHOD
            Address("{req.userAddress}")
            "deposit_batch"
            Expression("ENTIRE_WORKTOP")
        ;
        """
        return transaction_string

    @app.post('/manifest/proposal/execute', tags=(['manifest_builder']))
    def vote_in_proposal(req: ExecuteProposal):
        proposal = conn.query(Proposal).filter(Proposal.proposal_address == req.proposal_address).first()
        community_id = proposal.community_id
        community = conn.query(Community).filter(Community.id == community_id).first()
        method = ""
        if proposal.proposal_type == 'buy_bond':
            method = 'execute_proposal'
        else:
            method = 'execute_proposal_to_change_token_price'

        transaction_string = f"""
               CALL_METHOD
               Address("{community.component_address}")
               "{method}"
               {proposal.proposal_id}u64
            ;
        """
        return transaction_string

    @app.post('/manifest/zero-coupon-bond', tags=(['manifest_builder']))
    def create_zero_coupon_bond(req: ZeroCouponBond):
        community = conn.query(Community).filter(Community.id == req.community_id).first()
        if community is not None:
            zcb = ZcpModel(
                community_id=req.community_id,
                name=req.bond_name,
                description=req.description,
                created_on_blockchain=False,
                contract_identity=req.bond_identity,
                asset_address=req.nft,
                has_accepted=False
            )
            conn.add(zcb)
            conn.commit()
        asset_address = req.nft
        transaction_string = f"""
                CALL_METHOD
                             Address("{req.user_address}")
                             "withdraw"
                             Address("{asset_address}")
                             Decimal("1")
                ;
                TAKE_FROM_WORKTOP
                             Address("{asset_address}")
                             Decimal("1")
                             Bucket("bucket1")
                ;
               CALL_METHOD
                            Address("{community.component_address}")
                            "create_zero_coupon_bond"
                            "{req.bond_name}"
                            "{req.bond_symbol}"
                            "{req.bond_identity}"
                            Decimal("{req.nominal_interest_rate}")
                            "xrd"
                            {int(req.initial_exchange_date.timestamp())}u64
                            {int(req.maturity_date.timestamp())}u64
                            Decimal("{req.notional_principal}")
                            {req.discount}u64
                            "{req.bond_position}"
                            {int(req.bond_price)}u64
                            Decimal("{req.number_of_bonds}")
                            Address("{req.user_address}")
                            Bucket("bucket1")
            ; 
        """
        return transaction_string

    @app.post('/manifest/create-ann', tags=(['manifest_builder']))
    def create_zero_coupon_bond(req:   IssueAnnTokenRequest):
        community = conn.query(Community).filter(Community.id == req.community_id).first()
        if community is not None:
            ann = AnnTokens(
                community_id=req.community_id,
                name=req.name,
                description=req.description,
                created_on_blockchain=False,
                contract_identity=req.contract_identity
            )
            conn.add(ann)
            conn.commit()
        transaction_string = f"""
                CALL_METHOD
                Address("{community.component_address}")
                "issue_ann_token"
                "{req.contract_type}"
                "{req.contract_role}"
                "{req.contract_identity}"
                Decimal("{req.nominal_interest_rate}")
                "xrd"
                {int(req.initial_exchange_date.timestamp())}u64
                {int(req.maturity_date.timestamp())}u64
                Decimal("{req.notional_principal}")
                "{req.ann_position}"
                Decimal("{req.price}")
                Decimal("{req.number_of_ann}")
                Address("{req.user_address}")
                ;
            """
        return transaction_string


    @app.post('/manifest/zcb/withdraw-all')
    def take_money_from_zcb(req: WithDrawMoneyFromBond):
        zcb = conn.query(ZcpModel).filter(ZcpModel.id == req.bond_id).first()
        if zcb is None:
            raise HTTPException(status_code=401, detail='invalid bond id')

        community = conn.query(Community).filter(Community.id == zcb.community_id).first()
        user_address = req.user_address
        transaction_string = f"""
        CALL_METHOD
            Address("{community.component_address}")
            "take_out_the_invested_XRDs_by_the_community"
            Address("{user_address}")
        ;

        CALL_METHOD
            Address("{user_address}")
            "deposit_batch"
            Expression("ENTIRE_WORKTOP")
        ;
        """
        return transaction_string

    @app.post('/manifest/zcb/add-xrds')
    def add_money_money_zcb(req: AddMoneyInBond):
            zcb = conn.query(ZcpModel).filter(ZcpModel.id == req.bond_id).first()
            if zcb is None:
                raise HTTPException(status_code=401, detail='invalid bond id')

            community = conn.query(Community).filter(Community.id == zcb.community_id).first()
            user_address = req.user_address
            transaction_string = f"""
                         CALL_METHOD
                         Address("{user_address}")
                         "withdraw"
                         Address("resource_tdx_2_1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxtfd2jc")
                         Decimal("{req.xrd_to_add}")
            ;
            
             TAKE_FROM_WORKTOP
                         Address("resource_tdx_2_1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxtfd2jc")
                         Decimal("{req.xrd_to_add}")
                         Bucket("bucket1")
            ;
            
            CALL_METHOD
            Address("{community.component_address}")
            "put_in_money_plus_interest_for_the_community_to_redeem"
            Address("{user_address}")
            Bucket("bucket1")
            ;
            
             CALL_METHOD
                         Address("{user_address}")
                         "deposit_batch"
                         Expression("ENTIRE_WORKTOP")
            ;
            """
            return transaction_string

        # get community component address
    @app.post('/manifest/zcb/claim')
    def add_money_money_zcb(req: ClaimBond):
        community = conn.query(Community).filter(Community.id == req.community_id).first()
        zcb = conn.query(ZcpModel).filter(ZcpModel.id == req.bond_id).first()
        transaction_string = f"""
                        CALL_METHOD
                        Address("{community.component_address}")
                        "claim_the_invested_XRDs_plus_interest"
                        Address("{zcb.creator}")
                    ;
                    """
        return transaction_string

    @app.post('/manifest/proposal/update-token-price')
    def create_token_price_change_proposal(req:DeployProposal):
        community = conn.query(Community).filter(Community.id == req.community_id).first()
        start_time = req.start_time
        end_time = req.end_time
        account_address = req.userAddress
        end_time_unix = int(end_time)  # Convert string to integer Unix timestamp
        end_time_dt = datetime.utcfromtimestamp(end_time_unix)

        # Extract year, month, day, hour, minute, second
        end_year = end_time_dt.year
        end_month = end_time_dt.month
        end_day = end_time_dt.day
        end_hour = end_time_dt.hour
        end_minute = end_time_dt.minute
        end_second = end_time_dt.second

        start_time_unix = int(start_time)  # Convert string to integer Unix timestamp
        start_time_dt = datetime.utcfromtimestamp(start_time_unix)

        # Extract year, month, day, hour, minute, second
        start_year = start_time_dt.year
        start_month = start_time_dt.month
        start_day = start_time_dt.day
        start_hour = start_time_dt.hour
        start_minute = start_time_dt.minute
        start_second = start_time_dt.second
        transaction_string = f"""
            CALL_METHOD
                Address("{req.userAddress}")
                "withdraw"
                Address("{community.token_address}")
                Decimal("1")
            ;

            TAKE_FROM_WORKTOP
                Address("{community.token_address}")
                Decimal("1")
                Bucket("bucket1")
            ;

            CALL_METHOD
                Address("{community.component_address}")
                "create_proposal_to_change_token_price"
                "{req.proposal}"
                "{req.description}"
                1u8
                Tuple(
                    {start_year}u32,
                    {start_month}u8,
                    {start_day}u8,
                    {start_hour}u8,
                    {start_minute}u8,
                    {start_second}u8
                )
                Tuple(
                    {end_year}u32,
                    {end_month}u8,
                    {end_day}u8,
                    {end_hour}u8,
                    {end_minute}u8,
                    {end_second}u8
                )
                Enum<1u8>(
                    Address("{req.userAddress}")
                )
                Bucket("bucket1")
                Enum<1u8>()
                Enum<1u8>(
                    Decimal("{req.desire_token_price}")
                )
                Enum<1u8>(
                    Decimal("{req.desire_token_buy_back_price}")
                )
            ;

            CALL_METHOD
                Address("{req.userAddress}")
                "try_deposit_batch_or_refund"
                Expression("ENTIRE_WORKTOP")
                Enum<0u8>()
            ;
        """

        return transaction_string


    @app.post('/mint/executive-token')
    def mint_executive_badge(req: MintExecutiveToken):
        community = conn.query(Community).filter(Community.id == req.community_id).first()
        zcb = conn.query(ZcpModel).filter(ZcpModel.id == req.bond_id).first()
        transaction_string = f"""
                       CALL_METHOD
                            Address("{community.component_address}")
                            "mint_executive_badge"
                            "Abdul Ahmed"
                            1u64
                            ;
                        CALL_METHOD
                            Address("{req.user_address}")
                            deposit_batch"
                            Expression("ENTIRE_WORKTOP")
                            ;
                    
                    """
        return transaction_string

