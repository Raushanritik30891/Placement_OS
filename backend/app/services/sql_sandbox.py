"""Read-only SQLite playground with an isolated in-memory database per request."""
import sqlite3
import time

MAX_QUERY_LENGTH = 4_000
MAX_ROWS = 200
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
        return {
            "columns": columns,
            "rows": [[row[column] for column in columns] for row in rows],
            "row_count": len(rows),
            "truncated": truncated,
            "read_only": True,
        }
    except sqlite3.Error as exc:
        message = "Query exceeded the time limit." if "interrupted" in str(exc).lower() else str(exc)
        raise ValueError(message) from exc
    finally:
        connection.close()
