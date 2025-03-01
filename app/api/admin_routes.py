from datetime import datetime

from fastapi import HTTPException

from app.api.forms.admin_forms import MarkCommunityAsFeatured, MarkCommunityAsDisable, AdminLogin

from app.api.logic.admin.community import mark_community_as_feature, disable_community
from config.config import config
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends, status
from pydantic import BaseModel

SECRET_KEY = config.get('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

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
    return token





def admin_routes(app):
    @app.post('/admin/community/mark-featured', status_code=status.HTTP_201_CREATED,
              summary='admin marks a community as featured', tags=['admin routes'])
    def mark_community_as_featured(req: MarkCommunityAsFeatured):
        return mark_community_as_feature(req.community_id, req.is_featured)

    @app.post('/admin/community/disable', status_code=status.HTTP_201_CREATED,
              summary='admin enable/disable a community', tags=['admin routes'])
    def mark_community_as_disabled(req: MarkCommunityAsDisable):
        return disable_community(req.community_id, req.is_disable)


    @app.post("/token", response_model=Token,status_code=status.HTTP_201_CREATED,
              summary='admin login', tags=['admin routes'])
    def login_for_access_token(form_data: AdminLogin):
        # Validate username and password (typically check against a database)
        if form_data.email == "admin@pandao.live" and form_data.password == "pandao@123":  # Example validation
            access_token = create_access_token(data={"sub": form_data.email})
            return {"access_token": access_token, "token_type": "bearer"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
