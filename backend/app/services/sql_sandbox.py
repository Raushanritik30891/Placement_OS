"""Read-only SQLite playground with an isolated in-memory database per request."""
import math
import sqlite3
import time

MAX_QUERY_LENGTH = 4_000
MAX_ROWS = 200
MAX_RESPONSE_CHARS = 200_000
TIME_LIMIT_SECONDS = 2.0

SEED_SQL = """
CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT, city TEXT);
CREATE TABLE orders (order_id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT, amount REAL, status TEXT);
CREATE TABLE employees (employee_id INTEGER PRIMARY KEY, name TEXT, department_id INTEGER, salary INTEGER, joining_date TEXT);
CREATE TABLE departments (department_id INTEGER PRIMARY KEY, department_name TEXT);
INSERT INTO customers VALUES
 (1,'Aarav','Delhi'),(2,'Diya','Pune'),(3,'Kabir','Bengaluru'),(4,'Meera','Delhi');
INSERT INTO orders VALUES
 (101,1,'2026-01-03',1250,'delivered'),(102,1,'2026-01-12',800,'delivered'),
 (103,2,'2026-02-02',2200,'pending'),(104,3,'2026-02-10',1750,'delivered'),
 (105,4,'2026-03-01',990,'cancelled');
INSERT INTO departments VALUES (1,'Engineering'),(2,'Analytics'),(3,'Operations');
INSERT INTO employees VALUES
 (1,'Anaya',1,90000,'2024-06-01'),(2,'Vivaan',1,82000,'2025-01-15'),
 (3,'Sara',2,76000,'2024-11-12'),(4,'Arjun',2,69000,'2025-03-20'),
 (5,'Ishita',3,61000,'2023-08-08');
"""


def execute_readonly_query(query: str) -> dict:
    sql = query.strip()
    if not sql or len(sql) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query must contain 1–{MAX_QUERY_LENGTH} characters.")
    if not (sql.lower().startswith("select") or sql.lower().startswith("with")):
        raise ValueError("Only SELECT queries and read-only CTEs are allowed.")

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        # Bound memory, statement size, expression depth and VM work even for
        # user-authored SELECT expressions such as randomblob()/recursive CTEs.
        limits = [
            ("SQLITE_LIMIT_LENGTH", 65_536),
            ("SQLITE_LIMIT_SQL_LENGTH", MAX_QUERY_LENGTH),
            ("SQLITE_LIMIT_COLUMN", 50),
            ("SQLITE_LIMIT_EXPR_DEPTH", 50),
            ("SQLITE_LIMIT_COMPOUND_SELECT", 10),
            ("SQLITE_LIMIT_VDBE_OP", 50_000),
            ("SQLITE_LIMIT_ATTACHED", 0),
        ]
        for limit_name, limit_value in limits:
            limit_code = getattr(sqlite3, limit_name, None)
            if limit_code is not None:
                connection.setlimit(limit_code, limit_value)

        connection.executescript(SEED_SQL)

        allowed = {
            sqlite3.SQLITE_SELECT,
            sqlite3.SQLITE_READ,
            sqlite3.SQLITE_FUNCTION,
            getattr(sqlite3, "SQLITE_RECURSIVE", -1),
        }

        def authorizer(action, arg1, arg2, database, trigger):
            if action in allowed:
                if action == sqlite3.SQLITE_FUNCTION and (arg2 or arg1 or "").lower() == "load_extension":
                    return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        connection.set_authorizer(authorizer)
        deadline = time.monotonic() + TIME_LIMIT_SECONDS
        connection.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 1_000)
        cursor = connection.execute(sql)
        columns = [item[0] for item in (cursor.description or [])]
        rows = cursor.fetchmany(MAX_ROWS + 1)
        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]
        safe_rows = []
        response_chars = 0
        for row in rows:
            safe_row = []
            for column in columns:
                value = row[column]
                if isinstance(value, bytes):
                    value = "hex:" + value.hex()
                elif isinstance(value, float) and not math.isfinite(value):
                    value = str(value)
                safe_row.append(value)
            row_chars = sum(len(str(value)) for value in safe_row)
            if response_chars + row_chars > MAX_RESPONSE_CHARS:
                truncated = True
                break
            response_chars += row_chars
            safe_rows.append(safe_row)
        return {
            "columns": columns,
            "rows": safe_rows,
            "row_count": len(safe_rows),
            "truncated": truncated,
            "read_only": True,
        }
    except sqlite3.Error as exc:
        message = "Query exceeded the time limit." if "interrupted" in str(exc).lower() else str(exc)
        raise ValueError(message) from exc
    finally:
        connection.close()
