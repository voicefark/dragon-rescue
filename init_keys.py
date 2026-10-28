
import secrets
import sqlite3
import string

# 金鑰資料庫檔案
DB_FILE = "dragon_rescue.db"

# 預先產生的金鑰數量
KEY_COUNT = 100

# 每組金鑰的長度
KEY_LENGTH = 8

# 使用英文字母與數字
CHARACTERS = string.ascii_uppercase + string.digits


def generate_key():
    """使用安全亂數產生一組 8 位英數字金鑰。"""
    return "".join(
        secrets.choice(CHARACTERS)
        for _ in range(KEY_LENGTH)
    )


def initialize_database():
    # 建立資料庫連線
    conn = sqlite3.connect(DB_FILE)

    try:
        cursor = conn.cursor()

        # 建立金鑰資料表
        # UNIQUE 確保資料庫中不會有重複金鑰
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_value TEXT NOT NULL UNIQUE,
                is_issued INTEGER NOT NULL DEFAULT 0,
                issued_to TEXT,
                issued_at TEXT
            )
        """)

        # 查詢目前已有多少組金鑰
        cursor.execute("SELECT COUNT(*) FROM keys")
        existing_count = cursor.fetchone()[0]

        # 只補足到 100 組，不刪除既有金鑰
        while existing_count < KEY_COUNT:
            key_value = generate_key()

            try:
                cursor.execute(
                    "INSERT INTO keys (key_value) VALUES (?)",
                    (key_value,)
                )
                existing_count += 1

            except sqlite3.IntegrityError:
                # 如果剛好重複，重新產生即可
                continue

        conn.commit()

        print("資料庫初始化完成！")
        print(f"目前金鑰總數：{existing_count}")
        print(f"金鑰長度：{KEY_LENGTH}")
        print("金鑰字元：大寫英文字母與數字")
        print(f"資料庫位置：{DB_FILE}")

    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
