import random
import string
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..auth.hash import hash_password, verify_password
from ..auth.jwt import create_access_token
from ..database import get_db
from ..models import User, VerificationCode

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SendCodeRequest(BaseModel):
    email: EmailStr


class SendCodeResponse(BaseModel):
    message: str
    expires_in: int = 600  # 10 minutes


class RegisterRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def _send_email(email: str, code: str) -> None:
    # TODO: Implement actual email sending
    # For now, just print to console
    print(f"[EMAIL] To: {email}, Code: {code}")


@router.post("/send-code", response_model=SendCodeResponse)
def send_code(request: SendCodeRequest, db: Session = Depends(get_db)) -> SendCodeResponse:
    # Check if there's a recent code that hasn't expired (60 second cooldown)
    recent = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.email == request.email,
            VerificationCode.expires_at > datetime.now(timezone.utc),
            VerificationCode.used == False,  # noqa: E712
        )
        .order_by(VerificationCode.created_at.desc())
        .first()
    )

    if recent:
        elapsed = (datetime.now(timezone.utc) - recent.created_at).total_seconds()
        if elapsed < 60:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="验证码已发送，请稍后再试",
            )

    # Create new code
    code = _generate_code()
    verification = VerificationCode(
        email=request.email,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(verification)
    db.commit()

    # Send email
    _send_email(request.email, code)

    return SendCodeResponse(message="验证码已发送")


@router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    # Find valid verification code
    verification = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.email == request.email,
            VerificationCode.code == request.code,
            VerificationCode.expires_at > datetime.now(timezone.utc),
            VerificationCode.used == False,  # noqa: E712
        )
        .order_by(VerificationCode.created_at.desc())
        .first()
    )

    if verification is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    # Mark code as used
    verification.used = True

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已注册")

    # Create user
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    access_token = create_access_token(data={"sub": user.id})

    return AuthResponse(
        access_token=access_token,
        user=UserResponse(id=user.id, email=user.email, is_admin=user.is_admin),
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == request.email).first()
    if user is None or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    access_token = create_access_token(data={"sub": user.id})

    return AuthResponse(
        access_token=access_token,
        user=UserResponse(id=user.id, email=user.email, is_admin=user.is_admin),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_admin=current_user.is_admin,
    )


AuthResponse.model_rebuild()
