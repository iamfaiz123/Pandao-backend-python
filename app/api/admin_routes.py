from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from starlette import status

from app.api.forms.admin_forms import MarkCommunityAsFeatured, MarkCommunityAsDisable
from app.api.forms.transaction_manifest import DeployTokenWeightedDao, BuyTokenWeightedDaoToken, DeployProposal, \
    ProposalVote, ExecuteProposal, ZeroCouponBond, IssueAnnTokenRequest, WithDrawMoneyFromBond, AddMoneyInBond, \
    ClaimBond, MintExecutiveToken, TransferExecutiveBadge
from app.api.logic.admin.community import mark_community_as_feature, disable_community
from models import Community, Participants, Proposal, CommunityToken, ZeroCouponBond as ZcpModel, AnnTokens
from models import dbsession as conn


def admin_routes(app):
    @app.post('/admin/community/mark-featured',status_code=status.HTTP_201_CREATED, summary='admin marks a community as featured',tags=(['admin routes']))
    def mark_community_as_featured(req: MarkCommunityAsFeatured):
        return mark_community_as_feature(req.community_id,req.is_featured)

    @app.post('/admin/community/disable',status_code=status.HTTP_201_CREATED, summary='admin enable/disable a community',tags=(['admin routes']))
    def mark_community_as_featured(req: MarkCommunityAsDisable):
        return disable_community(req.community_id,req.is_disable)
