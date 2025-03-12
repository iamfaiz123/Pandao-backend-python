import uuid
from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, Field
from typing_extensions import Optional, List
from enum import Enum


class TransactionSubmit(BaseModel):
    tx_id: str
    user_address: str


class DeployTokenWeightedDao(BaseModel):
    userAddress: str = Field(..., description="wallet address of user")
    communityName: str = Field(..., description="name of the community user want to create")
    tokenSupply: int = Field(..., description="token Supply")
    tokenPrice: float = Field(..., description="token price")
    tokenWithDrawPrice: float = Field(..., description="token withdraw price")
    communityImage: str = Field(..., description="community image")
    description: str = Field(..., description="description of community ")
    tokenImage: str = Field(..., description="token image")
    purpose: str = Field(..., description="purpose of community")
    tags: List[str] = Field(..., description="tags of the community")
    proposal_right: Optional[str] = Field(..., description="proposal right , ie who can create proposal")
    proposal_minimum_token: Optional[int] = Field(..., description="minimum number of token required for proposal "                                                        "creation")
    package_addr: str = Field(..., description="token image")
    community_token_name: str = Field(..., description="community_token_name")


class BuyTokenWeightedDaoToken(BaseModel):
    userAddress: str = Field(..., description="wallet address of user")
    # community_id: uuid = Field(..., description="id of the community user want buy token from")
    tokenSupply: int = Field(..., description="token Supply user want to buy")
    community_id: uuid.UUID = Field(..., description="community id")


class DeployProposal(BaseModel):
    community_id: uuid.UUID = Field(..., description="community id")
    minimumquorum: int = Field(..., description="minimum quorm for praposal")
    start_time: str = Field(..., description="start time of praposal")
    end_time: str = Field(..., description="end time of praposal")
    proposal: str = Field(..., description="proposal")
    userAddress: str = Field(..., description="user address")
    description: str = Field(..., description="description")
    vote_type: Optional[str] = Field(..., description="voting system of proposal")
    bond_issuer_address: Optional[str] = Field(None, description="voting system of proposal")
    desire_token_price:Optional[float] = Field(None,description="desire token price of user")
    desire_token_buy_back_price:Optional[float] = Field(None,description="desire token price of user")


class ProposalVote(BaseModel):
    proposal_address: str = Field(..., description="propsal address")
    userAddress: str = Field(..., description="user address")
    vote_against: bool = Field(..., description=" voted against")


class ExecuteProposal(BaseModel):
    proposal_id: int = Field(..., description="proposal id")
    proposal_address: str = Field(..., description="proposal address")


class ZeroCouponBond(BaseModel):
    community_id: uuid.UUID = Field(..., description="community id")
    bond_name: str
    bond_symbol: str
    bond_identity: str
    nominal_interest_rate: float
    currency: str = "xrd"  # Assuming this is a constant value
    initial_exchange_date: datetime
    maturity_date: datetime
    notional_principal: float
    discount: int
    bond_position: str
    bond_price: float
    number_of_bonds: float
    user_address: str
    description: str
    nft: str

class IssueAnnTokenRequest(BaseModel):
    contract_type: str
    contract_role: str
    contract_identity: str
    nominal_interest_rate: float
    initial_exchange_date: datetime
    maturity_date: datetime
    notional_principal: float
    ann_position: str
    price: float
    number_of_ann: float
    user_address: str
    community_id: uuid.UUID = Field(..., description="community id")
    name:str
    description: str

class WithDrawMoneyFromBond(BaseModel):
        bond_id: uuid.UUID = Field(..., description="community id")
        user_address: str


class AddMoneyInBond(BaseModel):
    bond_id: uuid.UUID = Field(..., description="community id")
    user_address: str
    xrd_to_add : float

class ClaimBond(BaseModel):
    bond_id: uuid.UUID = Field(..., description="bond id")
    community_id: uuid.UUID = Field(..., description="community id")

class MintExecutiveToken(BaseModel):
    user_address: str = Field(..., description="wallet address of user")
    community_id: uuid.UUID = Field(..., description="community id")
    name : str = Field(..., description="name of user")

class TransferExecutiveBadge(BaseModel):
    user_address: str = Field(..., description="wallet address of user")
    community_id: uuid.UUID = Field(..., description="community id")
    recipient: str = Field(..., description="wallet address of recipient")

class RequestTokenWithDraw(BaseModel):
    user_address: str = Field(..., description="wallet address of user")
    community_id: uuid.UUID = Field(..., description="community id")
    amount : float =  Field(..., description="amount to withdraw")

class SignWithDrawRequest(BaseModel):
    user_address: str = Field(..., description="wallet address of user")
    community_id: uuid.UUID = Field(..., description="community id")
    requested_addre : float =  Field(..., description="amount to withdraw")