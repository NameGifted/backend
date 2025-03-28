from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Use your preferred database URL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User Model (Database)
class User(Base):
    """SQLAlchemy model for the users table."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Hashed password
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    address = Column(String)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    date_joined = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    def set_password(self, password: str):
        """Set the user's password with hashing."""
        self.password = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the provided password against the stored hash."""
        return pwd_context.verify(password, self.password)

# Pydantic Schemas (API Validation)
class UserCreate(BaseModel):
    """Schema for user registration input."""
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str
    address: str

class UserOut(BaseModel):
    """Schema for user output, excluding sensitive data like password."""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: str
    address: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    date_joined: datetime
    last_login: Optional[datetime]

    class Config:
        orm_mode = True  # Allows mapping from SQLAlchemy objects

class UserUpdate(BaseModel):
    """Schema for updating user details, with optional fields."""
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str

# JWT Configuration
SECRET_KEY = "your_secret_key"  # Replace with a secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency to retrieve the current user from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# API Router
router = APIRouter()

# Endpoints
@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check for existing username
    existing_user = db.query(User).filter(User.username == ▋
