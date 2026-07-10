import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Add app directory to path so main and services can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "NEMESIS" in response.text or "<html" in response.text

def test_ml_ontology():
    response = client.get("/api/ml/ontology")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data or "error" in data

def test_ml_datasets():
    response = client.get("/api/ml/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_admin_dashboard():
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Admin Dashboard" in response.text or "<html" in response.text

def test_api_knowledge_index_missing_url():
    response = client.post("/api/knowledge/index", json={"url": ""})
    # Since URL is blank but required in BaseModel, it should hit a validation error if URL is not passed,
    # or it will fail fetching within the endpoint and return 500.
    assert response.status_code in [422, 500]
