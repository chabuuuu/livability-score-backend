from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import redis
import os
import ssl

from dotenv import load_dotenv

load_dotenv()

# --- CẤU HÌNH CHUNG ---
# Đường dẫn đến file chứng chỉ CA (Dùng chung cho cả Postgres và Redis nếu cùng Provider)
SSL_CA_PATH = os.getenv("SSL_CA_PATH", "ca.pem")

if not os.path.exists(SSL_CA_PATH):
    print(f"⚠️ Warning: SSL CA file not found at '{SSL_CA_PATH}'. Connection might fail.")

# --- 1. POSTGRESQL CONFIG ---
# Format: postgresql://user:password@host:port/dbname
SCORING_DATABASE_URL = os.getenv("SCORING_DATABASE_URL", "postgresql://avnadmin:password@host:port/defaultdb")

db_connect_args = {
    "sslmode": "verify-ca", 
    "sslrootcert": SSL_CA_PATH
}

engine = create_engine(
    SCORING_DATABASE_URL,
    connect_args=db_connect_args
)

ScoringSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_scoring_db():
    db = ScoringSession()
    try:
        yield db
    finally:
        db.close()

