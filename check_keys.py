
import sqlite3

conn = sqlite3.connect("dragon_rescue.db")

cursor = conn.cursor()

cursor.execute("""
    SELECT
        COUNT(*),
        COUNT(DISTINCT key_value),
        SUM(is_issued)
    FROM keys
""")

total, unique_total, issued_total = cursor.fetchone()

print("金鑰總數：", total)
print("不重複金鑰數：", unique_total)
print("已發放金鑰數：", issued_total or 0)
print("未發放金鑰數：", total - (issued_total or 0))

conn.close()
