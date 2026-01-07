import uuid
from datetime import datetime
import sys
import os

# Add /app to sys.path to find app module
sys.path.append("/app")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import get_settings

def create_test_users():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        # Create 5 resident users
        for i in range(5):
            username = f"resident_{i}"
            email = f"resident_{i}@example.com"

            # Check if exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                continue

            new_user = User(
                id=uuid.uuid4(),
                username=username,
                email=email,
                hashed_password=get_password_hash("password123"),
                role="resident",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(new_user)

        # Create 5 faculty users
        for i in range(5):
            username = f"faculty_{i}"
            email = f"faculty_{i}@example.com"

            # Check if exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                continue

            new_user = User(
                id=uuid.uuid4(),
                username=username,
                email=email,
                hashed_password=get_password_hash("password123"),
                role="faculty",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(new_user)

        session.commit()
        print("Created test users.")

if __name__ == "__main__":
    create_test_users()
