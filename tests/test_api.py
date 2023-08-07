import pytest
from fastapi.testclient import TestClient

import ifuntrans.api.translate as translate
from ifuntrans.api import create_app


@pytest.fixture(scope="module", autouse=True)
def client():
    app = create_app()
    yield TestClient(app)


def test_translate(client):
    request = translate.TranslationRequest.get_example()
    response = client.post("/translate", json=request).json()
    translate.TranslationResponse(**response)


def test_localization(client):
    pass
