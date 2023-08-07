import os
import tempfile
import time
from unittest.mock import patch

import botocore
import pandas as pd
import pytest
import requests
from fastapi.testclient import TestClient

import ifuntrans.api.translate as translate
import ifuntrans.api.localization as localization
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

    s3_source_file = "ai-translate/source/test.xlsx"
    # upload sample file
    s3.upload_file(test_file, utils.S3_DEFAULT_BUCKET, s3_source_file)

    request = {
        "id": task_id,
        "type": "doc",
        "targetLan": "en,zh-TW",
        "translateSource": "test.xlsx",
    }
    response = client.post("/translate", json=request).json()
    response_model = translate.TranslationResponse(**response)
    assert response_model.code == 200

    # Mock background task
    file_key = utils.get_s3_key_from_id(task_id)

    localization.translate_s3_excel_task(
        task_id,
        s3_source_file,
        "en,zh-TW",
    )

    with tempfile.NamedTemporaryFile(suffix=".xlsx") as temp:
        s3.download_file(
            utils.S3_DEFAULT_BUCKET,
            file_key,
            temp.name,
        )

        df = pd.read_excel(temp.name)
        assert len(df.columns.tolist()) == 4
