from flask import Flask, request, jsonify
from google import genai
from dotenv import load_dotenv
from functools import lru_cache
from flask_cors import CORS
import os
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("api_key_gemini")

# Initialize Gemini client
client = genai.Client(api_key=api_key)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests


# ----------------------------
# Cached Gemini Question Generator
# ----------------------------
@lru_cache(maxsize=128)
def cached_generate(subject, subtopic, level, num_questions):
    """
    Generate structured JSON questions using Gemini API.
    Each question will NOT include answers or explanations.
    """

    # Build the AI prompt
    prompt = (
        f"Generate exactly {num_questions} Python questions for the subject '{subject}', "
        f"focused on the subtopic '{subtopic}', at {level} difficulty level. "
        "Questions should be a mix of conceptual and practical programming ones. "
        "Return a valid JSON array where each item has keys: 'q_no' and 'question'. "
        "If the question is multiple-choice, include an 'options' array labeled A, B, C, D. "
        "Do NOT include answers or explanations. Only return pure JSON."
    )

    # Call Gemini model
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text or "[]"

    # Try to parse clean JSON safely
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except Exception:
        try:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            data = json.loads(raw[start:end])
            return data
        except Exception:
            return []


# ----------------------------
# API Route: Generate Question Paper (JSON)
# ----------------------------
@app.route('/api/generate-paper', methods=['POST'])
def generate_paper():
    """Generate question paper JSON (clean version)."""
    payload = request.json or {}

    org = payload.get('organization', '').strip()
    subject = payload.get('subject', '').strip()
    subtopic = payload.get('subtopic', '').strip()
    level = payload.get('level', 'Medium').strip()
    num_questions = int(payload.get('num_questions', 10))

    if not org or not subject or not subtopic or num_questions <= 0:
        return jsonify({'error': 'Missing required fields or invalid number of questions'}), 400

    # Generate questions (with cache)
    questions = cached_generate(subject, subtopic, level, num_questions)

    return jsonify({
        'organization': org,
        'subject': subject,
        'subtopic': subtopic,
        'level': level,
        'total_questions': len(questions),
        'questions': questions
    })


# ----------------------------
# Run Flask server
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
