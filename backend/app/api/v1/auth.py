from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from ...core.database import get_db
from ...core.security import (
    create_access_token, create_refresh_token, verify_token,
    get_password_hash, verify_password, generate_mfa_secret,
    generate_mfa_qr_code, verify_mfa_token, PasswordValidator
)
from ...core.config import settings
from ...models.user import User, UserRole, Session, AuditLog
from ...schemas.user import (
    UserCreate, UserLogin, UserLoginResponse, UserResponse,
    PasswordChange, MFADisplay, MFAVerify, MFASetup
)

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )

    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is temporarily locked"
        )

    return user


def log_audit_action(
    db: Session,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Log audit action"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()


@router.post("/login", response_model=UserLoginResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.password_hash):
        # Log failed attempt if user exists
        if user:
            user.failed_login_attempts += 1

            # Lock account after too many failed attempts
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                )

            db.commit()
            log_audit_action(
                db, user.id, "LOGIN_FAILED", "auth",
                details="Invalid password",
                ip_address=request.client.host
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is temporarily locked"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )

    # Reset failed login attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if user_data.remember_me:
        access_token_expires = timedelta(days=1)  # Extended session for remember me

    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(subject=user.id)

    # Log successful login
    log_audit_action(
        db, user.id, "LOGIN_SUCCESS", "auth",
        ip_address=request.client.host
    )

    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.from_orm(user)
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    request: Request,
    db: Session = Depends(get_db)
):
    """User logout endpoint"""
    # In a real implementation, you would invalidate the token here
    # For now, we'll just log the logout
    log_audit_action(
        db, current_user.id, "LOGOUT", "auth",
        ip_address=request.client.host
    )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_orm(current_user)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    request: Request,
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate and set new password
    errors = PasswordValidator.validate(password_data.new_password)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors)
        )

    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    # Log password change
    log_audit_action(
        db, current_user.id, "PASSWORD_CHANGED", "auth",
        ip_address=request.client.host
    )

    return {"message": "Password changed successfully"}


@router.post("/setup-mfa", response_model=MFADisplay)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup multi-factor authentication"""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )

    # Generate MFA secret
    secret = generate_mfa_secret()
    qr_code = generate_mfa_qr_code(current_user.email, secret)

    # Generate backup codes
    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

    # Store secret temporarily (not enabled until verified)
    current_user.mfa_secret = secret
    db.commit()

    return MFADisplay(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )


@router.post("/verify-mfa")
async def verify_mfa_setup(
    mfa_data: MFASetup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify and enable MFA"""
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated"
        )

    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )

    # Verify the token
    if not verify_mfa_token(mfa_data.secret, mfa_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token"
        )

    # Enable MFA
    current_user.mfa_enabled = True
    db.commit()

    return {"message": "MFA enabled successfully"}


@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    access_token = create_access_token(subject=user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }