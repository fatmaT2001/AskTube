from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    DBNAME: str

    # YouTube settings
    YOUTUBE_API_KEY: str
    PREFERRED_LANGS: list[str]
    CHUNK_DURATION:int

    # Pinecone settings
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str
    PINECONE_EMBEDDING_MODEL: str
    PINECONE_RERANKING_MODEL: str
    PINECONE_HOST_URL:str


    # Other settings
    VECTOR_DB_PROVIDER:str




    class Config:
        env_file = ".env"









def get_settings():
    return Settings()