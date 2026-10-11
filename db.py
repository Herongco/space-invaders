import hashlib
import hmac
import os
import random
import threading
import time

import mysql.connector
from mysql.connector import Error

CODE_EXPIRY_MINUTES = 15
MAX_CODE_ATTEMPTS = 5


def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            database="herongco_space_invaders_db",
            user="root",
            password="",
            connection_timeout=5
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print(f"Database Connection Error: {e}")

    return None


def get_db_connection():
    return create_connection()


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 100_000
    )
    return f"pbkdf2${salt.hex()}${digest.hex()}"


def verify_password(stored, password):
    if not stored:
        return False

    if stored.startswith("pbkdf2$"):
        try:
            _, salt_hex, digest_hex = stored.split("$")
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                100_000
            )
            return hmac.compare_digest(digest.hex(), digest_hex)
        except ValueError:
            return False

    return stored == password


def _hash_code(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def setup_database():
    conn = create_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("SHOW TABLES LIKE 'players'")
        players_exists = cursor.fetchone()

        if not players_exists:
            cursor.execute("""
                CREATE TABLE players (
                    player_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(100) NULL UNIQUE,
                    password VARCHAR(255) NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("SHOW COLUMNS FROM players")
            columns = [row[0] for row in cursor.fetchall()]

            if "email" not in columns:
                cursor.execute("""
                    ALTER TABLE players
                    ADD COLUMN email VARCHAR(100) NULL
                """)

            if "password" not in columns:
                cursor.execute("""
                    ALTER TABLE players
                    ADD COLUMN password VARCHAR(255) NULL
                """)

        cursor.execute("SHOW TABLES LIKE 'scores'")
        scores_exists = cursor.fetchone()

        if not scores_exists:
            cursor.execute("""
                CREATE TABLE scores (
                    score_id INT AUTO_INCREMENT PRIMARY KEY,
                    player_id INT NOT NULL,
                    score INT NOT NULL DEFAULT 0,
                    level INT NOT NULL DEFAULT 1,
                    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id)
                    REFERENCES players(player_id)
                    ON DELETE CASCADE
                )
            """)
        else:
            cursor.execute("SHOW COLUMNS FROM scores")
            score_columns = [row[0] for row in cursor.fetchall()]

            if "date_added" not in score_columns:
                cursor.execute("""
                    ALTER TABLE scores
                    ADD COLUMN date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                """)

            if "level" not in score_columns:
                cursor.execute("""
                    ALTER TABLE scores
                    ADD COLUMN level INT NOT NULL DEFAULT 1
                """)

        cursor.execute("SHOW COLUMNS FROM scores")
        score_columns = [row[0] for row in cursor.fetchall()]

        if "stars" not in score_columns:
            cursor.execute("""
                ALTER TABLE scores
                ADD COLUMN stars TINYINT NOT NULL DEFAULT 0
            """)

        if "completed" not in score_columns:
            cursor.execute("""
                ALTER TABLE scores
                ADD COLUMN completed TINYINT(1) NOT NULL DEFAULT 0
            """)

        cursor.execute("DROP TABLE IF EXISTS email_codes")
        cursor.execute("DROP TABLE IF EXISTS level_progress")

        conn.commit()
        return True

    except Error as e:
        print(f"Database Setup Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


_codes = {}
_codes_lock = threading.Lock()


def create_email_code(email, purpose):
    email = email.strip().lower()
    code = f"{random.SystemRandom().randint(0, 999999):06d}"
    now = time.monotonic()

    with _codes_lock:
        for key in [k for k, v in _codes.items() if v["expires"] < now]:
            del _codes[key]

        _codes[(email, purpose)] = {
            "hash": _hash_code(code),
            "attempts": 0,
            "expires": now + CODE_EXPIRY_MINUTES * 60,
        }

    return code


def verify_email_code(email, purpose, code):
    key = (email.strip().lower(), purpose)

    with _codes_lock:
        entry = _codes.get(key)

        if not entry:
            return False, "NO CODE FOUND. REQUEST A NEW ONE"

        if time.monotonic() > entry["expires"]:
            del _codes[key]
            return False, "CODE EXPIRED. REQUEST A NEW ONE"

        if entry["attempts"] >= MAX_CODE_ATTEMPTS:
            return False, "TOO MANY TRIES. REQUEST A NEW CODE"

        if not hmac.compare_digest(entry["hash"], _hash_code(code)):
            entry["attempts"] += 1
            return False, "WRONG CODE"

        del _codes[key]
        return True, "OK"


def account_exists(username, email):
    conn = get_db_connection()

    if not conn:
        return True, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT player_id FROM players WHERE username = %s",
            (username,)
        )
        if cursor.fetchone():
            return True, "USERNAME ALREADY EXISTS"

        cursor.execute(
            "SELECT player_id FROM players WHERE email = %s",
            (email,)
        )
        if cursor.fetchone():
            return True, "EMAIL ALREADY EXISTS"

        return False, ""

    except Error as e:
        print(f"Account Check Error: {e}")
        return True, "DATABASE ERROR"

    finally:
        cursor.close()
        conn.close()


def email_registered(email):
    conn = get_db_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT player_id FROM players WHERE email = %s",
            (email,)
        )
        return cursor.fetchone() is not None

    except Error as e:
        print(f"Email Check Error: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def register_player(username, email, password):
    if not email or not email.strip():
        return False, "EMAIL IS REQUIRED"

    conn = get_db_connection()

    if not conn:
        return False, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT player_id FROM players WHERE username = %s",
            (username,)
        )

        if cursor.fetchone():
            return False, "USERNAME ALREADY EXISTS"

        cursor.execute(
            "SELECT player_id FROM players WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            return False, "EMAIL ALREADY EXISTS"

        cursor.execute(
            """
            INSERT INTO players
            (username, email, password)
            VALUES (%s, %s, %s)
            """,
            (username, email, hash_password(password))
        )

        conn.commit()

        return True, "ACCOUNT CREATED"

    except Error as e:
        conn.rollback()
        print(f"Registration Error: {e}")
        return False, f"DATABASE ERROR: {e}"

    finally:
        cursor.close()
        conn.close()


def login_player(username_or_email, password):
    conn = get_db_connection()

    if not conn:
        print("Login Error: Database connection failed")
        return None

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                player_id,
                username,
                email,
                password
            FROM players
            WHERE username = %s
            OR email = %s
            """,
            (username_or_email, username_or_email)
        )

        player = cursor.fetchone()

        if not player:
            return None

        stored = player["password"]

        if not verify_password(stored, password):
            return None

        if stored and not stored.startswith("pbkdf2$"):
            cursor.execute(
                "UPDATE players SET password = %s WHERE player_id = %s",
                (hash_password(password), player["player_id"])
            )
            conn.commit()

        player.pop("password", None)

        return player

    except Error as e:
        print(f"Login Error: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def reset_password(email, new_password):
    conn = get_db_connection()

    if not conn:
        return False, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE players SET password = %s WHERE email = %s",
            (hash_password(new_password), email)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return False, "NO ACCOUNT WITH THAT EMAIL"

        return True, "PASSWORD UPDATED"

    except Error as e:
        print(f"Reset Password Error: {e}")
        conn.rollback()
        return False, "DATABASE ERROR"

    finally:
        cursor.close()
        conn.close()


def save_score(player_id, score, level=1, stars=0, completed=False):
    conn = get_db_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO scores
            (player_id, score, level, stars, completed, date_added)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (player_id, score, level, stars, 1 if completed else 0)
        )

        conn.commit()

        return True

    except Error as e:
        print(f"Score Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def load_leaderboard():
    conn = get_db_connection()

    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                p.player_id,
                p.username,
                s.score,
                s.level,
                s.date_added
            FROM players p
            INNER JOIN scores s
                ON s.player_id = p.player_id
            WHERE s.score = (
                SELECT MAX(s2.score)
                FROM scores s2
                WHERE s2.player_id = s.player_id
            )
            ORDER BY s.score DESC,
                     s.date_added DESC
            """
        )

        rows = cursor.fetchall()

        result = []
        used_players = set()

        for row in rows:
            if row["player_id"] not in used_players:
                result.append(row)
                used_players.add(row["player_id"])

            if len(result) == 10:
                break

        return result

    except Error as e:
        print(f"Leaderboard Error: {e}")
        return []

    finally:
        cursor.close()
        conn.close()


def get_player_highest_score(player_id):
    conn = get_db_connection()

    if not conn:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(MAX(score), 0)
            FROM scores
            WHERE player_id = %s
            """,
            (player_id,)
        )

        result = cursor.fetchone()

        if result:
            return result[0]

        return 0

    except Error as e:
        print(f"Highest Score Error: {e}")
        return 0

    finally:
        cursor.close()
        conn.close()


def get_player_highest_level(player_id):
    conn = get_db_connection()

    if not conn:
        return 1

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(MAX(level), 1)
            FROM scores
            WHERE player_id = %s
            """,
            (player_id,)
        )

        result = cursor.fetchone()

        if result and result[0]:
            return result[0]

        return 1

    except Error as e:
        print(f"Highest Level Error: {e}")
        return 1

    finally:
        cursor.close()
        conn.close()


def get_level_best(player_id, level):
    conn = get_db_connection()

    if not conn:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT COALESCE(MAX(score), 0) FROM scores "
            "WHERE player_id = %s AND level = %s",
            (player_id, level)
        )
        row = cursor.fetchone()
        return int(row[0] or 0) if row else 0

    except Error as e:
        print(f"Level Best Error: {e}")
        return 0

    finally:
        cursor.close()
        conn.close()


def load_level_progress(player_id):
    result = {}
    conn = get_db_connection()

    if not conn:
        return result

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT level,
                   MAX(score),
                   MAX(stars),
                   MAX(completed)
            FROM scores
            WHERE player_id = %s
            GROUP BY level
            """,
            (player_id,)
        )

        for level, best, stars, completed in cursor.fetchall():
            result[int(level or 1)] = {
                "best": int(best or 0),
                "stars": int(stars or 0),
                "completed": bool(completed),
            }

    except Error as e:
        print(f"Level Progress Error: {e}")

    finally:
        cursor.close()
        conn.close()

    return result


def get_unlocked_level(player_id, total_levels):
    progress = load_level_progress(player_id)

    completed = [n for n, p in progress.items() if p["completed"]]
    unlocked = (max(completed) + 1) if completed else 1

    unlocked = max(unlocked, int(get_player_highest_level(player_id)))

    return max(1, min(total_levels, unlocked))


def update_player_profile(player_id, new_username, new_email):
    conn = get_db_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT player_id
            FROM players
            WHERE (username = %s OR email = %s)
            AND player_id != %s
            """,
            (new_username, new_email, player_id)
        )

        if cursor.fetchone():
            return False

        cursor.execute(
            """
            UPDATE players
            SET username = %s,
                email = %s
            WHERE player_id = %s
            """,
            (new_username, new_email, player_id)
        )

        conn.commit()

        return True

    except Error as e:
        print(f"Profile Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


_last_error = ""


def get_last_error():
    return _last_error


def delete_player(player_id):
    global _last_error
    _last_error = ""

    if player_id is None:
        _last_error = "NO PLAYER ID"
        print("Delete Error: player_id is None")
        return False

    conn = get_db_connection()

    if not conn:
        _last_error = "NO DATABASE CONNECTION"
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 5")

        cursor.execute(
            """
            SELECT TABLE_NAME, COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE REFERENCED_TABLE_SCHEMA = DATABASE()
            AND REFERENCED_TABLE_NAME = 'players'
            """
        )
        children = cursor.fetchall()

        if not any(t.lower() == "scores" for t, _ in children):
            children.append(("scores", "player_id"))

        for table, column in children:
            cursor.execute(
                f"DELETE FROM `{table}` WHERE `{column}` = %s",
                (player_id,)
            )

        cursor.execute(
            "DELETE FROM players WHERE player_id = %s",
            (player_id,)
        )

        deleted = cursor.rowcount > 0

        if not deleted:
            _last_error = "PLAYER NOT FOUND"
            print(f"Delete Error: no player with id {player_id}")
            conn.rollback()
            return False

        conn.commit()
        return True

    except Exception as e:
        _last_error = str(getattr(e, "msg", e))[:40].upper()
        print(f"Delete Error: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    if setup_database():
        print("DATABASE READY")
    else:
        print("DATABASE SETUP FAILED")