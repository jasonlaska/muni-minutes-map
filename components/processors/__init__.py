import os

ENV_OPENAI_KEY = "OPENAI_KEY"


def get_openai_key():
    if ENV_OPENAI_KEY not in os.environ or not os.environ[ENV_OPENAI_KEY]:
        raise ValueError("OPENAI_KEY env var not set")

    return os.environ[ENV_OPENAI_KEY]
