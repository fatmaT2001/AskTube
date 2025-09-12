from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    DBNAME: str




    class Config:
        env_file = ".env"









def get_settings():
    return Settings()