
import os
import pathlib
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import markdown
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Load API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")

# Configure GenAI
genai.configure(api_key=api_key)

# Load Indian Constitution PDF from local path
file_path = pathlib.Path("20240716890312078.pdf")
if not file_path.exists():
    raise FileNotFoundError(f"PDF not found at {file_path}")
print(f"📄 PDF loaded from {file_path}")

# Create model instance
# Use Gemini 2.5 Flash for the fastest, most capable, and highest quality chat (no cost concern)
model = genai.GenerativeModel("gemini-2.5-flash")

# Initial system instruction
system_prompt = """

You are a professional, friendly constitutional lawyer and legal assistant who helps people with little legal knowledge.



For the first message, greet the user and provide a clear, bolded instruction like this:

<strong>To help you best, please briefly describe your situation or question in your own words.</strong><br>
<strong>Include:</strong><br>
<strong>What happened?</strong> (Who did what to whom, when, and where?)<br>
<strong>What outcome are you hoping for?</strong><br>


After the first message, ask only one clear, relevant follow-up question at a time, based on what the user shared. Do not overwhelm them with multiple questions.

Format your replies for clarity: use short paragraphs, bold for important points, and lists if helpful.
If the user is unsure, gently suggest what kind of information would help, but keep it conversational and encouraging.
Always use plain, simple language—avoid legal jargon.
Give practical, actionable advice tailored to the user's specific situation.

Whenever possible, suggest and link to official, trusted legal resources, government portals, or up-to-date legal documents to help the user further. Provide the most accurate and current information available.



If the user's question is out of context (not related to legal issues, law, or justice in India), reply clearly and politely:
<br><strong>Sorry, I can only provide legal support. Please ask a question related to law, legal rights, or justice in India.</strong><br>
Do not attempt to answer unrelated questions.

You can help with:
<ul>
    <li>Legal rights and duties</li>
    <li>Legal procedures and remedies</li>
    <li>How to approach courts or authorities</li>
    <li>Understanding laws, acts, and legal documents</li>
    <li>General legal advice for common situations</li>
</ul>

Keep the conversation natural, step-by-step, and supportive. Only ask for more details if truly needed to help the user.
"""

# Flask app
app = Flask(__name__)

# Keep chat history
chat_history = [{"role": "system", "content": system_prompt}]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "Please enter a valid question."})

    chat_history.append({"role": "user", "content": user_message})
    conversation = [m["content"] for m in chat_history]


    reply_text = ""
    response = model.generate_content(conversation)
    if hasattr(response, "text"):
        # Convert Markdown to HTML for proper rendering
        reply_text = markdown.markdown(response.text)
        # Ensure newlines are preserved as <br> if markdown doesn't add them
        reply_text = reply_text.replace('\n', '<br>')

    chat_history.append({"role": "assistant", "content": reply_text})

    return jsonify({"reply": reply_text})

@app.route("/ocr", methods=["GET", "POST"])
def ocr_page():
    text = ""
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        # Open the image and extract text
        img = Image.open(file)
        text = pytesseract.image_to_string(img)

        return jsonify({"ocr_text": text})

    # For GET request, show a simple upload form
    return '''
        <h2>Upload an Image for OCR</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*">
            <input type="submit" value="Upload">
        </form>
    '''

if __name__ == "__main__":
    app.run(debug=True)

