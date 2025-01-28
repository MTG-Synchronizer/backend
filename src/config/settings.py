from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,  # Disable .env file
        extra="allow",
        case_sensitive=False,
    )

    SERVER_HOST: str
    NEO4J_SERVICE: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    TAG: str
    FRONTEND_URL: str
    ALLOW_ORIGINS: str

@lru_cache()
def get_settings() -> Settings:
    # Use lru_cache to avoid loading .env file for every request
    return Settings()


bearer_scheme = HTTPBearer(auto_error=False)
def get_firebase_user_from_token(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
) -> dict | None:
    """Uses bearer token to identify Firebase user ID."""

    try:
        if not token:
            raise ValueError("No token")

        # ✅ Check if credentials are loaded
        user = auth.verify_id_token(token.credentials)
        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in or Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
