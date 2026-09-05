import logging
from pathlib import Path
from datetime import datetime
from database import (
    initialize_db,
    save_files_to_db,
    delete_missing_files_from_db,
    count_files_in_db,
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


def scan_files(target_dir):
    """指定フォルダ以下を再帰的に走査し、ファイル情報と本文を取得する。"""

    files = []

    # 指定フォルダ以下のファイル・フォルダを再帰的に確認
    for path in target_dir.rglob("*"):
        try:
            if path.is_file():

                content = None

                extension = path.suffix.lower()

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
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime),
                    "content": content
                }

                files.append(file_info)

        except (PermissionError, OSError) as error:
            logging.error("読み込み失敗: %s / 理由: %s", path, error)

    return files


def main():
    """ファイルスキャン、DB更新、検索メニューを実行する。"""

    target_dir = Path(r"C:\Users\deser\Documents")

    logging.info("スキャンを開始します")

    # DBの初期化
    initialize_db()

    # ファイル情報と本文を取得
    files = scan_files(target_dir)

    logging.info("スキャン完了: %d件", len(files))

    # スキャン結果をDBへ保存
    save_files_to_db(files)

    # 実際には存在しなくなったファイルをDBから削除
    delete_missing_files_from_db()

    file_count = count_files_in_db()

    print("DBに保存されているファイル数:", file_count)

    print("1: 拡張子検索")
    print("2: ファイル名検索")
    print("3: ファイル内容検索") 

    choice = input("検索方法を選択してください: ")

    if choice == "1":
        search_extension = input("検索する拡張子を入力してください: ").lower()

        # 「txt」のように入力された場合も「.txt」に統一
        if not search_extension.startswith("."):
            search_extension = "." + search_extension

        results = search_by_extension_db(search_extension)    

    elif choice == "2":
        keyword = input("検索するファイル名を入力してください: ")
        results = search_by_name_db(keyword)

    elif choice == "3":
        keyword = input("検索するファイル内容を入力してください: ")
        results = search_by_content_db(keyword)

    else:
        print("1~3を入力してください。")
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