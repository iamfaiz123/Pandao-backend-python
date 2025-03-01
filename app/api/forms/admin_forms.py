from uuid import UUID
from pydantic import BaseModel, Field
from typing_extensions import Optional, List
from enum import Enum


class MarkCommunityAsFeatured(BaseModel):
    community_id: UUID = Field(..., description="The UUID of the community.")
    is_featured: bool = Field(..., description="True to mark as featured, False to un feature.")

class MarkCommunityAsDisable(BaseModel):
    community_id: UUID = Field(..., description="The UUID of the community.")
    is_disable: bool = Field(..., description="True to mark as disable, False to enable.")