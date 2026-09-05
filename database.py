import sqlite3
from pathlib import Path


def get_connection():
    """files.dbへのSQLite接続を作成して返す。"""

    return sqlite3.connect("files.db")


def initialize_db():
    """ファイル情報を保存するfilesテーブルを作成する。"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        extension TEXT,
        path TEXT UNIQUE,
        size INTEGER,
        modified TEXT,
        content TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_files_to_db(files):
    """スキャンしたファイル情報をDBへ保存または更新する。"""

    conn = get_connection()
    cursor = conn.cursor()

    for file in files:
        cursor.execute("""
        INSERT INTO files (name, extension, path, size, modified, content)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            name = excluded.name,
            extension = excluded.extension,
            size = excluded.size,
            modified = excluded.modified,
            content = excluded.content
        """, (
            file["name"],
            file["extension"],
            file["path"],
            file["size"],
            str(file["modified"]),
            file["content"]
        ))

    conn.commit()
    conn.close()


def delete_missing_files_from_db():
    """実際には存在しないファイルの情報をDBから削除する。"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT path
    FROM files
    """)

    db_paths = [row[0] for row in cursor.fetchall()]

    # DBに登録されているファイルが現在も存在するか確認
    for path in db_paths:
        try:
            Path(path).stat()

        except FileNotFoundError:
            cursor.execute("""
            DELETE FROM files
            WHERE path = ?
            """, (path,))

        # アクセスできないファイルは削除せず、そのまま残す
        except (PermissionError, OSError):
            continue

    conn.commit()
    conn.close()
    

def count_files_in_db():
    """DBに保存されているファイル件数を返す。"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM files")

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_files_from_db():
    """DBに保存されている全ファイル情報を取得する。"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, extension, path, size, modified, content
    FROM files
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def search_by_extension_db(extension):
    """指定した拡張子と一致するファイルを検索する。"""

    conn = get_connection()

    # 検索結果を列名で参照できるようにする
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
    """ファイル名にキーワードを含むファイルを検索する。"""

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


def search_by_content_db(keyword):
    """ファイル本文にキーワードを含むファイルを検索する。"""

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, extension, path, size, modified, content
    FROM files
    WHERE content LIKE ?
    """, (f"%{keyword}%",))

    rows = cursor.fetchall()

    conn.close()

    return rows