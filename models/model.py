from idlelib.pyparse import trans

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Enum, DECIMAL, Float, \
    func, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, sessionmaker, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import Mapped
from .engine import Base


class User(Base):
    __tablename__ = 'users'
    name: Mapped[str] = Column(String)
    # user public address represents the user unique id
    public_address: Mapped[str] = Column(String(256), primary_key=True)
    last_login: Mapped[DateTime] = Column(DateTime, default=func.now())
    usermetadata: Mapped["UserMetaData"] = relationship("UserMetaData", back_populates="user")


class UserMetaData(Base):
    __tablename__ = 'user_meta_data'
    user_address: Mapped[str] = Column(String, ForeignKey('users.public_address'), primary_key=True)
    # about is a detail version about user details
    about: Mapped[str] = Column(String)
    image_url: Mapped[str] = Column(String)
    cover_url: Mapped[str] = Column(String)
    x_url: Mapped[str] = Column(String)
    linkedin: Mapped[str] = Column(String)
    website: Mapped[str] = Column(String)
    tiktok: Mapped[str] = Column(String)
    # bio is short description about user detail
    bio: Mapped[str] = Column(String)
    address: Mapped[str] = Column(String)
    user: Mapped["User"] = relationship("User", back_populates="usermetadata")


class UserWork(Base):
    __tablename__ = 'user_work'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_address: Mapped[str] = Column(String, ForeignKey('users.public_address'))
    company: Mapped[str] = Column(String, nullable=False)
    from_date: Mapped[DateTime] = Column(DateTime)
    to_date: Mapped[DateTime] = Column(DateTime)
    designation: Mapped[str] = Column(String, nullable=False)
    description: Mapped[str] = Column(String, nullable=False)


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)


class UserPreference(Base):
    __tablename__ = 'user_preference'
    user_address: Mapped[str] = Column(String, ForeignKey('users.public_address'))
    tag: Mapped[str] = Column(String, nullable=False)
    __table_args__ = (PrimaryKeyConstraint('user_address', 'tag'),)


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
    # community_comment: Mapped[list['CommunityDiscussion']] = relationship("CommunityDiscussion",
    # back_populates="community")


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

class ZeroCouponBond(Base):
    __tablename__ = 'zero_coupon_bond'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=True)
    community_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community.id"), nullable=True)
    created_at: Mapped[DateTime] = Column(DateTime, default=func.now(), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    symbol: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    creator: Mapped[str] = mapped_column(String, nullable=True)
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


class Blog(Base):
    __tablename__ = 'blogs'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description: Mapped[str] = mapped_column(String)
    thumbnail_image = Column(String, nullable=True)
    created_at: Mapped[DateTime] = Column(DateTime, default=func.now())
    published_by = Column(String, nullable=False)
    url = Column(String, nullable=False)


from .engine import engine

Base.metadata.create_all(engine)
