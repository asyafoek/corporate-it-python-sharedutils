import logging
from sqlalchemy import text, inspect
from datetime import datetime
from dateutil.parser import parse

from decimal import Decimal
from typing import Any, Dict

from decimal import Decimal, InvalidOperation
# from typing import Any, Dict
from typing import List, Dict, Any, Optional

import json

import pandas as pd
from sqlalchemy import create_engine, text, Table, MetaData
from sqlalchemy import MetaData, Table, select, and_
from sqlalchemy.dialects.postgresql import insert

from sqlalchemy import select, and_
from typing import List
import psycopg2

import re
from typing import Literal
import os

KeyCase = Literal["lower", "upper", None]

def get_schema_dict(records: list[dict]) -> dict:
    """
    Returns a    The value for each key is the first non-None value encountered,    Returns a single dict containing all keys found in the records.
    so datatypes can be inferred.
    """
    schema = {}

    for record in records:
        for key, value in record.items():
            if key not in schema and value is not None:
                schema[key] = value

    return schema

# -----------------------------
# Connection
# -----------------------------

def get_default_engine(schema="raw"):
    user=os.environ["PG_USER"]
    password=os.environ["PG_PASSWORD"]
    db=os.environ["PG_DATABASE"]
    # schema="raw"
    host=os.environ["PG_HOST"]
    port="5432"

    engine = get_engine(user,password,db,host,port)
    return user, password, db, schema, host, port, engine

def get_engine(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT="5432", DB_DRIVER="postgresql+psycopg2"):
    # DB_HOST = "db"
    # DB_PORT = "5432"
    # DB_NAME = "trading_system"
    # DB_USER = "dbt_user"
    # DB_PASSWORD = "dbt_pass"
    DATABASE_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    engine = create_engine(DATABASE_URL)
    return engine 

def get_connection(host: str, port: str, user: str, password: str, dbname: str):
    """Create a PostgreSQL connection using explicit parameters only"""

    return psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname,
    )


# -----------------------------
# Databases
# -----------------------------

def list_databases(conn) -> List[str]:
    """Return all non-template databases using existing connection"""

    cur = conn.cursor()

    cur.execute("""
        SELECT datname
        FROM pg_database
        WHERE datistemplate = false;
    """)

    dbs = [row[0] for row in cur.fetchall()]

    cur.close()
    return dbs


# -----------------------------
# Schemas
# -----------------------------

def list_schemas(conn) -> List[str]:
    """Return all schemas in the current database using existing connection"""

    cur = conn.cursor()

    cur.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name;
    """)

    schemas = [row[0] for row in cur.fetchall()]

    cur.close()
    return schemas


# -----------------------------
# Main
# -----------------------------

def summary():
    """Create connection from env vars and reuse it across all methods"""

    host = os.environ["PG_HOST"]
    port = os.environ.get("PG_PORT", "5432")
    user = os.environ["PG_USER"]
    password = os.environ["PG_PASSWORD"]
    dbname = os.environ["PG_DATABASE"]

    conn = get_connection(host, port, user, password, dbname)

    try:
        print("Databases:")
        for db in list_databases(conn):
            print(" -", db)

        print("\nSchemas:")
        for s in list_schemas(conn):
            print(" -", s)

    finally:
        conn.close()



def split_keys_on_uppercase(obj):
    """
    Recursively split dictionary keys on uppercase letters.
    Example: 'prevDayVW' -> 'prev_Day_V_W'
    Casing is preserved; lower/upper happens elsewhere.
    """
    def split_key(key: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', key)

    if isinstance(obj, dict):
        return {
            split_key(k): split_keys_on_uppercase(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [split_keys_on_uppercase(item) for item in obj]
    else:
        return obj

# def flatten_json(y, parent_key="", sep="_"):
#     items = []
#     for k, v in y.items():
#         new_key = f"{parent_key}{sep}{k}" if parent_key else k
#         if isinstance(v, dict):
#             items.extend(flatten_json(v, new_key, sep=sep).items())
#         else:
#             items.append((new_key, v))
#     return dict(items)

def flatten_json(y, parent_key="", sep="_", key_case=None, split_on_upper=False):
    items = []
    for k, v in y.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(
                flatten_json(
                    v,
                    new_key,
                    sep=sep,
                    key_case=None,
                    split_on_upper=False,
                ).items()
            )
        else:
            items.append((new_key, v))

    flat = dict(items)

    if split_on_upper:
        flat = split_keys_on_uppercase(flat)

    flat = normalize_key_case(flat, key_case)

    return flat


# def flatten_json_array(records, sep="_", lowercase_keys=True):
#     """
#     Takes a list of nested dictionaries and returns a list of flattened dictionaries.

#     Args:
#         records (list[dict]): List of nested dictionaries
#         sep (str): Separator for flattened keys
#         lowercase_keys (bool): Whether to lowercase all keys (default True)

#     Returns:
#         list[dict]: List of flattened dictionaries
#     """
#     if not records:
#         return []

#     if not isinstance(records, list):
#         raise TypeError("Expected a list of dictionaries")

#     flattened = []
#     for item in records:
#         if not isinstance(item, dict):
#             raise TypeError("All items in the list must be dictionaries")

#         flat = flatten_json(item, sep=sep)

#         if lowercase_keys:
#             flat = {k.lower(): v for k, v in flat.items()}

#         flattened.append(flat)

#     return flattened


def flatten_json_array(records, sep="_", key_case=None, split_on_upper=False):
    if not records:
        return []

    if not isinstance(records, list):
        raise TypeError("Expected a list of dictionaries")

    flattened = []
    for item in records:
        if not isinstance(item, dict):
            raise TypeError("All items in the list must be dictionaries")

        flattened.append(
            flatten_json(
                item,
                sep=sep,
                key_case=key_case,
                split_on_upper=split_on_upper,
            )
        )

    return flattened


def lowercase_keys(obj):
    """
    Recursively lowercases all dictionary keys.
    Works for dicts, lists, and nested structures.
    """
    if isinstance(obj, dict):
        return {k.lower(): lowercase_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [lowercase_keys(item) for item in obj]
    else:
        return obj


def uppercase_keys(obj):
    """
    Recursively uppercases all dictionary keys.
    Works for dicts, lists, and nested structures.
    """
    if isinstance(obj, dict):
        return {k.upper(): uppercase_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [uppercase_keys(item) for item in obj]
    else:
        return obj


def normalize_key_case(obj, key_case: KeyCase):
    """
    Normalize dict keys based on key_case:
    - "lower": lowercase all keys
    - "upper": uppercase all keys
    - None: leave as-is
    """
    if key_case == "lower":
        return lowercase_keys(obj)
    if key_case == "upper":
        return uppercase_keys(obj)
    return obj

def lower_set_values(input_set: set[str]) -> set[str]:
    """
    Returns a new set with all string values from input_set converted to lowercase.
    """
    return {value.lower() for value in input_set}



def convert_jsonb_to_string(data: Dict[str, Any]) -> Dict[str, Any]:
    def convert_value(val: Any) -> Any:
        if isinstance(val, (dict, list)):
            try:
                return json.dumps(val)
            except (TypeError, ValueError):
                return val  # leave unchanged if not serializable
        elif isinstance(val, str):
            try:
                # if it's already a valid JSON string, keep it
                json.loads(val)
                return val
            except json.JSONDecodeError:
                return val
        else:
            return val  # leave numbers, bools, None, etc.

    return {k: convert_value(v) for k, v in data.items()}

def convert_floats_to_decimal(data: Dict[str, Any]) -> Dict[str, Any]:
    def convert_value(val):
        if isinstance(val, float):
            try:
                return Decimal(str(val))
            except InvalidOperation:
                return val
        elif isinstance(val, Decimal):
            try:
                # Try to parse string as float-like value
                return val
            except InvalidOperation:
                return val
        elif isinstance(val, str):
            try:
                # Try to parse string as float-like value
                # return Decimal(val)
                return val
            except InvalidOperation:
                return val
        elif isinstance(val, dict):
            return {k: convert_value(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [convert_value(item) for item in val]
        else:
            return val  # Leave ints, bools, None, etc. untouched

    return {k: convert_value(v) for k, v in data.items()}


def lowercase_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    def normalize(obj):
        if isinstance(obj, dict):
            return {k.lower(): normalize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [normalize(item) for item in obj]
        else:
            return obj
    return normalize(data)

def get_postgres_type(dtype):
    # Map pandas dtype to postgres type
    if pd.api.types.is_float_dtype(dtype):
        return "NUMERIC"
    elif pd.api.types.is_integer_dtype(dtype):
        return "NUMERIC"
    # elif pd.api.types.is_integer_dtype(dtype):
    #     return "BIGINT"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMPTZ"
    else:
        # fallback to text for object, string types
        return "TEXT"

def ensure_table_from_dataframe(df, engine, table_name):
     # Build CREATE TABLE IF NOT EXISTS DDL dynamically from df dtypes
    columns_ddl = []
    for col, dtype in df.dtypes.items():
        pg_type = get_postgres_type(dtype)
        columns_ddl.append(f'"{col.lower()}" {pg_type}')
    columns_sql = ", ".join(columns_ddl)

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name.lower()} (
        {columns_sql}
    );
    """

    with engine.begin() as conn:  # begin() ensures commit
        conn.execute(text(create_table_sql))


    
def ensure_schema_and_table(db, schema, table, flat_json, metrics_counter, allow_drop=False, alter_existing=False):
    with db.begin() as conn:
        # Ensure schema exists
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
 
        inspector = inspect(conn)
        if table in inspector.get_table_names(schema=schema):
            # Check column differences
            existing_cols = {col["name"]: col["type"] for col in inspector.get_columns(table, schema=schema)}

            # make sure to lowercase all columns because in db we assume column names are always in lower case
            # Incoming event might still have mixed case keys in dict, so compare with lower case
            lower_keys_flat_json = lowercase_keys(flat_json)
            incoming_cols = set(lower_keys_flat_json.keys())

            new_cols = incoming_cols - set(existing_cols.keys())
            missing_cols = set(existing_cols.keys()) - incoming_cols

            logging.debug(f"Existing columns: {existing_cols}")
            logging.debug(f"Incoming columns: {incoming_cols}")

            logging.debug(f"New columns: {new_cols}")
            logging.debug(f"Missing columns: {missing_cols}")
 
            for col in new_cols:
                try:
                    sql_type = _infer_sql_type(flat_json[col])
                    conn.execute(text(f"ALTER TABLE {schema}.{table} ADD COLUMN {col} {sql_type}"))
                    if metrics_counter is not None:
                        metrics_counter.labels(schema=schema, table=table, change_type="column_added").inc()
                except Exception as e:
                    conn.rollback()
                    logging.warning(f"Could not add column: {col}, because {e}")
                     
            if allow_drop:
                for col in missing_cols:
                    conn.execute(text(f"ALTER TABLE {schema}.{table} DROP COLUMN {col}"))
                    if metrics_counter is not None:
                        metrics_counter.labels(schema=schema, table=table, change_type="column_dropped").inc()
 
            # Check for type changes
            for col, val in flat_json.items():
                if col in existing_cols:
                    new_type = _infer_sql_type(val)
                    if str(existing_cols[col]).lower() != new_type.lower():
                        if alter_existing:
                            # try:
                            #     conn.execute(text(f"ALTER TABLE {schema}.{table} ALTER COLUMN {col} TYPE {new_type}"))
                            # except:
                            #     conn.execute(text(f"ALTER TABLE {schema}.{table} ALTER COLUMN {col} TYPE {new_type} USING {col}::{new_type}"))
                            conn.execute(text(f"ALTER TABLE {schema}.{table} ALTER COLUMN {col} TYPE {new_type} USING {col}::{new_type}"))


                            if metrics_counter is not None:
                                metrics_counter.labels(schema=schema, table=table, change_type="type_changed").inc()
        else:
            # Create new table and preserve column name mixed case
            # columns_def = ", ".join(f'"{k}" {_infer_sql_type(v)}' for k, v in flat_json.items())
            columns_def = ", ".join(f'{k.lower()} {_infer_sql_type(v)}' for k, v in flat_json.items())
            conn.execute(text(f"CREATE TABLE {schema}.{table} ({columns_def})"))

def _infer_sql_type(value):
    # Handle float type
    if isinstance(value, bool):
        return "BOOLEAN"    
    # Handle integer type
    elif isinstance(value, int):
        return "BIGINT"
    # Handle float type
    elif isinstance(value, float) or isinstance(value, Decimal):
        # return "DOUBLE PRECISION"
        return "NUMERIC"

    # elif isinstance(value, float):
    #     # return "DOUBLE PRECISION"
    #     return "NUMERIC"
    # elif isinstance(value, Decimal):
    #     # return "DOUBLE PRECISION"
    #     return "NUMERIC"
    # # Handle boolean type
    # # Handle integer type
    # elif isinstance(value, int):
    #     if value == 0:
    #         return "NUMERIC"  # Default to numeric for ambiguous 0
    #     else:
    #         return "BIGINT"
    
    # Handle string type
    elif isinstance(value, str):
        # Do not make strings numeric automatically is not always what is expected, only check for datetime
        try:
            parsed_date = parse(value)
            # If the string contains time zone information, use TIMESTAMP WITH TIME ZONE
            if '+' in value or 'Z' in value:  # Check if there's a time zone info in the string
                return "TIMESTAMP WITH TIME ZONE"
            else:
                # return "TIMESTAMP"
                try:
                    float_value = Decimal(value)
                    # return "DOUBLE PRECISION"
                    if str(value).lower() == 'nan':
                        return "TEXT"
                    else:
                        return "NUMERIC"
                except:
                    return "TEXT"
        except (ValueError, OverflowError):
            # If it's not a valid datetime, treat it as a regular string
            return "TEXT"


    # Handle datetime type (already a datetime object)
    elif isinstance(value, datetime):
        # Check if the datetime object is timezone-aware
        if value.tzinfo is not None:
            return "TIMESTAMP WITH TIME ZONE"  # Handle timezone-aware datetime
        else:
            return "TIMESTAMP"  # Handle naive datetime (without timezone)
    
    # Handle dictionary or list (assume JSON type)
    elif isinstance(value, dict) or isinstance(value, list):
        return "JSONB"
    
    # If it's none of the above, treat it as text
    else:
        return "TEXT"


# Add this log to print out the JSON being inserted
def log_insert_data(flat_json):
    logging.info("Inserting the following data into the database:")
    for key, value in flat_json.items():
        logging.info(f"Column: {key}, Value: {value}")



# def store_dicts_into_table(engine, records: list[dict], schema: str, table_name: str, upsert: bool = False, ignore_keys={"reference_data_id", "updated_at", "value"}):
#     """
#     Inserts or upserts a list of dictionaries into a specified table (DB-agnostic).

#     Args:
#         engine: SQLAlchemy engine.
#         records (list of dict): List of records to insert.
#         table_name (str): Target table name.
#         upsert (bool): If True, update 'value' if record exists matching other columns
#                        (excluding reference_data_id, updated_at, and value).
#     """
#     if not records:
#         print("No records to insert.")
#         return

#     metadata = MetaData()
#     table = Table(table_name, metadata, schema=schema, autoload_with=engine)

#     # ignore_keys = {"reference_data_id", "updated_at", "value"}

#     with engine.begin() as conn:
#         for record in records:
#             if not upsert:
#                 # Insert only
#                 conn.execute(table.insert().values(**record))
#             else:
#                 # Match on all columns except ignored ones
#                 match_keys = {k: v for k, v in record.items() if k not in ignore_keys}

#                 sel = select(table).where(
#                     and_(*(table.c[k] == v for k, v in match_keys.items()))
#                 )
#                 existing = conn.execute(sel).first()

#                 if existing:
#                     update_values = {k: v for k, v in record.items() if k in ignore_keys}
#                     if update_values:                    
#                         upd = (
#                             table.update()
#                             .where(
#                                 and_(*(table.c[k] == v for k, v in match_keys.items()))
#                             )
#                             # .values(value=record["value"])
#                             .values(**update_values)                            
#                         )
#                         conn.execute(upd)
#                 else:
#                     conn.execute(table.insert().values(**record))

def store_dicts_into_table(
    engine,
    records: list[dict],
    schema: str,
    table_name: str,
    upsert: bool = False,
    ignore_keys=None,
    conflict_cols: list[str] | None = None,
    use_bulk: bool = False,
):
    if not records:
        return

    metadata = MetaData()
    table = Table(table_name, metadata, schema=schema, autoload_with=engine)

    ignore_keys = ignore_keys or {"reference_data_id", "updated_at", "value"}

    with engine.begin() as conn:

        # -----------------------------------
        # ✅ FAST PATH (bulk insert / upsert)
        # -----------------------------------
        if use_bulk:

            # ✅ maak alle records dezelfde structuur
            all_keys = set().union(*(r.keys() for r in records))

            normalized_records = [
                {k: r.get(k, None) for k in all_keys}
                for r in records
            ]

            # stmt = insert(table).values(records)
            stmt = insert(table).values(normalized_records)

            # ✅ BULK UPSERT (only if configured)
            if upsert and conflict_cols:
                update_cols = {
                    c.name: stmt.excluded[c.name]
                    for c in table.columns
                    if c.name not in conflict_cols
                }

                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_cols,
                    set_=update_cols
                )

            conn.execute(stmt)
            return

        # -----------------------------------
        # ✅ SAFE GENERIC PATH (old logic)
        # -----------------------------------
        for record in records:

            if not upsert:
                conn.execute(table.insert().values(**record))
                continue

            match_keys = {k: v for k, v in record.items() if k not in ignore_keys}

            sel = select(table).where(
                and_(*(table.c[k] == v for k, v in match_keys.items()))
            )

            existing = conn.execute(sel).first()

            if existing:
                update_values = {k: v for k, v in record.items() if k in ignore_keys}
                if update_values:
                    upd = (
                        table.update()
                        .where(
                            and_(*(table.c[k] == v for k, v in match_keys.items()))
                        )
                        .values(**update_values)
                    )
                    conn.execute(upd)
            else:
                conn.execute(table.insert().values(**record))


def select_to_json(engine, sql: str, params: dict | None = None) -> list[dict]:
    """
    Execute a SELECT statement and return the result as a list of dicts (JSON-like).

    Args:
        engine (sqlalchemy.engine.Engine): SQLAlchemy engine
        sql (str): SELECT query
        params (dict | None): Optional bind parameters

    Returns:
        list[dict]: Query result as list of dictionaries
    """
    params = params or {}

    with engine.connect() as conn:
        result = conn.execute(text(sql), params)

        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]