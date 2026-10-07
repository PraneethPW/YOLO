import json
import re
from contextlib import contextmanager
from pathlib import Path
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from .config import settings

pool: ConnectionPool | None = None


def start():
    global pool
    if not settings.database_url:
        raise RuntimeError('DATABASE_URL is required. There is no sample database fallback.')
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}',settings.database_schema):
        raise RuntimeError('Invalid DATABASE_SCHEMA')
    pool = ConnectionPool(settings.database_url, min_size=1, max_size=8,
                          kwargs={'row_factory': dict_row, 'prepare_threshold': None}, open=True)
    pool.wait(timeout=30)
    with pool.connection() as conn:
        conn.execute(f'CREATE SCHEMA IF NOT EXISTS {settings.database_schema}')
        conn.execute(f'SET LOCAL search_path TO {settings.database_schema},public')
        conn.execute(Path(__file__).with_name('schema.sql').read_text())


@contextmanager
def connection():
    if pool is None:
        raise RuntimeError('Database is not connected')
    # PgBouncer transaction pooling does not preserve per-session settings.
    # Set the namespace inside every transaction, never in startup options.
    with pool.connection() as conn:
        conn.execute(f'SET LOCAL search_path TO {settings.database_schema},public')
        yield conn


def query(sql, params=(), one=False):
    if pool is None:
        raise RuntimeError('Database is not connected')
    with connection() as conn:
        cursor = conn.execute(sql, params)
        if cursor.description:
            return cursor.fetchone() if one else cursor.fetchall()
        return None


def event(kind, payload):
    query('INSERT INTO events(kind,payload) VALUES(%s,%s::jsonb)', (kind, json.dumps(payload, default=str)))


def close():
    if pool:
        pool.close()
