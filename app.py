import os
import json
from flask import Flask, render_template, request, Response
from google import genai
from dictionaries import DICTIONARIES

# ── 初始化 Flask ────────────────────────────────────────────
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 允許回傳中文、韓文等非 ASCII 字元

# ── 初始化 Gemini 客戶端（從 Render 環境變數讀取 Key）──────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

# ── 統一回傳 JSON 的輔助函式 ────────────────────────────────
def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False),
        status=status,
        mimetype="application/json; charset=utf-8"
    )

# ── 主頁面 ──────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", dictionaries=DICTIONARIES)

# ── 搜尋 API ────────────────────────────────────────────────
@app.route("/search")
def search():
    lang  = request.args.get("lang", "en")
    query = request.args.get("q", "").strip().lower()

    # 檢查語言是否存在
    if lang not in DICTIONARIES:
        return json_response({"error": "Unknown language"}, 400)

    words = DICTIONARIES[lang]["words"]

    # 若無搜尋字詞，回傳全部
    if not query:
        return json_response({"results": words, "out_of_range": False})

    # 過濾符合的字詞
    results = [
        w for w in words
        if query in w["word"].lower() or query in w["short"].lower()
    ]

    # 若無結果，標記超出題庫
    return json_response({
        "results": results,
        "out_of_range": len(results) == 0,
        "query": query
    })

# ── AI 解釋 API ─────────────────────────────────────────────
@app.route("/explain")
def explain():
    word = request.args.get("word", "")
    lang = request.args.get("lang", "en")

    if not word:
        return json_response({"error": "No word provided"}, 400)

    # 依語言決定 prompt
    if lang == "en":
        prompt = f'Give a rich explanation of the English word "{word}" in 3-4 sentences. Include etymology, nuance, and one example sentence.'
    else:
        prompt = f'"{word}"라는 한국어 단어에 대해 3~4문장으로 설명해 주세요. 어원이나 뉘앙스, 예문을 포함해 주세요.'

    try:
        # 呼叫 Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return json_response({"explanation": response.text})

    except Exception as e:
        error_msg = str(e)
        # 配額超過的錯誤提示
        if "quota" in error_msg.lower() or "429" in error_msg:
            return json_response({"error": "⚠ AI 配額已超過，請明天再試或更換 API Key。"}, 500)
        return json_response({"error": error_msg}, 500)

# ── 啟動 ────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
