from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Permite que Alembic encuentre el paquete 'app' al ejecutarse desde
# la raíz del proyecto (donde vive también este alembic.ini).
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Importamos Base y CADA modelo explícitamente: Base.metadata solo
# "conoce" las tablas de los modelos que ya fueron importados en
# algún punto del programa. Si un modelo no se importa aquí,
# autogenerate no lo vería y no generaría su tabla.
from app.database.connection import Base
from app.models.user_model import User
from app.models.device_model import Device
from app.models.loan_model import Loan

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 'target_metadata' es lo que Alembic compara contra la base de datos
# real para saber qué tablas/columnas faltan o sobran al generar
# una migración automática (alembic revision --autogenerate).
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
