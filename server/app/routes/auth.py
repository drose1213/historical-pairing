import logging
import random
import smtplib
import string
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..auth.hash import hash_password, verify_password
from ..auth.jwt import create_access_token
from ..captcha import generate_captcha, verify_captcha
from ..config import settings
from ..database import get_db
from ..models import User, VerificationCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SendCodeRequest(BaseModel):
    email: EmailStr
    captcha_token: str
    captcha_answer: str


class SendCodeResponse(BaseModel):
    message: str
    expires_in: int = 600  # 10 minutes


class CaptchaResponse(BaseModel):
    token: str
    question: str
    expires_in: int = 300


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
    """发送验证码邮件。SMTP 未配置时降级为控制台输出。"""
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        print(f"[EMAIL-FALLBACK] To: {email}, Code: {code}")
        return

    sender = settings.smtp_from or settings.smtp_user
    subject = "历史配对 - 邮箱验证码"
    html_body = f"""
    <div style="max-width:480px;margin:0 auto;font-family:'Microsoft YaHei',sans-serif;color:#1a1a1a;">
      <div style="background:#246b55;padding:24px 32px;border-radius:12px 12px 0 0;text-align:center;">
        <h2 style="color:#fff;margin:0;font-size:22px;">历史配对</h2>
        <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:13px;">邮箱验证码</p>
      </div>
      <div style="background:#fff;padding:32px;border:1px solid #e8dcc8;border-top:none;border-radius:0 0 12px 12px;">
        <p style="font-size:15px;line-height:1.6;margin:0 0 20px;">您好，您正在进行历史配对账号注册，验证码如下：</p>
        <div style="background:#f4f1ea;border:2px dashed #d4c9b0;border-radius:8px;padding:20px;text-align:center;margin:0 0 20px;">
          <span style="font-size:32px;font-weight:800;color:#246b55;letter-spacing:8px;">{code}</span>
        </div>
        <p style="font-size:13px;color:#6b7280;line-height:1.6;margin:0;">验证码 10 分钟内有效，请勿泄露给他人。如非本人操作，请忽略此邮件。</p>
      </div>
    </div>
    """

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = email

    try:
        if settings.smtp_tls:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(sender, [email], msg.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(sender, [email], msg.as_string())
        logger.info("验证码邮件已发送至 %s", email)
    except Exception:
        logger.exception("发送邮件失败: %s", email)


@router.get("/captcha", response_model=CaptchaResponse)
def get_captcha() -> CaptchaResponse:
    token, question = generate_captcha()
    return CaptchaResponse(token=token, question=question)


@router.post("/send-code", response_model=SendCodeResponse)
def send_code(request: SendCodeRequest, db: Session = Depends(get_db)) -> SendCodeResponse:
    if not verify_captcha(request.captcha_token, request.captcha_answer):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码答案错误，请重新获取",
        )
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
