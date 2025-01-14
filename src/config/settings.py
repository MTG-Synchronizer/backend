from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin.auth import verify_id_token

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        case_sensitive=False,
    )

    SERVER_HOST: str
    NEO4J_SERVICE: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    TAG: str
    FRONTEND_URL: str

@lru_cache()
def get_settings() -> Settings:
    # Use lru_cache to avoid loading .env file for every request
    config = Settings()
    return config


bearer_scheme = HTTPBearer(auto_error=False)
def get_firebase_user_from_token(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
) -> dict | None:
    """Uses bearer token to identify firebase user id
    Args:
        token : the bearer token. Can be None as we set auto_error to False
    Returns:
        dict: the firebase user on success
    Raises:
        HTTPException 401 if user does not exist or token is invalid
    """

    try:
        if not token:
            # raise and catch to return 401, only needed because fastapi returns 403
            # by default instead of 401 so we set auto_error to False
            raise ValueError("No token")
        user = verify_id_token(token.credentials)
        return user
    # lots of possible exceptions, see firebase_admin.auth,
    # but most of the time it is a credentials issue
    except Exception:
        # we also set the header
        # see https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in or Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
