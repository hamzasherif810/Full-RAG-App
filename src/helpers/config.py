from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    # model_config is a reserved word

    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    MONGODB_URL: str
    MONGODB_DATABASE: str

    GENERATION_BACKEND: str = None
    EMBEDDING_BACKEND: str = None

    OPENAI_API_KEY: str = None
    OPENAI_BASE_URL: str = None
    COHERE_API_KEY: str = None

    GENERATION_MODEL_ID: str = None
    EMBEDDING_MODEL_ID: str = None
    EMBEDDING_MODEL_SIZE: int = None

    INPUT_DEFAULT_MAX_TOKENS: int
    GENERATION_DEFAULT_MAX_TOKENS = 200
    GENERATION_DEFAULT_TEMPERATURE = 0.1


def get_settings():
    return Settings()
