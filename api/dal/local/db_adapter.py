from __future__ import annotations

from contextlib import contextmanager

from core.logs import error
from core.settings import app_settings
from sqlalchemy import (
    MetaData,
    Table,
    and_,
    create_engine,
    delete,
    insert,
    inspect,
    select,
    update,
)
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchTableError


class DBAdapter:
    """
    Database Adapter for MySQL (also works for other SQLAlchemy-supported DBs).
    Provides engine access, safe connection context, reflection, and CRUD methods.
    """

    def __init__(self, engine: Engine | None = None):
        settings = app_settings()

        # Make sure your uri() is a MySQL URI, e.g.:
        # mysql+pymysql://user:pass@host:port/dbname?charset=utf8mb4
        self.engine = engine or create_engine(
            settings.colors_auto_training_db.uri(),
            pool_pre_ping=True,  # important for cloud DBs (Aiven)
        )

        # Remove postgres-only type registration
        # (keep this adapter generic; register dialect-specific types elsewhere if needed)

    def get_engine(self) -> Engine:
        return self.engine

    @contextmanager
    def connect(self):
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def get_inspector(self):
        return inspect(self.engine)

    def reflect_table(self, table_name: str, schema: str | None = None) -> Table:
        metadata = MetaData()
        try:
            # For MySQL, schema is the database name; usually you can pass None
            return Table(table_name, metadata, autoload_with=self.engine, schema=schema)
        except NoSuchTableError:
            raise ValueError(f"Table '{table_name}' not found in the database.")

    # ------- CRUD operations -------- #

    def read_all(self, table_name: str, schema: str | None = None):
        table = self.reflect_table(table_name, schema)
        stmt = select(table)
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(stmt).mappings().all()]

    def _build_conditions(self, table: Table, where: dict):
        conditions = []

        for key, value in where.items():
            if key not in table.c:
                raise ValueError(f"Unknown column '{key}' for table '{table.name}'")

            col = table.c[key]

            if isinstance(value, dict):
                for op, op_val in value.items():
                    if op == "$gte":
                        conditions.append(col >= op_val)
                    elif op == "$lte":
                        conditions.append(col <= op_val)
                    elif op == "$gt":
                        conditions.append(col > op_val)
                    elif op == "$lt":
                        conditions.append(col < op_val)
                    elif op == "$in":
                        if not isinstance(op_val, (list, tuple, set)):
                            raise ValueError(
                                f"$in for '{key}' must be a list/tuple/set"
                            )
                        conditions.append(col.in_(list(op_val)))
                    elif op == "$isnull":
                        conditions.append(col.is_(None) if op_val else col.is_not(None))
                    else:
                        raise ValueError(f"Unsupported operator '{op}' for '{key}'")
            else:
                conditions.append(col == value)

        return conditions

    def read_where_many(
        self,
        table_name: str,
        where: dict,
        *,
        limit: int | None = None,
        offset: int | None = None,
        order_by: list | None = None,
        schema: str | None = None,
    ):
        table = self.reflect_table(table_name, schema)
        conditions = self._build_conditions(table, where)
        stmt = select(table).where(and_(*conditions))

        if order_by:
            stmt = stmt.order_by(*order_by)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        with self.connect() as conn:
            return [dict(r) for r in conn.execute(stmt).mappings().all()]

    def read_where_one(self, table_name: str, where: dict, schema: str | None = None):
        table = self.reflect_table(table_name, schema)
        conditions = self._build_conditions(table, where)
        stmt = select(table).where(and_(*conditions)).limit(1)
        with self.connect() as conn:
            row = conn.execute(stmt).mappings().first()
            return dict(row) if row is not None else None

    def read_by_id(
        self,
        table_name: str,
        id_value,
        id_column: str = "id",
        schema: str | None = None,
    ):
        table = self.reflect_table(table_name, schema)
        stmt = select(table).where(table.c[id_column] == id_value).limit(1)
        with self.connect() as conn:
            row = conn.execute(stmt).mappings().first()
            return dict(row) if row is not None else None

    def insert_row(
        self,
        table_name: str,
        data: dict,
        schema: str | None = None,
        *,
        ignore: bool = False,
    ):
        table = self.reflect_table(table_name, schema)

        if ignore:
            # INSERT IGNORE ... (MySQL)
            stmt = mysql_insert(table).values(**data).prefix_with("IGNORE")
            with self.connect() as conn:
                result = conn.execute(stmt)
                conn.commit()
                return result.rowcount == 1  # ✅ True inserted, False already existed

        # normal insert (your original behavior)
        stmt = insert(table).values(**data)
        with self.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()
            pk = result.inserted_primary_key
            if pk:
                return pk[0]
            return data.get("id")

    def update_row(
        self,
        table_name: str,
        id_value,
        data: dict,
        id_column: str = "id",
        schema: str | None = None,
    ):
        table = self.reflect_table(table_name, schema)
        stmt = update(table).where(table.c[id_column] == id_value).values(**data)
        with self.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()
            return result.rowcount

    def update_where(
        self, table_name: str, where: dict, data: dict, schema: str | None = None
    ):
        table = self.reflect_table(table_name, schema)
        conditions = self._build_conditions(table, where)
        stmt = update(table).where(and_(*conditions)).values(**data)
        with self.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()
            return result.rowcount

    def delete_row(
        self,
        table_name: str,
        id_value,
        id_column: str = "id",
        schema: str | None = None,
    ):
        table = self.reflect_table(table_name, schema)
        stmt = delete(table).where(table.c[id_column] == id_value)
        with self.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()
            return result.rowcount

    def delete_where(self, table_name: str, where: dict, schema: str | None = None):
        table = self.reflect_table(table_name, schema)
        conditions = self._build_conditions(table, where)
        stmt = delete(table).where(and_(*conditions))
        with self.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()
            return result.rowcount

    # ------- Introspection ------- #

    def list_tables(self, schema: str | None = None):
        return self.get_inspector().get_table_names(schema=schema)

    def get_columns(self, table_name: str, schema: str | None = None):
        return self.get_inspector().get_columns(table_name, schema=schema)
