"""本地员工账号存储和内部演示用的签名令牌。"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "employees.sqlite3"
TOKEN_TTL_SECONDS = 60 * 60 * 8
PBKDF2_ITERATIONS = 310_000
_DEV_SECRET = "development-only-change-this-secret-before-deployment"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_auth_db():
    with _connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                display_name TEXT NOT NULL,
                department TEXT NOT NULL,
                job_level TEXT NOT NULL,
                position TEXT NOT NULL,
                hire_date TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def _password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)


def _public_user(row):
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "department": row["department"],
        "job_level": row["job_level"],
        "position": row["position"],
        "hire_date": row["hire_date"],
        "role": row["role"],
    }


def create_employee(*, username, password, display_name, department, job_level, position, hire_date, role="employee"):
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long")
    if role not in {"admin", "employee"}:
        raise ValueError("Role must be admin or employee")
    required_values = (username, display_name, department, job_level, position)
    if any(not value.strip() for value in required_values):
        raise ValueError("Username and employee profile fields cannot be blank")

    salt = secrets.token_bytes(16)
    password_hash = _password_hash(password, salt)
    try:
        with _connect() as db:
            cursor = db.execute(
                """INSERT INTO employees
                (username, password_hash, password_salt, display_name, department, job_level, position, hire_date, role)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (username.strip(), password_hash.hex(), salt.hex(), display_name.strip(), department.strip(),
                 job_level.strip(), position.strip(), hire_date.isoformat(), role),
            )
            row = db.execute("SELECT * FROM employees WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return _public_user(row)
    except sqlite3.IntegrityError as exc:
        raise ValueError("Username already exists") from exc


def authenticate(username: str, password: str):
    with _connect() as db:
        row = db.execute("SELECT * FROM employees WHERE username = ? COLLATE NOCASE", (username.strip(),)).fetchone()
    if row is None:
        # 对不存在的账号也执行密码哈希，降低账号枚举时的耗时差异。
        _password_hash(password, bytes(16))
        return None
    actual = _password_hash(password, bytes.fromhex(row["password_salt"]))
    if not hmac.compare_digest(actual.hex(), row["password_hash"]) or not row["active"]:
        return None
    return _public_user(row)


def _secret() -> bytes:
    return os.environ.get("EMPLOYEE_AUTH_SECRET", _DEV_SECRET).encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def issue_token(user: dict) -> str:
    payload = json.dumps({"sub": user["id"], "exp": int(time.time()) + TOKEN_TTL_SECONDS}).encode("utf-8")
    body = _b64(payload)
    signature = hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64(signature)}"


def get_user_from_token(token: str):
    try:
        body, encoded_signature = token.split(".", 1)
        signature = base64.urlsafe_b64decode(encoded_signature + "=" * (-len(encoded_signature) % 4))
        expected = hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        claims = json.loads(payload)
        if claims["exp"] < int(time.time()):
            return None
        with _connect() as db:
            row = db.execute("SELECT * FROM employees WHERE id = ? AND active = 1", (claims["sub"],)).fetchone()
        return _public_user(row) if row else None
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def list_employees():
    with _connect() as db:
        rows = db.execute(
            "SELECT * FROM employees ORDER BY department, display_name"
        ).fetchall()
    return [_public_user(row) for row in rows]
