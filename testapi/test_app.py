from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_read_root():
    reponse = client.get("/")
    assert reponse.status_code == 200
    assert reponse.json() == {"message": "Hello, World!"}

