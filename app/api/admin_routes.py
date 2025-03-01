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
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends, status
from pydantic import BaseModel

SECRET_KEY = "your-secret-key"  # Change to a strong secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expiration time

class Token(BaseModel):
    access_token: str
    token_type: str

from fastapi import APIRouter
from pydantic import BaseModel
class UserLogin(BaseModel):
    username: str
    password: str

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_current_user(token: str = Depends(verify_token)):
    # You can use the 'token' payload here to get user info and verify roles
    return token  # This is where you would extract user details from the payload
def admin_routes(app):
    @app.post('/admin/community/mark-featured', status_code=status.HTTP_201_CREATED,
              summary='admin marks a community as featured', tags=['admin routes'])
    def mark_community_as_featured(req: MarkCommunityAsFeatured, token: str = Depends(get_current_user)):
        # You can now use `token` to get user data or roles and check if the user is an admin
        return mark_community_as_feature(req.community_id, req.is_featured)

    @app.post('/admin/community/disable', status_code=status.HTTP_201_CREATED,
              summary='admin enable/disable a community', tags=['admin routes'])
    def mark_community_as_disabled(req: MarkCommunityAsDisable, token: str = Depends(get_current_user)):
        # Use `token` to check user roles if needed
        return disable_community(req.community_id, req.is_disable)


    @app.post("/token", response_model=Token,status_code=status.HTTP_201_CREATED,
              summary='admin login', tags=['admin routes'])
    def login_for_access_token(form_data: UserLogin):
        # Validate username and password (typically check against a database)
        if form_data.username == "admin" and form_data.password == "password":  # Example validation
            access_token = create_access_token(data={"sub": form_data.username})
            return {"access_token": access_token, "token_type": "bearer"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
