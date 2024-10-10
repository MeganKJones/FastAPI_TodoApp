from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from .auth import get_current_user
from pydantic import BaseModel
from pydantic import Field
from models import Users

router = APIRouter(prefix="/user", tags=["user"])

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class UserRequest(BaseModel):
    password: str
    new_password: str = Field(min_length=6)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed.")

    return db.query(Users).filter(Users.id == user.get('id')).all()

@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(db: db_dependency, user: user_dependency, user_request: UserRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed.")

    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if not bcrypt_context.verify(user_request.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail="Error with password change.")

    user_model.hashed_password = bcrypt_context.hash(user_request.new_password)

    db.add(user_model)
    db.commit()

@router.put("/phone_number/{phone_number}", status_code=status.HTTP_204_NO_CONTENT)
async def update_phone_number(db: db_dependency, user: user_dependency, phone_number: str):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed.")

    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found.")


    user_model.phone_number = phone_number

    db.add(user_model)
    db.commit()