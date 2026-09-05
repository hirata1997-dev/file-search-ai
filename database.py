import sqlite3
from pathlib import Path


def get_connection():
    """files.dbへのSQLite接続を作成して返す。"""

    return sqlite3.connect("files.db")


def fetch_all_rows(query, params=()):
    """SQLを実行し、取得したすべての行を列名付きで返す。"""

    conn = get_connection()
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(query, params)

    rows = cursor.fetchall()

    conn.close()

    return rows


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
    
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS files_fts
    USING fts5(
        name,
        content,
        path UNINDEXED,
        tokenize='trigram'
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

        cursor.execute("""
        DELETE FROM files_fts
        WHERE path = ?
        """, (
            file["path"],
        ))

        cursor.execute("""
        INSERT INTO files_fts (name, content, path)
        VALUES (?, ?, ?)
        """, (
            file["name"],
            file["content"],
            file["path"]
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

            cursor.execute("""
            DELETE FROM files_fts
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

    return fetch_all_rows("""
    SELECT name, extension, path, size, modified
    FROM files
    WHERE extension = ?
    """, (extension,))


def search_by_name_db(keyword):
    """検索語の長さに応じてLIKE検索とFTS5検索を使い分ける。"""

    if len(keyword) < 3:
        return fetch_all_rows("""
        SELECT name, extension, path, size, modified
        FROM files
        WHERE name LIKE ?
        """, (f"%{keyword}%",))

    return fetch_all_rows("""
    SELECT
        files.name,
        files.extension,
        files.path,
        files.size,
        files.modified
    FROM files_fts
    JOIN files
        ON files_fts.path = files.path
    WHERE files_fts.name MATCH ?
    """, (keyword,))


def search_by_content_db(keyword):
    """検索語の長さに応じてLIKE検索とFTS5検索を使い分ける。"""

    if len(keyword) < 3:
        return fetch_all_rows("""
        SELECT name, extension, path, size, modified, content
        FROM files
        WHERE content LIKE ?
        """, (f"%{keyword}%",))

    return fetch_all_rows("""
    SELECT
        files.name,
        files.extension,
        files.path,
        files.size,
        files.modified,
        files.content
    FROM files_fts
    JOIN files
        ON files_fts.path = files.path
    WHERE files_fts.content MATCH ?
    """, (keyword,))