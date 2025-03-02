from uuid import UUID
from pydantic import BaseModel, Field
from typing_extensions import Optional, List
from enum import Enum


class MarkCommunityAsFeatured(BaseModel):
    community_id: UUID = Field(..., description="The UUID of the community.")
    is_featured: bool = Field(..., description="True to mark as featured, False to un feature.")

class MarkCommunityAsDisable(BaseModel):
    community_id: UUID = Field(..., description="The UUID of the community.")
    is_disable: bool = Field(..., description="True to mark as disable, False to enable.")\

class AdminLogin(BaseModel):
    email: str = Field('admin@pandao.live', description="The email of the admin.")
    password: str = Field('pandao@123', description="The password of the admin.")


class UpdateCommunityFunctions(BaseModel):
    community_id: UUID = Field(..., description="The UUID of the community.")
    token_buy_enable: bool = Field(False, description="Enable or disable token buying.")
    proposal_create_enable: bool = Field(False, description="Enable or disable proposal creation.")
    is_participation_enabled: bool = Field(False, description="Enable or disable participation.")
    bond_creation_enable: bool = Field(False, description="Enable or disable bond creation.")
    discussion_creation_enable: bool = Field(False, description="Enable or disable discussion creation.")