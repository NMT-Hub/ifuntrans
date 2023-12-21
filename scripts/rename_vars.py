import os
import sys
from typing import List

import openai
from loguru import logger

if os.environ.get("USE_GPT4", None):
    AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_GPT4_ENDPOINT"]
    AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_GPT4_API_KEY"]
    DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID_GPT4"]
    logger.info("Use GPT4")
else:
    AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
    AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
    DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID"]
    logger.info("Use GPT3.5")

# OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# openai.api_key = os.environ["OPENAI_API_KEY"]

openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = "2023-05-15"


def rename_vars(vars: List[str]) -> List[str]:
    system_prompt = """
    I'd like to rename these variables with a different proximity. Please help me do that. Don't do any explanation, just rename them and output the new names.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "IsNotUsed\nUpdateNeeds\nNeed\nInitializeWatch"},
        {
            "role": "assistant",
            "content": "IsUnused\nUpdateRequires\nRequires\nCreateWatch",
        },
        {"role": "user", "content": "\n".join(vars)},
    ]

    results = []
    while len(results) != len(vars):
        chat_completion_resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            timeout=30,
            deployment_id=DEPLOYMENT_ID,
            temperature=1.0,
        )
        response = chat_completion_resp.choices[0].message.content

        results = response.split("\n")
        logger.info("retrying...")

    return results


# iter stdin
max_num = 10
vars = []
for line in sys.stdin:
    line = line.strip()
    if len(vars) >= max_num:
        results = rename_vars(vars)
        for result in results:
            print(result)
        vars = []
    vars.append(line)

if len(vars) > 0:
    results = rename_vars(vars)
    for result in results:
        print(result)
    vars = []
