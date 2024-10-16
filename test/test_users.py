from routers.users import get_current_user
from routers.users import get_db
from .utils import *
from fastapi import status


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_return_user(test_user):
    response = client.get("/user")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]['username'] == "megjones"
    assert response.json()[0]['email'] == "megjones@email"
    assert response.json()[0]['id'] == 1
    assert response.json()[0]['first_name'] == "Meg"
    assert response.json()[0]['last_name'] == "Jones"
    assert response.json()[0]['role'] == "admin"
    assert response.json()[0]['phone_number'] == "07947298572"


def test_change_password_success(test_user):
    response = client.put("/user/password", json={"password": "password", "new_password": "new_password"})
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_change_password_invalid_current_password(test_user):
    response = client.put("/user/password", json={"password": "notmypassword", "new_password": "new_password"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Error with password change.'

def test_change_phones_number_success(test_user):
    response = client.put("/user/phone_number/07948297485")
    assert response.status_code == status.HTTP_204_NO_CONTENT