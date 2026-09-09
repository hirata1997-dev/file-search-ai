# File Search AI

ローカルドライブ内のファイルをスキャンし、SQLiteに情報を保存して検索できるシステムです。

将来的には、ファイル名や拡張子だけでなく、PDF・Officeファイル・画像・音声・動画などの内容も解析し、
自然言語で目的のファイルを検索できるローカル検索システムを目指します。


### 現在の機能

- 指定フォルダ以下のファイルを再帰的にスキャン
- `config.json` によるスキャン対象フォルダの設定
- ファイル名、拡張子、パス、サイズ、更新日時を取得
- SQLiteへのファイル情報保存
- 同一パスのファイル情報を更新
- 新規・更新ファイルのみを処理する差分スキャン
- 削除されたファイル情報をDBから削除
- 拡張子による検索
- ファイル名検索
- ファイル内容検索
- SQLite FTS5による全文検索
  - trigram tokenizerによる部分一致検索
  - 3文字未満の検索語はLIKE検索を使用
- ファイル内容の抽出
  - TXTファイル
    - UTF-8
    - CP932
  - PDFファイル
  - Wordファイル（.docx）
    - 通常の段落
    - 表内のテキスト
  - Excelファイル（.xlsx）
    - 各シートのセル内容
- 検索結果件数の表示
- 内容検索時に検索語周辺のスニペットを表示
- スニペット内の検索語を強調表示
- 検索メニューの繰り返し実行
- 空欄・不正な検索入力のチェック
- ファイル読み込みエラー時の継続処理
- ログファイルへの実行状況・エラー記録


## 使用技術

- Python
- SQLite
  - FTS5
  - trigram tokenizer
- pathlib
- logging
- pypdf
- python-docx
- openpyxl


## セットアップ

現在はWindows環境での動作を前提としています。

### 1. リポジトリを取得

```powershell
git clone https://github.com/hirata1997-dev/file-search-ai.git
cd file-search-ai
```

### 2. 仮想環境を作成
```powershell
python -m venv .venv
```

### 3. 必要なライブラリをインストール

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. スキャン対象フォルダを設定
config.example.json をコピーして config.json を作成します。
```powershell
Copy-Item config.example.json config.json
```
作成した config.json の target_dir を、検索対象とするフォルダに変更します。
```JSON
{
    "target_dir": "C:\\Users\\your-name\\Documents"
}
```

## 実行方法

```powershell
.\.venv\Scripts\python.exe scanner.py
```


## 今後の実装予定

- 検索機能の改善
  - 検索結果の並び替え
  - 検索速度の改善
- 自然言語・意味検索
  - Embeddingによるベクトル化
  - ベクトル検索
  - 自然言語による検索条件の解析
- 画像検索
  - 画像の特徴量・内容解析
  - 自然言語による画像検索
- 音声ファイル検索
  - メタデータ取得
  - 音声の文字起こし
- 動画ファイル検索
  - 動画情報の取得
  - 音声・字幕・フレームの解析
- GUIの実装