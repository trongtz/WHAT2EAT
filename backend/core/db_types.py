from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB


def json_column_type():
    return JSON().with_variant(JSONB, "postgresql")
