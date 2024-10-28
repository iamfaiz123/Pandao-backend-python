from uuid import UUID
from pydantic import BaseModel, Field
from typing_extensions import Optional, List
from enum import Enum


class ValueType(Enum):
    INT = "INT"
    DECIMAL = "DECIMAL"
    STRING = "STRING"


class CommunityGovernanceType(Enum):
    TokenWeight = 'TOKEN_WEIGHT'


class BluePrintTermsForm(BaseModel):
    term: str = Field(..., description="The heading  of the blueprint")
    description: str = Field(..., description="The description of the blueprint")


class BlurPrintForm(BaseModel):
    slug: str = Field(..., description="slug of the blue print", example='blue-print')
    description: str = Field(..., description="description of the blue print")
    price: float = Field(..., description="price of the blue print")
    package_address: str = Field(..., description="package address of the blue print")
    terms: List[BluePrintTermsForm]


class DeployCommunity(BaseModel):
    tx_id: str = Field(..., description="The transaction id of the deployed community")
    name: str = Field(..., description='the name of the community')
    description: str = Field(..., description='description of the community')
    CommunityGovernance: CommunityGovernanceType = Field(..., description='the community governance')
    user_address: str
