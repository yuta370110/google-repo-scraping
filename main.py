import sqlite3
import time
import requests
from bs4 import BeautifulSoup

# 1. データベースの準備（SQLite）
db_name = "google_repos.db"
conn = sqlite3.connect(db_name)
cur = conn.cursor()

# テーブル作成（既存の同名テーブルがあれば作り直す例）
cur.execute("DROP TABLE IF EXISTS repositories")
cur.execute("""
    CREATE TABLE repositories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        language TEXT,
        stars TEXT
    )
""")

# 2. スクレイピング処理（全ページ取得）
base_url = "https://github.com/orgs/google/repositories"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

page = 1
while True:
    print(f"{page}ページ目を取得中...")
    url = f"{base_url}?page={page}"
    response = requests.get(url, headers=headers)
    
    # ページが存在しない、またはエラーの場合は終了
    if response.status_code != 200:
        break

    soup = BeautifulSoup(response.text, "html.parser")
    
    # リポジトリ一覧の各ブロックを取得（※GitHubのHTML仕様に合わせて要確認）
    repo_items = soup.select("li.Box-row") # または div[data-testid="list-view-item"] など
    
    # リポジトリが1件も取得できなくなったら最終ページと判断してループ終了
    if not repo_items:
        print("全ページの取得が完了しました。")
        break

    for item in repo_items:
        # リポジトリ名の取得
        name_tag = item.select_one("a[data-testid='listitem-title-link']") or item.select_one("h3 a")
        name = name_tag.get_text(strip=True) if name_tag else "不明"

        # 主要な言語の取得（言語設定がないリポジトリもあるため考慮）
        lang_tag = item.select_one("span[itemprop='programmingLanguage']")
        language = lang_tag.get_text(strip=True) if lang_tag else "None"

        # スター数の取得
        star_tag = item.select_one("a[href$='/stargazers']")
        stars = star_tag.get_text(strip=True) if star_tag else "0"

        # DBへ挿入
        cur.execute(
            "INSERT INTO repositories (name, language, stars) VALUES (?, ?, ?)",
            (name, language, stars)
        )

    conn.commit()
    page += 1
    
    # サーバー負荷軽減のための待機（課題の必須要件）
    time.sleep(1)

# 3. 保存したデータをSELECT文で表示
print("\n--- 保存されたデータ一覧（先頭20件） ---")
cur.execute("SELECT * FROM repositories LIMIT 20")
rows = cur.fetchall()
for row in rows:
    print(row)

# 総件数の確認
cur.execute("SELECT COUNT(*) FROM repositories")
total = cur.fetchone()[0]
print(f"\n合計取得件数: {total}件")

conn.close()