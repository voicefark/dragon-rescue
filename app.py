
import json
import random

from flask import Flask, render_template, request, session

# 建立 Flask 網站
app = Flask(__name__)

# 設定 Session 金鑰，供網站暫存每位玩家的答題狀態
app.secret_key = "dragon-rescue-test-key"

# 正確答案放在 Python 後端，不放進網頁
ANSWERS = {
    1: "B",
    2: "C"
}


# 讀取題庫
def load_questions():
    with open("questions.json", "r", encoding="utf-8") as file:
        return json.load(file)


# 首頁：顯示一題尚未作答的題目
@app.route("/")
def index():
    questions = load_questions()

    # 第一次進入網站時，建立作答紀錄
    if "attempted" not in session:
        session["attempted"] = []

    attempted = session["attempted"]

    # 找出尚未作答的題目
    remaining = [
        question for question in questions
        if question["id"] not in attempted
    ]

    # 所有題目都作答過，就重新開始一輪
    if not remaining:
        session["attempted"] = []
        attempted = []
        remaining = questions

    # 隨機抽出一題
    question = random.choice(remaining)

    return render_template(
        "index.html",
        question=question,
        result=None
    )


# 收到玩家的答案
@app.route("/answer", methods=["POST"])
def answer():
    questions = load_questions()

    question_id = int(request.form["question_id"])
    user_answer = request.form.get("answer", "")

    # 找出這次回答的題目
    question = next(
        (q for q in questions if q["id"] == question_id),
        None
    )

    if question is None:
        return "找不到這道題目。", 400

    # 防止同一題被重複提交
    attempted = session.get("attempted", [])

    if question_id in attempted:
        return "這道題目已經作答過，請返回首頁。", 400

    # 不論答對或答錯，都記錄為已作答
    attempted.append(question_id)
    session["attempted"] = attempted

    # 在伺服器端判斷答案
    correct = user_answer == ANSWERS.get(question_id)

    return render_template(
        "result.html",
        question=question,
        correct=correct,
        user_answer=user_answer,
        correct_answer=ANSWERS.get(question_id)
    )


# 啟動網站
if __name__ == "__main__":
    app.run(debug=False)
