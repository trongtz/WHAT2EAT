from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings # Import settings



is_sqlite = settings.DATABASE_URL.startswith("sqlite")
if is_sqlite:
    # Nếu là SQLite, bắt buộc phải có connect_args này
    engine = create_engine(
        settings.DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # Nếu là Postgres (về sau)
    engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()