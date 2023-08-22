import datetime
import os
import tempfile

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import ifuntrans.api.translate as translate
import ifuntrans.utils as utils
from ifuntrans.api import create_app

test_file = os.path.join(os.path.dirname(__file__), "assets/small.xlsx")


@pytest.fixture(scope="module", autouse=True)
def client():
    app = create_app()
    yield TestClient(app)


@pytest.mark.parametrize("engine", ["google", "chatgpt"])
def test_translate(client, engine):
    request = {
        "type": "text",
        "engine": engine,
        "sourceLan": "auto",
        "targetLan": "en",
        "translateSource": "Bonjour le monde",
    }

    response = client.post("/translate", json=request).json()
    response_model = translate.TranslationResponse(**response)
    assert response_model.code == 200


@pytest.mark.asyncio
async def test_localization(client, mocker):
    task_id = 12345

    date_str = datetime.datetime.now().strftime("%Y%m%d")
    s3_source_file = f"ai-translate/source/{date_str}/_test.xlsx"

    async with utils.S3Client() as s3_client:
        # upload sample file
        await s3_client.upload_file(test_file, utils.S3_DEFAULT_BUCKET, s3_source_file)

        langs = "en,zh-TW"
        request = {
            "id": task_id,
            "type": "doc",
            "targetLan": langs,
            "translateSource": s3_source_file,
        }

        # from ifuntrans.api.localization import callback
        # mocker.patch.object(callback, "__call__", new_callable=mocker.AsyncMock, return_value=None)
        response = client.post("/translate", json=request).json()
        response_model = translate.TranslationResponse(**response)
        assert response_model.code == 200

        s3_target_file = f"ai-translate/target/{date_str}/{task_id}.xlsx"
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as temp:
            await s3_client.download_file(
                utils.S3_DEFAULT_BUCKET,
                s3_target_file,
                temp.name,
            )

            df = pd.read_excel(temp.name, sheet_name=None)
            # assert num sheet equals to target language + 1
            assert len(df) == len(langs.split(",")) + 1

        # delete file from s3
        await s3_client.delete_object(Bucket=utils.S3_DEFAULT_BUCKET, Key=s3_source_file)
        await s3_client.delete_object(Bucket=utils.S3_DEFAULT_BUCKET, Key=s3_target_file)
