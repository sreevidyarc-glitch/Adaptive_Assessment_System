import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, security_bearer
from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    generate_secure_otp,
    decode_access_token
)
from app.models.user import User, RoleEnum, OTPToken, TokenBlacklist
from app.schemas.auth import (
    FacultyLoginInitRequest,
    FacultyLoginInitResponse,
    FacultyVerifyOTPRequest,
    StudentLoginRequest,
    TokenResponse,
    UserResponse
)

logger = logging.getLogger("adaptive_assessment.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/faculty/login-init", response_model=FacultyLoginInitResponse)
def faculty_login_init(payload: FacultyLoginInitRequest, db: Session = Depends(get_db)):
    """
    Step 1 of Faculty Login:
    Verifies faculty credentials and issues a temporary OTP.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if user.role != RoleEnum.FACULTY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: The requested portal requires a Faculty account."
        )

    # Invalidate previous unconsumed OTPs for this user
    db.query(OTPToken).filter(
        OTPToken.user_id == user.id,
        OTPToken.is_consumed == False
    ).update({"is_consumed": True})

    otp_code = generate_secure_otp(6)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    otp_record = OTPToken(
        user_id=user.id,
        otp_code=otp_code,
        purpose="FACULTY_LOGIN",
        expires_at=expires_at,
        attempts=0,
        is_consumed=False
    )
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    logger.info(f"Generated Faculty OTP for {user.email}: [{otp_code}] (Valid for {settings.OTP_EXPIRE_MINUTES} mins)")

    dev_otp = otp_code if (settings.DEV_EXPOSE_OTP_IN_RESPONSE or settings.DEBUG) else None

    return FacultyLoginInitResponse(
        status="OTP_SENT",
        message=f"A 6-digit verification code has been issued. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.",
        session_ticket=otp_record.id,
        dev_otp=dev_otp
    )

@router.post("/faculty/verify-otp", response_model=TokenResponse)
def faculty_verify_otp(payload: FacultyVerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Step 2 of Faculty Login:
    Verifies the OTP and issues a 30-minute faculty session token.
    """
    otp_record = db.query(OTPToken).filter(OTPToken.id == payload.session_ticket).first()
    if not otp_record or otp_record.is_consumed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP session. Please initiate login again."
        )

    now = datetime.now(timezone.utc)
    # Ensure timezone awareness for comparison
    otp_expires = otp_record.expires_at
    if otp_expires.tzinfo is None:
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)

    if now > otp_expires:
        otp_record.is_consumed = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new code."
        )

    if otp_record.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp_record.is_consumed = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum verification attempts exceeded. Please login again."
        )

    otp_record.attempts += 1

    if otp_record.otp_code != payload.otp_code.strip():
        db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - otp_record.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect OTP. {remaining} attempt(s) remaining."
        )

    # Consume OTP
    otp_record.is_consumed = True
    db.commit()

    user = db.query(User).filter(User.id == otp_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    # Issue 30-minute faculty session token
    token_str, jti, expire_dt = create_access_token(
        subject=user.id,
        role=user.role.value
    )

    return TokenResponse(
        access_token=token_str,
        token_type="bearer",
        expires_in_minutes=settings.FACULTY_TOKEN_EXPIRE_MINUTES,
        role=user.role.value,
        user=UserResponse.model_validate(user)
    )

@router.post("/student/login", response_model=TokenResponse)
def student_login(payload: StudentLoginRequest, db: Session = Depends(get_db)):
    """
    Student Login:
    Verifies student roll number / email and issues a 60-minute student session token.
    """
    identifier = payload.identifier.strip()
    user = db.query(User).filter(
        (User.roll_number == identifier) | (User.email == identifier)
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid roll number/email or password."
        )

    if user.role != RoleEnum.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: The requested portal requires a Student account."
        )

    # Issue 60-minute student session token
    token_str, jti, expire_dt = create_access_token(
        subject=user.id,
        role=user.role.value
    )

    return TokenResponse(
        access_token=token_str,
        token_type="bearer",
        expires_in_minutes=settings.STUDENT_TOKEN_EXPIRE_MINUTES,
        role=user.role.value,
        user=UserResponse.model_validate(user)
    )

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revokes the current session token immediately via TokenBlacklist.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        jti = payload.get("jti")
        exp_ts = payload.get("exp")
        exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else datetime.now(timezone.utc) + timedelta(hours=1)

        if jti:
            blacklist_entry = TokenBlacklist(
                jti=jti,
                user_id=current_user.id,
                expires_at=exp_dt
            )
            db.add(blacklist_entry)
            db.commit()
    except Exception as e:
        logger.warning(f"Error blacklisting token on logout: {e}")

    return {"status": "SUCCESS", "message": "Successfully logged out. Session has been revoked."}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

