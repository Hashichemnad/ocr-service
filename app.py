import os
from flask import Flask, request, jsonify
import base64
import io
import pdfplumber

app = Flask(__name__)

@app.route("/extract", methods=["POST"])
def extract_text():
    data = request.get_json()
    if not data or "fileBase64" not in data:
        return jsonify({"error": "fileBase64 is required"}), 400

    try:
        pdf_bytes = base64.b64decode(data["fileBase64"])
        pdf_stream = io.BytesIO(pdf_bytes)

        extracted_text = ""
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                extracted_text += (page.extract_text() or "") + "\n"

        return jsonify({"text": extracted_text.strip()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
