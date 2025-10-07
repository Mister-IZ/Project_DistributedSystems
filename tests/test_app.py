import pytest
from app.app import app # Flask app importée depuis app/app.py

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    """Vérifie que la page d'accueil répond correctement"""
    response = client.get('/')
    assert response.status_code == 200
