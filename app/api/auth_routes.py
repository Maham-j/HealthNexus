from fastapi import APIRouter, HTTPException, status

from app.models.auth_schemas import LoginRequest, TokenResponse
from app.core.auth import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(data={"sub": request.username})
    return {"access_token": token, "token_type": "bearer"}
