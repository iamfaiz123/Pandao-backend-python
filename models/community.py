from idlelib.pyparse import trans

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Enum, DECIMAL, Float, \
    func, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, sessionmaker, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import Mapped
from .engine import Base

class UserActivity(Base):
    __tablename__ = 'user_activity'
    transaction_id: Mapped[str] = Column(String, primary_key=True)
    # this contains a basic info about a user transaction in the DAO
    transaction_info: Mapped[str] = Column(String)
    activity_type: Mapped[str] = Column(String)
    community_id = Column(UUID(as_uuid=True))
    user_address: Mapped[str] = Column(String, ForeignKey('users.public_address'))
    created_at: Mapped[DateTime] = Column(DateTime, default=func.now())


class BluePrint(Base):
    __tablename__ = 'blueprint'
    slug: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(DECIMAL)
    package_addr = Column(String, nullable=False)
    # define relationships
    terms: Mapped[list["BluePrintTerms"]] = relationship("BluePrintTerms", back_populates="blueprint")


class BluePrintTerms(Base):
    __tablename__ = 'blueprint_terms'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    blueprint_slug: Mapped[str] = mapped_column(ForeignKey("blueprint.slug"))
    blueprint: Mapped["BluePrint"] = relationship("BluePrint", back_populates="terms")


class Community(Base):
    __tablename__ = 'community'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(128))
    component_address = Column(String(2048), unique=True)
    description = Column(String)
    blueprint_slug = Column(String)  #: Mapped[str] = mapped_column(ForeignKey("blueprint.slug"))
    token_address = Column(String)
    owner_token_address = Column(String)
    image = Column(String)
    token_image = Column(String)
    token_price = Column(Float)  # Assuming token price is stored as a float
    token_buy_back_price = Column(Float)  # Assuming buy-back price is stored as a float
    total_token = Column(Integer)
    token_bought = Column(Integer)
    owner_address = Column(String)  # = Column(String, ForeignKey('users.public_address'))
    funds = Column(Float)
    purpose = Column(String)
    # proposal rights tells about who can create a proposal in Pandao/community
    proposal_rights = Column(String)
    proposal_minimum_token = Column(Integer)
    executive_badge_address = Column(String)
    is_featured = Column(Boolean,default=False)
    is_disabled_by_admin = Column(Boolean,default=False)

class CommunityTags(Base):
    __tablename__ = 'community_tags'
    community_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    tag: Mapped[str] = Column(String, nullable=False)
    __table_args__ = (PrimaryKeyConstraint('community_id', 'tag'),)


class ProposalComments(Base):
    __tablename__ = 'proposal_comments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    proposal_id: Mapped[UUID] = mapped_column(ForeignKey('proposal.id'))
    comment = Column(String)
    user_id = Column(String, ForeignKey('users.public_address'))
    timestamp: Mapped[DateTime] = Column(DateTime, default=func.now())


class Participants(Base):
    __tablename__ = 'participants'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id = Column(UUID(as_uuid=True), ForeignKey('community.id'))
    user_addr = Column(String, ForeignKey('users.public_address'))


class CommunityToken(Base):
    __tablename__ = 'community_token'
    community_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_address = Column(String, ForeignKey('users.public_address'), primary_key=True)
    token_owned = Column(Float)


class CommunityDiscussion(Base):
    __tablename__ = 'community_discussions'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"))
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.public_address"))
    created_at: Mapped[DateTime] = Column(DateTime, default=func.now())
    title: Mapped[str] = mapped_column(String)
    # community: Mapped["Community"] = relationship("Community", back_populates="community_discussions")


class DiscussionComment(Base):
    __tablename__ = 'discussion_comments'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discussion_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community_discussions.id"))
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.public_address"))
    created_at: Mapped[DateTime] = Column(DateTime, default=func.now())
    comment: Mapped[str] = mapped_column(String)
    image: Mapped[str] = mapped_column(String)


class Proposal(Base):
    __tablename__ = 'proposal'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"))
    voted_for = Column(Float)
    voted_against = Column(Float)
    is_active = Column(Boolean)
    start_time = Column(Integer)
    ends_time = Column(Integer)
    minimum_quorum = Column(Integer)
    proposal_address: Mapped[str] = mapped_column(String)
    proposal_id = Column(Integer)
    creator: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(String)
    number_of_people_voted = Column(Integer)
    zcb_bond_creator: Mapped[str] = mapped_column(String)
    proposal_vote_type: Mapped[str] = mapped_column(String)
    status = Column(Integer)
    proposed_token_price = Column(Float)
    proposed_token_buy_back_price = Column(Float)
    proposal_type: Mapped[str] = mapped_column(String)

class UserToProposalVote(Base):
    __tablename__ = "user_to_proposal_vote"
    user_address: Mapped[str] = mapped_column(String, ForeignKey("users.public_address"), primary_key=True)
    proposal_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

class ZeroCouponBond(Base):
    __tablename__ = 'zero_coupon_bond'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=True)
    created_at: Mapped[DateTime] = Column(DateTime, default=func.now(), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    symbol: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    creator: Mapped[str] = mapped_column(String, ForeignKey("users.public_address"),nullable=True)
    bond_price = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    contract_type: Mapped[str] = mapped_column(String, nullable=True)
    contract_role: Mapped[str] = mapped_column(String, nullable=True)
    contract_identity: Mapped[str] = mapped_column(String, nullable=True)
    currency: Mapped[str] = mapped_column(String, nullable=True)
    initial_exchange_date: Mapped[DateTime] = Column(DateTime, nullable=True)
    maturity_date: Mapped[DateTime] = Column(DateTime, nullable=True)
    notional_principle = Column(Float, nullable=True)
    discount = Column(Integer, nullable=True)
    bond_position: Mapped[str] = mapped_column(String, nullable=True)
    price = Column(Float, nullable=True)
    number_of_bonds = Column(Float, nullable=True)
    created_on_blockchain = Column(Boolean, nullable=True)
    asset_address:  Mapped[str] = mapped_column(String, nullable=True)
    asset_url:  Mapped[str] = mapped_column(String, nullable=True)
    asset_name:  Mapped[str] = mapped_column(String, nullable=True)
    amount_stored = Column(Float, nullable=True)
    has_accepted = Column(Boolean, nullable=True)
    has_withdrawn = Column(Boolean, nullable=True)
    amount_own = Column(Float, nullable=True)
    claimed = Column(Boolean, nullable=True)

class AnnTokens(Base):
    __tablename__ = 'ann_tokens'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=True)
    created_at: Mapped[DateTime] = Column(DateTime, default=func.now(), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    symbol: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    creator: Mapped[str] = mapped_column(String, nullable=True)
    ann_price = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    contract_type: Mapped[str] = mapped_column(String, nullable=True)
    contract_role: Mapped[str] = mapped_column(String, nullable=True)
    contract_identity: Mapped[str] = mapped_column(String, nullable=True)
    currency: Mapped[str] = mapped_column(String, nullable=True)
    initial_exchange_date: Mapped[DateTime] = Column(DateTime, nullable=True)
    maturity_date: Mapped[DateTime] = Column(DateTime, nullable=True)
    notional_principle = Column(Float, nullable=True)
    discount = Column(Integer, nullable=True)
    ann_position: Mapped[str] = mapped_column(String, nullable=True)
    price = Column(Float, nullable=True)
    number_of_ann_tokens = Column(Float, nullable=True)
    created_on_blockchain = Column(Boolean, nullable=True)


class CommunityExpense(Base):
    __tablename__ = 'community_expense'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True) , default=uuid.uuid4)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=False)
    xrd_spent_transactions: Mapped[float] = mapped_column(Float, nullable=False)
    xrd_spend_on_asset: Mapped[float] = mapped_column(Float, nullable=True)
    creator: Mapped[str] = mapped_column(String, nullable=True)
    tx_hash: Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    xrd_spent_on: Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    date: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)


class CommunityFunds(Base):
    __tablename__ = 'community_funds'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True) , default=uuid.uuid4)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=False)
    xrd_added: Mapped[float] = mapped_column(Float, nullable=False)
    current_xrd: Mapped[float] = mapped_column(Float, nullable=False)
    creator: Mapped[str] = mapped_column(String, nullable=True)
    tx_hash: Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    date: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)

class PendingTransactions(Base):
    __tablename__ = 'pending_transactions'
    creator: Mapped[str] = mapped_column(String, nullable=True)
    tx_hash: Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    error : Mapped[str] = mapped_column(String, nullable=True)
    event_type:Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)

## alter table in new release
class CommunityNotice(Base):
    __tablename__ = 'community_notice'
    creator: Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    date: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)
    notice:Mapped[str] = mapped_column(String, nullable=True)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=False)


class CommunityExecutiveBadge(Base):
    __tablename__ = 'community_executive_badge'
    holder_address: Mapped[str] = mapped_column(String, primary_key=True)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=False, primary_key=True)

class CommunityFunctions(Base):
    __tablename__ = 'community_functions'
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=False,primary_key=True)
    token_buy_enable = Column(Boolean, nullable=True,default=True)
    proposal_create_enable = Column(Boolean, nullable=True, default=True)
    is_participation_enabled = Column(Boolean, nullable=True, default=True)
    bond_creation_enable = Column(Boolean, nullable=True, default=True)
    discussion_creation_enable = Column(Boolean, nullable=True, default=True)

class TokenWithDrawRequest(Base):
    __tablename__ = 'token_withdraw_request'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=False)
    user_address:Mapped[str] = mapped_column(String, ForeignKey("users.public_address"),nullable=True)
    amount_to_withdraw = Column(Float, nullable=False)
    request_date = Column(DateTime, default=func.now(), nullable=False)
    status = Column(Boolean, nullable=False)

class TokenWithDrawExecutiveSignStatus(Base):
    __tablename__ = 'token_withdraw_executive_sign_status'
    signed_by:Mapped[str] = mapped_column(String, ForeignKey("users.public_address"),nullable=True)
    signed_date = Column(DateTime, default=func.now(), nullable=False)
    req_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


from .engine import engine
Base.metadata.create_all(engine)

