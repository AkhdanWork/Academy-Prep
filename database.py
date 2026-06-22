import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(os.environ.get("ACADEMY_DB_PATH", "data/academy_prep.db"))
PASSWORD_ITERATIONS = 600_000
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with _connect() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_key TEXT NOT NULL UNIQUE,
                score REAL NOT NULL,
                correct INTEGER NOT NULL,
                incorrect INTEGER NOT NULL,
                unanswered INTEGER NOT NULL,
                total INTEGER NOT NULL,
                duration_seconds INTEGER NOT NULL,
                finish_reason TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS section_results (
                attempt_id INTEGER NOT NULL,
                section TEXT NOT NULL,
                correct INTEGER NOT NULL,
                total INTEGER NOT NULL,
                PRIMARY KEY (attempt_id, section),
                FOREIGN KEY (attempt_id) REFERENCES attempts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS answer_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                section TEXT NOT NULL,
                concept TEXT,
                question TEXT NOT NULL,
                user_answer TEXT,
                correct_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                FOREIGN KEY (attempt_id) REFERENCES attempts(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_attempts_user
                ON attempts(user_id, completed_at);
            CREATE INDEX IF NOT EXISTS idx_answers_attempt
                ON answer_results(attempt_id);
            """
        )


def normalize_email(email):
    return email.strip().lower()


def validate_registration(name, email, password):
    name = name.strip()
    email = normalize_email(email)
    if len(name) < 2:
        return "Nama minimal 2 karakter."
    if len(name) > 80:
        return "Nama maksimal 80 karakter."
    if not EMAIL_PATTERN.match(email):
        return "Format email belum valid."
    if len(password) < 8:
        return "Password minimal 8 karakter."
    if not any(character.isalpha() for character in password):
        return "Password harus memiliki setidaknya satu huruf."
    if not any(character.isdigit() for character in password):
        return "Password harus memiliki setidaknya satu angka."
    return None


def _hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return (
        base64.b64encode(password_hash).decode("ascii"),
        base64.b64encode(salt).decode("ascii"),
    )


def create_user(name, email, password):
    validation_error = validate_registration(name, email, password)
    if validation_error:
        return None, validation_error

    email = normalize_email(email)
    password_hash, password_salt = _hash_password(password)
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        with _connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (name, email, password_hash, password_salt, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name.strip(), email, password_hash, password_salt, created_at),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return None, "Email sudah terdaftar. Silakan masuk."

    return {"id": user_id, "name": name.strip(), "email": email}, None


def authenticate_user(email, password):
    email = normalize_email(email)
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, name, email, password_hash, password_salt
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    if row is None:
        return None

    salt = base64.b64decode(row["password_salt"])
    candidate_hash, _ = _hash_password(password, salt)
    if not hmac.compare_digest(candidate_hash, row["password_hash"]):
        return None

    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def save_attempt(user_id, session_key, summary, sections, answers):
    with _connect() as connection:
        existing = connection.execute(
            "SELECT id FROM attempts WHERE session_key = ?", (session_key,)
        ).fetchone()
        if existing:
            return existing["id"]

        cursor = connection.execute(
            """
            INSERT INTO attempts (
                user_id, session_key, score, correct, incorrect, unanswered,
                total, duration_seconds, finish_reason, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_key,
                summary["score"],
                summary["correct"],
                summary["incorrect"],
                summary["unanswered"],
                summary["total"],
                summary["duration_seconds"],
                summary["finish_reason"],
                summary["started_at"],
                summary["completed_at"],
            ),
        )
        attempt_id = cursor.lastrowid

        connection.executemany(
            """
            INSERT INTO section_results (attempt_id, section, correct, total)
            VALUES (?, ?, ?, ?)
            """,
            [
                (attempt_id, section, values["correct"], values["total"])
                for section, values in sections.items()
            ],
        )
        connection.executemany(
            """
            INSERT INTO answer_results (
                attempt_id, section, concept, question, user_answer,
                correct_answer, is_correct
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    attempt_id,
                    answer["section"],
                    answer.get("concept"),
                    answer["question"],
                    answer.get("user_answer"),
                    answer["correct_answer"],
                    int(answer["is_correct"]),
                )
                for answer in answers
            ],
        )
        return attempt_id


def get_attempts(user_id):
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, score, correct, incorrect, unanswered, total,
                   duration_seconds, finish_reason, started_at, completed_at
            FROM attempts
            WHERE user_id = ?
            ORDER BY completed_at ASC, id ASC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_section_performance(user_id):
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT sr.section,
                   SUM(sr.correct) AS correct,
                   SUM(sr.total) AS total,
                   COUNT(*) AS attempts
            FROM section_results sr
            JOIN attempts a ON a.id = sr.attempt_id
            WHERE a.user_id = ?
            GROUP BY sr.section
            ORDER BY (SUM(sr.correct) * 1.0 / SUM(sr.total)) DESC, sr.section
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_concept_performance(user_id):
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT ar.concept,
                   SUM(ar.is_correct) AS correct,
                   COUNT(*) AS total
            FROM answer_results ar
            JOIN attempts a ON a.id = ar.attempt_id
            WHERE a.user_id = ?
              AND ar.concept IS NOT NULL
              AND TRIM(ar.concept) != ''
            GROUP BY ar.concept
            HAVING COUNT(*) >= 1
            ORDER BY (SUM(ar.is_correct) * 1.0 / COUNT(*)) ASC, COUNT(*) DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]
