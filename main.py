from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import base64, io, pdfplumber

# ---------- BASIC SETUP ----------
app = FastAPI()
client = OpenAI()   # requires OPENAI_API_KEY in environment

# allow Wix and browsers to reach it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- SIMPLE /analyze ENDPOINT ----------
@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    filename = data.get("filename", "uploaded.pdf")
    file_data = data.get("file_data")

    if not file_data:
        return {"status": "error", "message": "No file data received"}

    # Decode the base64 PDF
    pdf_bytes = base64.b64decode(file_data)
    pdf_text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:5]:   # limit for performance
            pdf_text += page.extract_text() or ""

    # Ask AI to check plan text against DBC 2021
    prompt = f"""
    You are a Dubai Municipality Building Code Compliance Engineer.
    The user uploaded a building plan in text form below.

    Analyze the plan for compliance with the Dubai Building Code (2021).
    Mention any violations and summarize clearly.

    Uploaded Plan:
    {pdf_text[:6000]}
    """

    response = client.responses.create(model="gpt-5", input=prompt)
    summary = response.output[0].content[0].text

    return {
        "status": "ok",
        "decision": "⚠️ Needs Review",
        "summary": summary,
        "issues": [],
    }

# ---------- /chat ENDPOINT ----------
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_msg = data.get("message", "")

    dbc_ref = "https://dm.gov.ae/wp-content/uploads/2021/12/Dubai%20Building%20Code_English_2021%20Edition_compressed.pdf"

    prompt = f"""
    You are an AI Building Code Consultant using the Dubai Building Code 2021 ({dbc_ref}).
    Answer the user's question clearly, citing relevant sections.

    Question: {user_msg}
    """

    response = client.responses.create(model="gpt-5", input=prompt)
    answer = response.output[0].content[0].text

    return {"reply": answer}

# ---------- HEALTH CHECK ----------
@app.get("/test")
def test():
    return {"status": "ok", "message": "Server running and OpenAI ready."}
