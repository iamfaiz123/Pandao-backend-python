import uuid

from fastapi import FastAPI
from starlette import status

from .forms.blueprint import DeployCommunity
from .forms.community import CommunityParticipant, ProposalComment, CommunityDiscussion, CommunityDiscussionComment
from .forms.transaction_manifest import TransactionSubmit
# from .forms.blueprint import DeployCommunity
from .logic import health as health_handler
from .logic.activity.user_activity import get_user_activity, UserActivityModel, get_community_activity
from .logic.auth.users import user_login_req, user_sign_up, check_user_exist, get_user_detail, update_user_profile, \
    delete_user, get_pending_transactions, get_user_created_bonds
from .logic.blueprint import add_blueprint as add_blueprint_logic
from .forms import *
from .logic.blueprint.blueprint import get_all_blueprints, get_blueprint

from .logic.community import get_community
from .logic.community.community import create_community, get_user_community, check_user_community_status, \
    user_participate_in_community, get_community_participants, get_community_comments, add_community_comment, \
    get_single_community, get_community_metadata_details, get_community_tokens, get_community_active_proposal, \
    get_proposal_comment, add_proposal_comment, add_community_discussion_comment, get_discussion_comments, \
    get_user_communities, get_all_community_of_platform, get_community_tags, get_community_all_proposal, \
    get_community_all_zero_coupon_bonds, get_community_all_ann_tokens, get_bonds_name, community_funds_history, \
    get_user_expense
from .logic.event_listener import token_bucket_deploy_event_listener
from .logic.health import pre_define_data
from .logic.tags import get_all_tags_query
from .logic.wallet import get_user_wallet_nfts
from .utils.presignsignature import generate_signature


def load_server(app):
    # defines routes

    @app.delete('/delete/user')
    def delete_user_route(user_addr: str):
        return delete_user(user_addr)

    @app.post('/run/predefine-query', tags=["system-apis"], description='add predefine data')
    def run_predefine_query():
        pre_define_data()

    @app.get('/')
    def health_check():
        return health_handler()

    # define public apis here
    @app.get('/tags', tags=(['TAGS']), description="get all tags from the platform")
    def get_all_tags():
        return get_all_tags_query()

    @app.get("/image-upload/signature", tags=(['presign-url']))
    def get_image_upload_signature_route():
        return generate_signature()

    # api for user to register
    @app.post('/user/signup', status_code=status.HTTP_201_CREATED, tags=(['user-auth']))
    def user_signup_route(req: UserSignupForm):
        return user_sign_up(req)

    @app.get('/user/activity', status_code=status.HTTP_201_CREATED, tags=(['user-auth']))
    def get_user_activity_route(user_address: str, page: int = 1, page_size: int = 10):
        return get_user_activity(user_address, page, page_size)

    @app.get('/user/check-signup/{public_address}', status_code=status.HTTP_200_OK, tags=(['user-auth']))
    def user_check_signup_route(public_address: str):
        return check_user_exist(public_address)

    @app.get('/user/details/{public_address}', status_code=status.HTTP_200_OK, tags=(['user-detail']))
    def get_user_details_route(public_address: str):
        return get_user_detail(public_address)

    @app.patch('/user/update-user', status_code=status.HTTP_200_OK, tags=(['user-detail']))
    def update_user_route(req: UserProfileUpdate):
        return update_user_profile(req)

    @app.post('/user/login', status_code=status.HTTP_201_CREATED, tags=(['user-auth']))
    def register(req: UserLogin):
        return user_login_req(req)

    # get_user_communities

    @app.get('/user/community/{public_address}', status_code=status.HTTP_200_OK, tags=(['user-detail']))
    def get_user_all_communities(public_address: str, owner: bool):
        return get_user_communities(public_address, owner)

    @app.get('/user/expense/{public_address}', status_code=status.HTTP_200_OK, tags=(['user-detail']))
    def get_user_all_expense_route(public_address: str):
        return get_user_expense(public_address)

    @app.get('/user/created-bonds/{public_address}', status_code=status.HTTP_200_OK, tags=(['user-detail']))
    def get_user_all_created_bonds_route(public_address: str):
        return get_user_created_bonds(public_address)

    @app.get('/user/pending-transactions/{public_address}', status_code=status.HTTP_200_OK, tags=(['user-detail']))
    def get_user_all_pending_transaction_route(public_address: str):
        return get_pending_transactions(public_address)

    # define routes for blueprints

    @app.post('/blueprint', summary="add a blueprint ", description="add blue print by admin", tags=(['blue-print']))
    def add_blueprint_route(req: BlurPrintForm):
        add_blueprint_logic(req)

    @app.get('/blueprint', summary="get all blueprint on the platform", tags=(['blue-print']))
    def get_all_blueprint_route():
        return get_all_blueprints()

    @app.get('/blueprint/{slug}', summary="get a blueprint detail on the platform", tags=(['blue-print']))
    def get_all_blueprint_route(slug: str):
        return get_blueprint(slug)

    @app.get('/community', summary="get communities of the platform ", description="get communities of platform",
             tags=(['community']))
    def get_community_route(sort: str = 'participants'):
        return get_all_community_of_platform(sort)

    @app.get('/community/all', summary="get all community of platform", description="get_all_community_of_platform",
             tags=(['community']))
    def get_all_communities(sort: str = 'participants'):
        return get_all_community_of_platform(sort)

    @app.get('/community/{user_addr}', summary="get communities of user ",
             description="get communities of user", tags=(['community']))
    def get_community_user_route(user_addr: str):
        return get_user_community(user_addr)

    # community_funds_history

    # @app.post('/community/deploy', summary="send this to server after deploying a community",
    #           description="send this to server after deploying a community")
    # def deploy_token_weighted_dao(req:DeployCommunity):
    #     return create_community(req)
    @app.post('/submit-tx', summary="submits a transaction on the platform",
              description="submits a transaction on the platform")
    def callme(req: TransactionSubmit):
        return token_bucket_deploy_event_listener(req.tx_id, req.user_address)

    ## routes related to activity
    @app.get('/activity/{community_id}', summary='get all the activity on the platform',
             description="get all the activity on the platform", tags=(['user-activity ']))
    def get_activity_route(community_id: uuid.UUID):
        return get_community_activity(community_id)

    @app.get('/community/check/user_status', summary="check if user is participant of community", tags=(['community']))
    def check_user_community_status_route(user_addr: str, community_id: uuid.UUID):
        return check_user_community_status(user_addr, community_id)

    # @app.get('/community/{user_addr}', summary="get communities of the platform ",
    #          description="get communities of platform")
    # def get_community_user_route(user_addr: str):
    #     return get_user_community(user_addr)

    @app.post('/community/participant', summary="user join a community", tags=(['community']))
    def join_community(req: CommunityParticipant):
        return user_participate_in_community(req.participant_address, req.community_id)

    @app.get('/community/participant/{c_id}', summary="user join a community", tags=(['community']))
    def get_community_participant_route(c_id: uuid.UUID):
        return get_community_participants(c_id)

    @app.get('/community/funds-history/{c_id}', summary="get funds history of a community", tags=(['community']))
    def get_community_funds_history_route(c_id: uuid.UUID):
        return community_funds_history(c_id)

    @app.get('/community/tags/{c_id}', summary="get tags of the community", tags=(['community']))
    def get_community_participant_route(c_id: uuid.UUID):
        return get_community_tags(c_id)

    @app.get('/community/discussion/{c_id}', summary="get discussions of user community", tags=(['community']))
    def get_discussion_route(c_id: uuid.UUID):
        return get_community_comments(c_id)

    @app.post('/community/discussion', summary='start a new discussion in community', tags=(['community']))
    def add_community_discussion_route(req: CommunityDiscussion):
        return add_community_comment(req)

    @app.get('/community/detail/{c_id}', summary="get community detail", tags=(['community']))
    def get_community_detail_route(c_id: uuid.UUID):
        return get_single_community(c_id)

    @app.get('/community/detail/metadata/{c_id}', summary="get community detail", tags=(['community']))
    def get_community_metadata_route(c_id: uuid.UUID):
        return get_community_metadata_details(c_id)

    @app.get('/community/token/{c_id}', summary="get community tokens holder details", tags=(['community']))
    def get_community_token_route(c_id: uuid.UUID):
        return get_community_tokens(c_id)

    @app.get('/community/proposal/active/{c_id}', summary="get community active proposal", tags=(['community']))
    def get_community_token_route(c_id: uuid.UUID):
        return get_community_active_proposal(c_id)

    @app.get('/community/proposal/all/{c_id}', summary="get community active proposal", tags=(['community']))
    def get_community_token_route(c_id: uuid.UUID):
        return get_community_all_proposal(c_id)

    @app.get('/community/zcb/all/{c_id}', summary="get community ero_coupon_bonds", tags=(['community']))
    def get_community_zero_coupon_bonds(c_id: uuid.UUID):
        return get_community_all_zero_coupon_bonds(c_id)

    @app.get('/community/ann/all/{c_id}', summary="get community anns tokens", tags=(['community']))
    def get_community_all_ann_tokens_routes(c_id: uuid.UUID):
        return get_community_all_ann_tokens(c_id)

    @app.get('/community/bonds-names/all/{c_id}', summary="get all bonds names in community", tags=(['community']))
    def get_community_all_bond_names_routes(c_id: uuid.UUID):
        return get_bonds_name(c_id)

    @app.get('/community/proposal/comments/{proposal_id}', summary="get proposal comments", tags=(['community']))
    def get_community_proposal_comment(proposal_id: uuid.UUID):
        return get_proposal_comment(proposal_id)

    @app.post('/community/proposal/comments', summary="add proposal comment", tags=(['community']))
    def get_community_proposal_comment(req: ProposalComment):
        return add_proposal_comment(req)



    @app.post('/community/discussion/comments', summary="add comment in community discussion", tags=(['community']))
    def get_community_discussion_comment(req: CommunityDiscussionComment):
        return add_community_discussion_comment(req)

    @app.get('/community/discussion/comments/{discussion_id}', summary="get community discussion comments",
             tags=(['community']))
    def get_community_proposal_comment(discussion_id: uuid.UUID):
        return get_discussion_comments(discussion_id)

    @app.get('/users/wallets/assets/{user_address}', summary="get all assets from users wallet",
             tags=(['User wallet']))
    def get_user_wallet_asset(user_address: str):
        return get_user_wallet_nfts(user_address)