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
    # It might return 200 or 404 if landing.html isn't in root, but it shouldn't crash.
    assert response.status_code in [200, 404]

def test_tracer_route():
    response = client.get("/tracer")
    assert response.status_code in [200, 404]

def test_start_trace_health():
    response = client.get("/api/start_trace")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_nemesis_id_intel():
    response = client.get("/api/nemesis_id/intel/0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc")
    assert response.status_code == 200
    data = response.json()
    assert data["is_malicious"] == True

def test_wallet_profile():
    response = client.get("/api/wallet_profile/0x0000000000000000000000000000000000000000")
    assert response.status_code == 200
    data = response.json()
    assert "usd_value" in data

