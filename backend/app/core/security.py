"""Security utilities for authentication and authorization."""
import uuid
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.schemas.auth import TokenData

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# JWT settings
ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> tuple[str, str, datetime]:
    """
    Create a JWT access token with jti for blacklist support.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Tuple of (encoded_jwt, jti, expires_at)
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Generate unique token identifier for blacklist tracking
    jti = str(uuid.uuid4())

    to_encode.update({
        "exp": expire,
        "jti": jti,
        "iat": datetime.utcnow(),
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire


def verify_token(token: str, db: Session | None = None) -> TokenData | None:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string
        db: Database session for blacklist check (optional)

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        jti: str = payload.get("jti")

        if user_id is None:
            return None

        # Check if token is blacklisted
        if db is not None and jti and TokenBlacklist.is_blacklisted(db, jti):
            return None

        return TokenData(user_id=user_id, username=username, jti=jti)
    except JWTError:
        return None


def blacklist_token(
    db: Session,
    jti: str,
    expires_at: datetime,
    user_id: UUID | None = None,
    reason: str = "logout"
) -> TokenBlacklist:
    """
    Add a token to the blacklist.

    Args:
        db: Database session
        jti: JWT ID to blacklist
        expires_at: When the token expires (for cleanup)
        user_id: Optional user ID who owned this token
        reason: Reason for blacklisting

    Returns:
        Created TokenBlacklist record
    """
    record = TokenBlacklist(
        jti=jti,
        user_id=user_id,
        expires_at=expires_at,
        reason=reason,
    )
    db.add(record)
    db.commit()
    return record


def get_user_by_username(db: Session, username: str) -> User | None:
    """Get a user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate a user with username and password.

    Args:
        db: Database session
        username: User's username
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Get the current authenticated user from JWT token.

    Security: Checks httpOnly cookie first, then falls back to Authorization header.
    This prevents XSS attacks while maintaining backward compatibility.

    Args:
        request: FastAPI request object to access cookies
        token: JWT token from Authorization header (fallback)
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    # Priority 1: Check httpOnly cookie (secure against XSS)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        # PGY2-01ie format is "Bearer <token>", extract the token
        if cookie_token.startswith("Bearer "):
            token = cookie_token[7:]
        else:
            token = cookie_token
    # Priority 2: Fall back to Authorization header (for API clients)
    elif not token:
        return None

    token_data = verify_token(token, db)
    if token_data is None or token_data.user_id is None:
        return None

    user = get_user_by_id(db, UUID(token_data.user_id))
    if user is None or not user.is_active:
        return None

    return user


async def get_current_active_user(
    current_user: User | None = Depends(get_current_user)
) -> User:
    """
    Require an authenticated active user.

    Raises HTTPException if not authenticated.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require an admin user.

    Raises HTTPException if not admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_scheduler_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require a user who can manage schedules (admin or coordinator).

    Raises HTTPException if not authorized.
    """
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Schedule management access required",
        )
    return current_user
