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
    public_address: Mapped[str] = Column(String(256), primary_key=True)
    last_login: Mapped[DateTime] = Column(DateTime, default=func.now())
    usermetadata: Mapped["UserMetaData"] = relationship("UserMetaData", back_populates="user")
    created_at: Mapped[DateTime] = Column(DateTime, default=func.now())
    user_email = Column(String, nullable=False)  # Corrected type


class UserMetaData(Base):
    __tablename__ = 'user_meta_data'
    user_address: Mapped[str] = Column(String, ForeignKey('users.public_address'), primary_key=True)
    about: Mapped[str] = Column(String)
    image_url: Mapped[str] = Column(String)
    cover_url: Mapped[str] = Column(String)
    x_url: Mapped[str] = Column(String)
    linkedin: Mapped[str] = Column(String)
    website: Mapped[str] = Column(String)
    tiktok: Mapped[str] = Column(String)
    bio: Mapped[str] = Column(String)
    address: Mapped[str] = Column(String)
    user: Mapped["User"] = relationship("User", back_populates="usermetadata")

class UserEmailPreference(Base):
    __tablename__='user_email_preference'
    user_address: Mapped[str] = Column(String, ForeignKey('users.public_address'), primary_key=True)
    new_letters = Column(Boolean, nullable=True,default=True)
    community_notice = Column(Boolean, nullable=True, default=True)
    bond_notice = Column(Boolean, nullable=True, default=True)
    proposal_notice = Column(Boolean, nullable=True, default=True)


class UserEmailVerification(Base):
    __tablename__ = 'user_email_verification'
    user_email = Column(String, nullable=False, primary_key=True)  # Corrected type
    otp = Column(Integer, nullable=False)  # Corrected type
    expire_time = Column(DateTime, nullable=False)

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


class UserNotification(Base):
    __tablename__ = 'user_notification'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_read = Column(Boolean, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=True, primary_key=True)
    user_address:Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    title:Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    text:Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    image:Mapped[str] = mapped_column(String, nullable=True,primary_key=True)
    date: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)


from .engine import engine
Base.metadata.create_all(engine)