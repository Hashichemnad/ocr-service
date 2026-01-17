from flask import Flask, request, jsonify
import base64
import io
import pdfplumber
import re
import os

app = Flask(__name__)

# ------------------------
# PII MASKING FUNCTION
# ------------------------
def mask_pii(text: str) -> str:
    if not text:
        return text

    # Mask email addresses
    text = re.sub(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        '[EMAIL_REDACTED]',
        text
    )

    # Mask phone numbers (international + local)
    text = re.sub(
        r'(\+?\d[\d\s\-]{7,}\d)',
        '[PHONE_REDACTED]',
        text
    )

    # Mask LinkedIn URLs
    text = re.sub(
        r'https?://(www\.)?linkedin\.com/\S+',
        '[LINKEDIN_REDACTED]',
        text,
        flags=re.IGNORECASE
    )

    return text


@app.route("/extract", methods=["POST"])
def extract_text():

    data = request.get_json()
    if not data or "fileBase64" not in data:
        return jsonify({"error": "fileBase64 is required"}), 400

    try:
        # Decode Base64 → PDF bytes
        pdf_bytes = base64.b64decode(data["fileBase64"])
        pdf_stream = io.BytesIO(pdf_bytes)

        extracted_text = ""
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                extracted_text += (page.extract_text() or "") + "\n"

        # 🔐 MASK PII HERE
        masked_text = mask_pii(extracted_text)

        return jsonify({
            "success": True,
            "text": masked_text.strip()
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
