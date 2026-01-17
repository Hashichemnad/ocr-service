import io
from flask import Flask, request, jsonify
import pdfplumber
import pytesseract
import fitz  # PyMuPDF
from PIL import Image

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

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    text = extract_text_from_pdf(file.stream)

    return jsonify({
        "success": True,
        "text": text
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
