from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import create_access_token, validate_password
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=schemas.UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    if not payload.username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required",
        )

    if not payload.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )

    if not payload.email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required",
        )

    validate_password(payload.password)

    try:
        user = crud.create_user(db, payload)
        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/verify-otp",
    response_model=schemas.TokenResponse,
)
def verify_otp(
    payload: schemas.VerifyOTP,
    db: Session = Depends(get_db),
):
    """Verify OTP and return access token."""

    try:
        user = crud.verify_user_otp(
            db,
            payload.email,
            payload.otp_code,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    token = create_access_token(
        user_id=user.id,
        username=user.username,
    )

    return schemas.TokenResponse(
        access_token=token,
        user=user,
    )


@router.post(
    "/login",
    response_model=schemas.TokenResponse,
)
def login(
    payload: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    try:
        user = crud.authenticate_user(
            db,
            payload.username,
            payload.password,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    token = create_access_token(
        user_id=user.id,
        username=user.username,
    )

    return schemas.TokenResponse(
        access_token=token,
        user=user,
    )


@router.post("/forgot-password")
def forgot_password(
    payload: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    crud.create_password_reset_otp(
        db,
        payload.email,
    )

    return {
        "message": (
            "If the account exists, "
            "a reset OTP has been sent."
        )
    }


@router.post("/reset-password")
def reset_password(
    payload: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    try:
        crud.reset_password(
            db,
            payload.email,
            payload.otp_code,
            payload.new_password,
        )

        return {
            "message": "Password reset successful"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )