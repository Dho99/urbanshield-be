from alembic import context
from sqlalchemy import pool

from app.database.session import Base, engine
import app.models  # noqa: F401 ensure metadata is populated

target_metadata = Base.metadata

# PostGIS system tables are owned by the extension, never part of app metadata.
EXCLUDE_TABLES = {"spatial_ref_sys", "geography_columns", "geometry_columns", "raster_columns", "raster_overviews"}


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and name in EXCLUDE_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(url=str(engine.url), target_metadata=target_metadata, literal_binds=True, include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
