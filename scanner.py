import logging
from pathlib import Path
from datetime import datetime
from database import (
    initialize_db,
    save_files_to_db,
    delete_missing_files_from_db,
    count_files_in_db,
    get_files_from_db,
    search_by_extension_db,
    search_by_name_db
)


logging.basicConfig(
    filename="scanner.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


def scan_files(target_dir):
    files = []

    for path in target_dir.rglob("*"):
        try:
            if path.is_file():
                file_info = {
                    "name": path.name,
                    "extension": path.suffix.lower(),
                    "path": str(path),
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime)
                }

                files.append(file_info)

        except (PermissionError, OSError) as error:
            logging.error("読み込み失敗: %s / 理由: %s", path, error)

    return files


def main():
    target_dir = Path(r"C:\Users\deser\Documents")

    logging.info("スキャンを開始します")

    initialize_db()

    files = scan_files(target_dir)

    logging.info("スキャン完了: %d件", len(files))

    save_files_to_db(files)

    delete_missing_files_from_db()

    file_count = count_files_in_db()

    print("DBに保存されているファイル数:", file_count)

    print("1: 拡張子検索")
    print("2: ファイル名検索")

    choice = input("検索方法を選択してください: ")

    if choice == "1":
        search_extension = input("検索する拡張子を入力してください: ").lower()

        if not search_extension.startswith("."):
            search_extension = "." + search_extension

        results = search_by_extension_db(search_extension)    

    elif choice == "2":
        keyword = input("検索するファイル名を入力してください: ")
        results = search_by_name_db(keyword)

    else:
        print("1か2を入力してください。")
        results = []

    if not results:
        print("該当するファイルはありませんでした。")

    else:
        print("検索結果:", len(results), "件")

        for file in results:
            print("ファイル名:", file["name"])
            print("拡張子:", file["extension"])
            print("パス:", file["path"])
            print("サイズ:", file["size"], "bytes")
            print("更新日時:", file["modified"])
            print("-" * 50)        

if __name__ == "__main__":
    main()