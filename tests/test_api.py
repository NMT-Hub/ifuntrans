import pytest

from ifuntrans.api import create_app
import ifuntrans.api.translate as translate


@pytest.fixture(scope="module", autouse=True))
def app():
    app = create_app()
    yield app


def test_translate(app):
    request = translate.TranslationRequest.get_example()

