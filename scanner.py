import json
import logging
from pathlib import Path
from datetime import datetime
from database import (
    initialize_db,
    save_files_to_db,
    delete_missing_files_from_db,
    count_files_in_db,
    get_file_metadata_map,
    search_by_extension_db,
    search_by_name_db,
    search_by_content_db
)
from extractors import (
    read_text_file,
    read_pdf_file,
    read_docx_file,
    read_excel_file
)


# スキャン処理や読み込みエラーをログファイルへ記録
logging.basicConfig(
    filename="scanner.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


def load_target_dir():
    """config.jsonからスキャン対象フォルダを読み込んで返す。"""

    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)

    except FileNotFoundError:
        print("config.json が見つかりません。")
        print("config.example.json を参考に config.json を作成してください。")
        return None

    except json.JSONDecodeError as error:
        print("config.json の形式が正しくありません。")
        print("エラー内容:", error)
        return None

    if "target_dir" not in config:
        print("config.json に target_dir が設定されていません。")
        return None

    target_dir = Path(config["target_dir"])

    if not target_dir.exists():
        print("設定されたスキャン対象フォルダが見つかりません。")
        print("設定値:", target_dir)
        return None

    if not target_dir.is_dir():
        print("設定されたパスはフォルダではありません。")
        print("設定値:", target_dir)
        return None

    return target_dir


def scan_files(target_dir, existing_metadata):
    """指定フォルダ以下を再帰的に走査し、新規・更新ファイルの情報と本文を取得する。"""

    updated_files = []

    # 指定フォルダ以下のファイル・フォルダを再帰的に確認
    for path in target_dir.rglob("*"):
        try:
            if path.is_file():

                content = None

                extension = path.suffix.lower()

                # 現在のファイル情報を取得
                stat = path.stat()
                modified = datetime.fromtimestamp(stat.st_mtime)

                # DBに保存されている前回のファイル情報を取得
                previous_metadata = existing_metadata.get(str(path))

                is_unchanged = (
                    previous_metadata is not None
                    and previous_metadata["modified"] == str(modified)
                    and previous_metadata["size"] == stat.st_size
                )

                # 前回から変更されていないファイルは本文抽出・DB更新をスキップ
                if is_unchanged:
                    continue

                # ファイル形式ごとに検索対象となる本文を抽出
                if extension == ".txt":
                    content = read_text_file(path)

                elif extension == ".pdf":
                    content = read_pdf_file(path)

                elif extension == ".docx":
                    content = read_docx_file(path)

                elif extension == ".xlsx":
                    content = read_excel_file(path)

                # DBへ保存するファイル情報を作成
                file_info = {
                    "name": path.name,
                    "extension": extension,
                    "path": str(path),
                    "size": stat.st_size,
                    "modified": modified,
                    "content": content
                }

                updated_files.append(file_info)

        except (PermissionError, OSError) as error:
            logging.error("読み込み失敗: %s / 理由: %s", path, error)

    return updated_files


def search_files():
    """検索方法を選択し、検索結果を返す。"""

    while True:
        print("1: 拡張子検索")
        print("2: ファイル名検索")
        print("3: ファイル内容検索")
        print("0: 終了")

        choice = input("検索方法を選択してください: ").strip()

        if choice == "1":
            search_extension = input("検索する拡張子を入力してください: ").strip().lower()

            if not search_extension:
                print("拡張子を入力してください。")
                continue

            # 「txt」のように入力された場合も「.txt」に統一
            if not search_extension.startswith("."):
                search_extension = "." + search_extension

            return search_by_extension_db(search_extension)

        elif choice == "2":
            keyword = input("検索するファイル名を入力してください: ").strip()

            if not keyword:
                print("検索語を入力してください。")
                continue

            return search_by_name_db(keyword)

        elif choice == "3":
            keyword = input("検索するファイル内容を入力してください: ").strip()

            if not keyword:
                print("検索語を入力してください。")
                continue

            return search_by_content_db(keyword)

        elif choice == "0":
            return None

        else:
            print("0~3を入力してください。")


def display_search_results(results):
    """検索結果を画面に表示する。"""

    if not results:
        print("該当するファイルはありませんでした。")
        return

    print("検索結果:", len(results), "件")

    for file in results:
        print("ファイル名:", file["name"])
        print("拡張子:", file["extension"])
        print("パス:", file["path"])
        print("サイズ:", file["size"], "bytes")
        print("更新日時:", file["modified"])
        print("-" * 50)


def main():
    """ファイルスキャン、DB更新、検索メニューを実行する。"""

    target_dir = load_target_dir()

    if target_dir is None:
        return

    logging.info("スキャンを開始します")

    # DBの初期化
    initialize_db()

    existing_metadata = get_file_metadata_map()

    # 新規・更新ファイルの情報と本文を取得
    updated_files = scan_files(target_dir, existing_metadata)

    logging.info("更新対象ファイル: %d件", len(updated_files))

    print("新規・更新ファイル数:", len(updated_files))

    # 新規・更新ファイルをDBへ保存
    save_files_to_db(updated_files)

    # 実際には存在しなくなったファイルをDBから削除
    delete_missing_files_from_db()

    file_count = count_files_in_db()

    print("DBに保存されているファイル数:", file_count)

    while True:
        results = search_files()

        if results is None:
            print("検索を終了します。")
            break

        display_search_results(results)


if __name__ == "__main__":
    main()