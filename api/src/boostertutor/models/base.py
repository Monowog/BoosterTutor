"""Shared declarative base for all tables."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Postgres auto-names indexes and constraints when you don't, and those generated
# names differ between databases. Alembic then can't reliably drop or alter them
# later - it doesn't know what they're called. Fixing the naming scheme now costs
# nothing; retrofitting it onto an existing database is genuinely painful.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Every model inherits from this. Alembic reads Base.metadata to see the schema."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
