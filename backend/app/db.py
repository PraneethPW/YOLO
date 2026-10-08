import json
import re
import time
from contextlib import contextmanager
from pathlib import Path
from psycopg.rows import dict_row
from psycopg import OperationalError,InterfaceError
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
    retryable=sql.lstrip().upper().startswith(('SELECT','UPDATE','WITH UPDATED AS'))
    for attempt in range(2):
        try:
            with pool.connection() as conn:
                # Send namespace selection and the query in one network batch.
                with conn.pipeline():
                    conn.execute(f'SET LOCAL search_path TO {settings.database_schema},public')
                    cursor=conn.execute(sql,params)
                if cursor.description:
                    return cursor.fetchone() if one else cursor.fetchall()
                return None
        except (OperationalError,InterfaceError):
            if attempt or not retryable:
                raise
            time.sleep(.15)


def event(kind, payload):
    source_id = payload.get('source_id') or (payload.get('id') if kind in ('source','frame') else None)
    owner = None
    if source_id:
        owner = query('SELECT id AS source_id,created_by FROM sources WHERE id=%s',(source_id,),one=True)
    elif kind in ('job','incident') and payload.get('id'):
        table = 'jobs' if kind=='job' else 'incidents'
        owner = query(f'SELECT s.id AS source_id,s.created_by FROM {table} r JOIN sources s ON s.id=r.source_id WHERE r.id=%s',(payload['id'],),one=True)
    elif kind=='alert' and payload.get('incident_id'):
        owner = query('SELECT s.id AS source_id,s.created_by FROM incidents i JOIN sources s ON s.id=i.source_id WHERE i.id=%s',(payload['incident_id'],),one=True)
    query('INSERT INTO events(kind,payload,owner_id,source_id) VALUES(%s,%s::jsonb,%s,%s)',
          (kind,json.dumps(payload,default=str),owner['created_by'] if owner else None,owner['source_id'] if owner else None))


def close():
    if pool:
        pool.close()
