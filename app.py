import os
import pathlib
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import markdown
import pytesseract
from PIL import Image

# ---------------- OCR SETUP ----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------------- GOOGLE API KEY ----------------
# Directly using your key (no .env needed)
api_key = "AIzaSyClrYnz_YfL-QpWp_I6Rp0-Rw9zSGx7_8o"
genai.configure(api_key=api_key)

# ---------------- LOAD PDF (optional) ----------------
file_path = pathlib.Path("20240716890312078.pdf")
if file_path.exists():
    print(f"📄 PDF loaded from {file_path}")
else:
    print(f"⚠️ PDF not found at {file_path}")

# ---------------- CHATBOT SETUP ----------------
model = genai.GenerativeModel("gemini-2.5-flash")
system_prompt = """
You are a professional, friendly constitutional lawyer and legal assistant.
Provide legal guidance in simple language.
"""
chat_history = [{"role": "system", "content": system_prompt}]

# ---------------- FLASK APP ----------------
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")  # Your main website page

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "Please enter a valid question."})

    chat_history.append({"role": "user", "content": user_message})
    conversation = [m["content"] for m in chat_history]

    reply_text = ""
    try:
        response = model.generate_content(conversation)
        if hasattr(response, "text"):
            reply_text = markdown.markdown(response.text)
            reply_text = reply_text.replace('\n', '<br>')
    except Exception as e:
        reply_text = f"Error generating reply: {str(e)}"

    chat_history.append({"role": "assistant", "content": reply_text})
    return jsonify({"reply": reply_text})

# ---------------- OCR PAGE ROUTE ----------------
@app.route("/ocr", methods=["GET", "POST"])
def ocr_page():
    text = ""
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        img = Image.open(file)
        text = pytesseract.image_to_string(img)

    return render_template("ocr.html", text=text)  # Render OCR page on website

# ---------------- RUN FLASK ----------------
if __name__ == "__main__":
    app.run(debug=True)

