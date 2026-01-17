import io
from flask import Flask, request, jsonify
import pdfplumber
import pytesseract
import fitz  # PyMuPDF
from PIL import Image

import re

app = Flask(__name__)

def extract_text_from_pdf(file_stream):
    text = ""

    # 1️⃣ Try text-based extraction first (FAST)
    try:
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass

    # If text found, return it
    if text.strip():
        return text.strip()

    # 2️⃣ Fallback to OCR (scanned PDFs)
    file_stream.seek(0)
    pdf = fitz.open(stream=file_stream.read(), filetype="pdf")

    for page in pdf:
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text += pytesseract.image_to_string(img)

    return text.strip()

def mask_pii(text: str) -> str:
    if not text:
        return text

    # 1️⃣ Emails
    text = re.sub(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        '[EMAIL_REMOVED]',
        text
    )

    # 2️⃣ Phone numbers (international + local)
    text = re.sub(
        r'(\+?\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}',
        '[PHONE_REMOVED]',
        text
    )

    # 3️⃣ LinkedIn URLs
    text = re.sub(
        r'linkedin\.com\/[^\s]+',
        '[LINKEDIN_REMOVED]',
        text,
        flags=re.IGNORECASE
    )

    # 4️⃣ Other URLs
    text = re.sub(
        r'(http|https):\/\/[^\s]+',
        '[URL_REMOVED]',
        text
    )

    # 5️⃣ Remove name line (heuristic)
    lines = text.splitlines()
    cleaned_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Heuristic: first non-empty line with 2–4 capitalized words
        if i < 3 and re.match(r'^([A-Z][a-z]+ ){1,3}[A-Z][a-z]+$', stripped):
            continue  # likely candidate name

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    return text.strip()

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    text = extract_text_from_pdf(file.stream)

    masked_text = mask_pii(text)
    
    return jsonify({
        "success": True,
        "text": masked_text
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
