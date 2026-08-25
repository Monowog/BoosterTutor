"""Database engine and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings

# pool_pre_ping tests a pooled connection before handing it out. Hosted
# Postgres drops idle connections; without this you get an occasional
# "server closed the connection unexpectedly" on the first query after a lull.
engine = create_engine(settings.sqlalchemy_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
