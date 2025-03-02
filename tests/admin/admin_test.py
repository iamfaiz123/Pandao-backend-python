import os

import pytest
from fastapi.testclient import TestClient
from main import app


os.environ['DATABASE_URL'] = 'postgresql://pandao:PqrGnFjwI00oBEgdL1nN2LDu2Egn6e9H@dpg-cuvv67aj1k6c738afd60-a.oregon-postgres.render.com/pandao_ncxa'
client = TestClient(app)
client.base_url = 'http://127.0.0.1:8000'
def test_login_for_access_token():
    response = client.post("/token", json={"email": "admin@pandao.live", "password": "pandao@123"})
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "Bearer"

def test_mark_community_as_featured():
    token_response = client.post("/token", json={"email": "admin@pandao.live", "password": "pandao@123"})
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/admin/community/mark-featured", json={"community_id": "some-uuid", "is_featured": True}, headers=headers)
    assert response.status_code == 201

def test_mark_community_as_disabled():
    token_response = client.post("/token", json={"email": "admin@pandao.live", "password": "pandao@123"})
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/admin/community/disable", json={"community_id": "some-uuid", "is_disable": True}, headers=headers)
    assert response.status_code == 201

def test_get_community_config():
    token_response = client.post("/token", json={"email": "admin@pandao.live", "password": "pandao@123"})
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/admin/community/config", params={"community_id": "some-uuid"}, headers=headers)
    assert response.status_code == 200

def test_update_community_config():
    token_response = client.post("/token", json={"email": "admin@pandao.live", "password": "pandao@123"})
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/admin/community/config", json={"community_id": "some-uuid", "new_config": "some-config"}, headers=headers)
    assert response.status_code == 201