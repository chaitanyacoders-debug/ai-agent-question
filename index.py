from flask import Flask, request, send_file, jsonify
from google import genai
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os
import io

# Load environment variables
load_dotenv()
api_key = os.getenv("api_key_gemini")

# Initialize Gemini client
client = genai.Client(api_key=api_key)

# Create Flask app
app = Flask(__name__)

@app.route("/generate-paper", methods=["POST"])
def generate_paper():
    try:
        # Step 1: Get input data from JSON
        data = request.get_json()
        subject = data.get("subject")
        hardness = data.get("level")
        num_questions = data.get("num_questions")
        org_name = data.get("organization")

        if not all([subject, hardness, num_questions, org_name]):
            return jsonify({"error": "Missing required fields"}), 400

        # Step 2: Generate content using Gemini
        prompt = (
            f"Create a {hardness} level question paper in {subject} with {num_questions} questions. "
            f"Each question should be numbered and relevant to {subject}."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text or "No response from model."

        # Step 3: Generate PDF (in memory)
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4

        # Add organization name as heading
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, height - inch, f"{org_name}")
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height - inch - 20, f"Subject: {subject} | Level: {hardness}")
        c.line(inch, height - inch - 30, width - inch, height - inch - 30)

        # Add generated content
        c.setFont("Helvetica", 12)
        y = height - 1.5 * inch
        lines = text.split("\n")
        for line in lines:
            if y < inch:  # Add new page if text exceeds the page
                c.showPage()
                y = height - inch
                c.setFont("Helvetica", 12)
            c.drawString(inch, y, line)
            y -= 18  # line spacing

        c.save()
        pdf_buffer.seek(0)

        # Step 4: Return the PDF as a response
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{subject}_Question_Paper.pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run Flask server
if __name__ == "__main__":
    app.run(debug=True)
