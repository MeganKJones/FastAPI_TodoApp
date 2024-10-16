from routers.auth import get_current_user, authenticate_user
from routers.auth import get_db
from routers.auth import create_access_token
from routers.auth import SECRET_KEY
from routers.auth import ALGORITHM
from .utils import *
from jose import jwt
from datetime import timedelta
import pytest
from fastapi import HTTPException


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_authenticate_user(test_user):
    db = TestingSessionLocal()

    authenticated_user = authenticate_user(test_user.username, "password", db)

    assert authenticated_user is not None
    assert authenticated_user.username == test_user.username

    non_existent_user = authenticate_user("not_a_user", "password", db)

    assert non_existent_user is False

    wrong_password_user = authenticate_user(test_user.username, "notmypassword", db)

    assert wrong_password_user is False



def test_create_access_token(test_user):
    db = TestingSessionLocal()

    username = "testusername"
    user_id = 1
    role = "user"
    expires_delta = timedelta(days=1)
    access_token = create_access_token(username, user_id, role, expires_delta)

    decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])

    assert decoded_token["sub"] == username
    assert decoded_token["role"] == role
    assert decoded_token["id"] == user_id



@pytest.mark.asyncio
async def test_get_current_user_valid_token(test_user):
    encode = {'sub': "testusername", 'role': "admin", 'id': 1}
    token = jwt.encode(encode, SECRET_KEY, ALGORITHM)

    user = await get_current_user(token=token)
    assert user == {'username': "testusername", 'user_role': "admin", 'id': 1}


@pytest.mark.asyncio
async def test_get_current_missing_payload(test_user):
    encode = {'role': "admin"}
    token = jwt.encode(encode, SECRET_KEY, ALGORITHM)

    with pytest.raises(HTTPException) as exception:
        await get_current_user(token=token)

    assert exception.value.status_code == 401
    assert exception.value.detail == "could not validate user."




