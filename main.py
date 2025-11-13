from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import base64, io, pdfplumber, re

# ---------------- BASIC CONFIG ----------------
app = FastAPI(title="7Lines Engineering AI – Dubai Building Code Compliance Checker")
client = OpenAI()  # requires OPENAI_API_KEY in environment variable

# Allow frontend (like Wix) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow Wix iframe
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
      <head>
        <title>7Lines Engineering AI</title>
        <style>
          body {
            background-color: #b30000;
            color: white;
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 60px;
          }
          h1 { font-size: 2.4em; }
          p { font-size: 1.1em; }
          a {
            background-color: white;
            color: #b30000;
            text-decoration: none;
            padding: 10px 15px;
            border-radius: 5px;
            font-weight: bold;
          }
          a:hover { background-color: #f5f5f5; }
          .endpoint {
            background: rgba(255,255,255,0.1);
            margin: 20px auto;
            max-width: 600px;
            padding: 20px;
            border-radius: 8px;
          }
        </style>
      </head>
      <body>
        <h1>🏗️ 7Lines Engineering AI</h1>
        <p>Dubai Building Code Compliance Assistant</p>
        <div class="endpoint">
          <h3>🔍 Analyze Building Plan</h3>
          <p><b>POST</b> /analyze</p>
          <p>Uploads a PDF plan and checks it against the Dubai Building Code 2021 and Permit Checklist.</p>
        </div>
        <div class="endpoint">
          <h3>💬 AI Chat Assistant</h3>
          <p><b>POST</b> /chat</p>
          <p>Ask about DBC rules, ramp slopes, accessibility, or checklist compliance.</p>
        </div>
        <a href="https://dm.gov.ae/wp-content/uploads/2021/12/Dubai%20Building%20Code_English_2021%20Edition_compressed.pdf" target="_blank">
          📘 View Dubai Building Code 2021
        </a>
      </body>
    </html>
    """

# ---------------- /analyze ----------------
@app.post("/analyze")
async def analyze(request: Request):
    """Analyze uploaded PDF (base64) and evaluate compliance with the Permit Checklist."""
    try:
        data = await request.json()
        file_data = data.get("file_data")
        if not file_data:
            return {"status": "error", "message": "No file data received."}

        # Decode Base64 and read PDF
        pdf_bytes = base64.b64decode(file_data)
        pdf_text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:8]:  # Read up to 8 pages
                pdf_text += page.extract_text() or ""

        pdf_text = pdf_text.lower()

        # Simulated Permit Checklist Rules (based on your Permit Checklist)
        checklist = [
            {"code": "E6", "criteria": "door width ≥ 900mm", "regex": r"door.*(900|1\.0|1000)"},
            {"code": "LCR2", "criteria": "ramp slope ≤ 8%", "regex": r"ramp.*(1[:/]\s*12|8\s*%)"},
            {"code": "PE1", "criteria": "path width ≥ 1800mm", "regex": r"path.*(1800|1\.8)"},
            {"code": "SPpt", "criteria": "accessible toilet available", "regex": r"toilet|wc|accessible"},
            {"code": "PA1", "criteria": "parking within 50m", "regex": r"parking.*(50|fifty)"},
            {"code": "GD3", "criteria": "handrail height ≥ 900mm", "regex": r"handrail.*(900|1\.0|1000)"},
            {"code": "GS", "criteria": "stair width ≥ 1200mm", "regex": r"stair.*(1200|1\.2)"},
            {"code": "PE7", "criteria": "no abrupt level changes", "regex": r"level.*change"},
            {"code": "SPsh", "criteria": "shower turning radius ≥1500mm", "regex": r"shower.*(1500|1\.5)"},
            {"code": "LCH1", "criteria": "guardrail height ≥1100mm", "regex": r"guardrail.*(1100|1\.1)"}
        ]

        failed_checks = []
        passed = 0
        for rule in checklist:
            if re.search(rule["regex"], pdf_text):
                passed += 1
            else:
                failed_checks.append({"code": rule["code"], "description": f"Missing or non-compliant: {rule['criteria']}"})

        total = len(checklist)
        pass_rate = int((passed / total) * 100)

        return {
            "status": "ok",
            "pass_rate": pass_rate,
            "failed": failed_checks
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------- /chat ----------------
@app.post("/chat")
async def chat(request: Request):
    """AI chat about Dubai Building Code and compliance."""
    data = await request.json()
    message = data.get("message", "")
    dbc_ref = (
        "https://dm.gov.ae/wp-content/uploads/2021/12/"
        "Dubai%20Building%20Code_English_2021%20Edition_compressed.pdf"
    )

    prompt = f"""
    You are an AI Building Compliance Engineer using the Dubai Building Code 2021 ({dbc_ref}).
    Answer clearly and professionally, citing code sections when possible.
    Question: {message}
    """

    try:
        response = client.responses.create(model="gpt-5", input=prompt)
        return {"reply": response.output[0].content[0].text}
    except Exception as e:
        return {"reply": f"⚠️ AI could not process your question: {e}"}

# ---------------- /test ----------------
@app.get("/test")
def test():
    return {"status": "ok", "message": "Server running and OpenAI ready."}
