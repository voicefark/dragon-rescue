import json
import random
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = "dragon-rescue-test-key"

DB_FILE = "dragon_rescue.db"
CORRECT_NEEDED = 5

# 正確答案放在後端
ANSWERS = {
    1: "B",
    2: "C"
}


def load_questions():
    with open("questions.json", "r", encoding="utf-8") as file:
        return json.load(file)


def get_db():
    return sqlite3.connect(DB_FILE)


def get_remaining_keys():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM keys WHERE is_issued = 0")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def issue_key():
    """取出一組尚未發放的金鑰，並立即標記為已發放。"""
    conn = get_db()

    try:
        cursor = conn.cursor()

        # 避免兩個請求同時取得同一組金鑰
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT id, key_value
            FROM keys
            WHERE is_issued = 0
            ORDER BY id
            LIMIT 1
        """)

        row = cursor.fetchone()

        if row is None:
            conn.rollback()
            return None

        key_id, key_value = row

        cursor.execute("""
            UPDATE keys
            SET is_issued = 1,
                issued_to = ?,
                issued_at = ?
            WHERE id = ? AND is_issued = 0
        """, (
            session["player_id"],
            datetime.now().isoformat(timespec="seconds"),
            key_id
        ))

        if cursor.rowcount != 1:
            conn.rollback()
            return None

        conn.commit()
        return key_value

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


@app.route("/")
def index():
    questions = load_questions()

    if "player_id" not in session:
        import secrets
        session["player_id"] = secrets.token_hex(16)

    if "attempted" not in session:
        session["attempted"] = []

    attempted = session["attempted"]

    remaining = [
        q for q in questions
        if q["id"] not in attempted
    ]

    # 本輪題目全部作答後，開始新一輪
    if not remaining:
        session["attempted"] = []
        remaining = questions

    question = random.choice(remaining)

    return render_template(
        "index.html",
        question=question,
        correct_count=session.get("correct_count", 0),
        remaining_keys=get_remaining_keys()
    )


@app.route("/answer", methods=["POST"])
def answer():
    questions = load_questions()

    try:
        question_id = int(request.form["question_id"])
    except (KeyError, ValueError):
        return "題目編號不正確。", 400

    user_answer = request.form.get("answer", "")

    question = next(
        (q for q in questions if q["id"] == question_id),
        None
    )

    if question is None:
        return "找不到這道題目。", 400

    attempted = session.get("attempted", [])

    if question_id in attempted:
        return "這道題目已經作答過，請返回首頁。", 400

    # 不論答對或答錯，都記錄本輪已作答
    attempted.append(question_id)
    session["attempted"] = attempted

    correct = user_answer == ANSWERS.get(question_id)
    key_value = None
    message = ""

    if correct:
        session["correct_count"] = session.get("correct_count", 0) + 1
        count = session["correct_count"]

        # 每累積答對 5 題，發放一組金鑰
        if count % CORRECT_NEEDED == 0:
            key_value = issue_key()

            if key_value:
                message = f"恭喜！你已答對 {count} 題，獲得一組救援金鑰！"
            else:
                message = "恭喜達成 5 題里程碑，但金鑰已全部發完，請聯絡活動工作人員。"
        else:
            message = f"答對了！目前累積答對 {count} 題，再答對 {CORRECT_NEEDED - count % CORRECT_NEEDED} 題即可取得下一組金鑰。"

    else:
        message = "答錯了，再接再厲！救援進度不變。"

    return render_template(
        "result.html",
        question=question,
        correct=correct,
        user_answer=user_answer,
        correct_answer=ANSWERS.get(question_id),
        correct_count=session.get("correct_count", 0),
        key_value=key_value,
        message=message,
        remaining_keys=get_remaining_keys()
    )


if __name__ == "__main__":
    app.run(debug=False)