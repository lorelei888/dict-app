import os
os.environ["GEMINI_API_KEY"] = "AIzaSyC6l8kefKOeNOCp-i4ApNV19MwW6KZphL0"

from flask import Flask, render_template, request, jsonify
from google import genai
from dictionaries import DICTIONARIES

app = Flask(__name__)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# ── 主頁面 ──────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", dictionaries=DICTIONARIES)

# ── 搜尋 API ────────────────────────────────────────────────
@app.route("/search")
def search():
    lang  = request.args.get("lang", "en")
    query = request.args.get("q", "").strip().lower()

    if lang not in DICTIONARIES:
        return jsonify({"error": "Unknown language"}), 400

    words = DICTIONARIES[lang]["words"]

    if not query:
        return jsonify({"results": words, "out_of_range": False})

    results = [
        w for w in words
        if query in w["word"].lower() or query in w["short"].lower()
    ]

    out_of_range = len(results) == 0

    return jsonify({
        "results": results,
        "out_of_range": out_of_range,
        "query": query
    })

# ── AI 解釋 API ─────────────────────────────────────────────
@app.route("/explain")
def explain():
    word = request.args.get("word", "")
    lang = request.args.get("lang", "en")

    if not word:
        return jsonify({"error": "No word provided"}), 400

    if lang == "en":
        prompt = (
            f'Give a rich, vivid explanation of the English word "{word}" '
            f"in 3-4 sentences. Include etymology, nuance, and one example sentence."
        )
    else:
        prompt = (
            f'"{word}"라는 한국어 단어에 대해 3~4문장으로 풍부하게 설명해 주세요. '
            f"어원이나 뉘앙스, 예문을 포함해 주세요."
        )

    try:
        response = client.models.generate_content(
         model="gemini-2.0-flash",
            contents=prompt
        )
        explanation = response.text
        return jsonify({"explanation": explanation})

    except Exception as e:
         error_msg = str(e)
         if "quota" in error_msg.lower() or "429" in error_msg:
              return jsonify({"error": "⚠ AI 配額已超過，請明天再試或更換 API Key。"}), 500
         return jsonify({"error": error_msg}), 500

# ── 啟動 ────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)