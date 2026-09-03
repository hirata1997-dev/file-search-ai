import sqlite3
from pathlib import Path


def get_connection():
    return sqlite3.connect("files.db")


def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        extension TEXT,
        path TEXT UNIQUE,
        size INTEGER,
        modified TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_files_to_db(files):
    conn = get_connection()
    cursor = conn.cursor()

    for file in files:
        cursor.execute("""
        INSERT INTO files (name, extension, path, size, modified)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            name = excluded.name,
            extension = excluded.extension,
            size = excluded.size,
            modified = excluded.modified
        """, (
            file["name"],
            file["extension"],
            file["path"],
            file["size"],
            str(file["modified"])
        ))

    conn.commit()
    conn.close()


def delete_missing_files_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT path
    FROM files
    """)

    db_paths = [row[0] for row in cursor.fetchall()]

    for path in db_paths:
        try:
            Path(path).stat()

        except FileNotFoundError:
            cursor.execute("""
            DELETE FROM files
            WHERE path = ?
            """, (path,))

        except (PermissionError, OSError):
            continue

    conn.commit()
    conn.close()
    

def count_files_in_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM files")

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_files_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, extension, path, size, modified
    FROM files
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def search_by_extension_db(extension):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, extension, path, size, modified
    FROM files
    WHERE extension = ?
    """, (extension,))

    rows = cursor.fetchall()

    conn.close()

    return rows


def search_by_name_db(keyword):
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, extension, path, size, modified
    FROM files
    WHERE name LIKE ?
    """, (f"%{keyword}%",))

    rows = cursor.fetchall()

    conn.close()

    return rows