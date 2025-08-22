from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util
import os
from DataBase import *
import torch

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- GLOBALS ---
faq_data = []
faq_embeddings = None
model = None

# --- PARSE .TXT FAQ FILES ---
def load_faq_and_model():
    global faq_data, faq_embeddings, model

    sentence_model_name = os.environ.get("SENTENCE_MODEL", "all-MiniLM-L6-v2")

    # Load Sentence Transformer model
    print(f"--- Loading Sentence Transformer model: {sentence_model_name} ---")
    model = SentenceTransformer(sentence_model_name)

    # Fetch FAQs from database
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, question, answer, keywords, reference FROM faq")
        rows = cursor.fetchall()
        conn.close()

        faq_data = []
        for row in rows:
            faq_data.append({
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "keywords": row[3].split(",") if row[3] else [],
                "reference": row[4] if row[4] else ""
            })

        if not faq_data:
            print("--- WARNING: No FAQ data found in database ---")
            return

        # Create embeddings using question
        questions = [item['question'] for item in faq_data]
        faq_embeddings = model.encode(questions, convert_to_tensor=True)
        print(f"--- Successfully loaded {len(faq_data)} FAQs and created embeddings. ---")

    except Exception as e:
        print(f"--- ERROR loading FAQ data: {e} ---")

# --- ROUTES ---
@app.route("/", methods=["GET"])
def root():
    return render_template('index.html')

@app.route("/ask/", methods=["POST"])
def ask_question():
    global faq_data, faq_embeddings, model

    if not faq_data or faq_embeddings is None:
        return jsonify({"error": "Server not ready."}), 503

    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' field."}), 400

    query = data["query"].strip()
    if not query:
        return jsonify({"error": "Query cannot be empty."}), 400

    query_embedding = model.encode(query, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_embedding, faq_embeddings)[0]
    best_match_index = int(torch.argmax(cos_scores))
    confidence = float(cos_scores[best_match_index])

    SIMILARITY_THRESHOLD = 0.50
    if confidence > SIMILARITY_THRESHOLD:
        return jsonify({
            "answer": faq_data[best_match_index]['answer'],
            "matched_question": faq_data[best_match_index]['question'],
            "confidence": confidence
        })
    else:
        return jsonify({
            "answer": "I am unable to answer that. Please contact us on: 7574949494 or 9099951160.",
            "matched_question": faq_data[best_match_index]['question'],
            "confidence": confidence
        })

if __name__ == "__main__":
    load_faq_and_model()
    app.run(host="0.0.0.0", port=8000, debug=False)