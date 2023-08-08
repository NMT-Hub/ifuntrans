import datetime
import os
import tempfile
from unittest.mock import patch

import pandas as pd
import pytest
import requests
from fastapi.testclient import TestClient

import ifuntrans.api.translate as translate
import ifuntrans.utils as utils
from ifuntrans.api import create_app

test_file = os.path.join(os.path.dirname(__file__), "assets/small.xlsx")


@pytest.fixture(scope="module", autouse=True)
def client():
    app = create_app()
    yield TestClient(app)


def test_translate(client):
    request = {
        "type": "text",
        "engine": "google",
        "sourceLan": "auto",
        "targetLan": "en",
        "translateSource": "Bonjour le monde",
    }

    response = client.post("/translate", json=request).json()
    response_model = translate.TranslationResponse(**response)
    assert response_model.code == 200


@patch.object(requests, "post")
def test_microsoft_successful_post_mock(mock_request_post):
    returned_json = {
        "code": 200,
        "message": "success",
    }

    def res():
        r = requests.Response()

        def json_func():
            return returned_json

        r.json = json_func
        return r

    mock_request_post.return_value = res()


def test_localization(client):
    task_id = "test_id"
    s3 = utils.get_s3_client()

    date_str = datetime.datetime.now().strftime("%Y%m%d")
    s3_source_file = f"ai-translate/source/{date_str}/_test.xlsx"
    # upload sample file
    s3.upload_file(test_file, utils.S3_DEFAULT_BUCKET, s3_source_file)

    langs = "en,zh-TW"
    request = {
        "id": task_id,
        "type": "doc",
        "targetLan": langs,
        "translateSource": s3_source_file,
    }
    response = client.post("/translate", json=request).json()
    response_model = translate.TranslationResponse(**response)
    assert response_model.code == 200

    s3_target_file = f"ai-translate/target/{date_str}/{task_id}.xlsx"
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as temp:
        s3.download_file(
            utils.S3_DEFAULT_BUCKET,
            s3_target_file,
            temp.name,
        )

        df = pd.read_excel(temp.name, sheet_name=None)
        # assert num sheet equals to target language + 1
        assert len(df) == len(langs.split(",")) + 1

    # delete file from s3
    s3.delete_object(Bucket=utils.S3_DEFAULT_BUCKET, Key=s3_source_file)
    s3.delete_object(Bucket=utils.S3_DEFAULT_BUCKET, Key=s3_target_file)
