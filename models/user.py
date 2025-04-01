from idlelib.pyparse import trans

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Enum, DECIMAL, Float, \
    func, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, sessionmaker, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import Mapped
from .engine import Base




from .engine import engine
Base.metadata.create_all(engine)