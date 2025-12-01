from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


genai = None
genai_import_error = None
try:
    from google import genai
    from google.genai import types
except ImportError as e:
    genai_import_error = str(e)


TABSCANNER_API_KEY = os.getenv("TABSCANNER_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

GEN_MODEL_NAME = "gemini-2.5-flash" 


app = FastAPI(title="Tabscanner + Gemini Transaction Filler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROCESS_URL = "https://api.tabscanner.com/api/2/process"
RESULT_URL = "https://api.tabscanner.com/api/result/"


def call_gemini(model_name: str, prompt: str):
    """
    Calls the Gemini API using the modern 'google-genai' SDK.
    """
    if genai is None:
        if os.getenv("SKIP_GEMINI") in ("1", "true", "True"):
            return _get_stub_response()
            
        raise RuntimeError(
            "The 'google-genai' library is not installed.\n"
            f"Error: {genai_import_error}\n"
            "Please run: pip install google-genai"
        )

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        generate_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=1000
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=generate_config
        )
        return response
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")

def _get_stub_response():
    """Helper for local testing without API usage"""
    stub = {
        "transaction_type": "Expense",
        "amount": 0.0,
        "account": "personal",
        "category": "uncategorized",
        "date": None,
        "description": "(stubbed response)",
        "is_recurring": False,
    }
    class Stub:
        text = json.dumps(stub)
    return Stub()


@app.post("/upload/")
async def upload_and_fill(file: UploadFile = File(...)):
    try:
        img_bytes = await file.read()
        process_resp = requests.post(
            PROCESS_URL,
            headers={"apikey": TABSCANNER_API_KEY},
            files={"file": (file.filename, img_bytes)}
        )

        if process_resp.status_code != 200:
            return JSONResponse(content={"error": f"Tabscanner Error: {process_resp.text}"}, status_code=process_resp.status_code)

        token = process_resp.json().get("token")
        if not token:
            return JSONResponse(content={"error": "No token from Tabscanner"}, status_code=500)


        result_data = None
        for _ in range(10):
            time.sleep(1)
            resp = requests.get(f"{RESULT_URL}{token}", headers={"apikey": TABSCANNER_API_KEY})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("result"):
                    result_data = data["result"]
                    break
            elif resp.status_code != 202:
                return JSONResponse(content={"error": f"Tabscanner Result Error: {resp.text}"}, status_code=resp.status_code)

        if result_data is None:
            return JSONResponse(content={"error": "OCR Timeout"}, status_code=504)

        prompt = f"""
        Analyze this receipt OCR data:
        {json.dumps(result_data)}
        based on the given receipt information try to fill in the categories for a personal finance app like category, or the account type.
        Map it to this JSON structure:
        {{
            "transaction_type": "Expense" | "Income",
            "amount": number,
            "account": "personal" | "business",
            "category": "string (e.g. Groceries, Dining)",
            "date": "YYYY-MM-DD",
            "description": "string (Merchant + Address)",
            "is_recurring": boolean
        }}
        """

        try:
            response = call_gemini(model_name=GEN_MODEL_NAME, prompt=prompt)
        except RuntimeError as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)

        raw_text = response.text
        
        try:
            form_json = json.loads(raw_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                form_json = json.loads(json_match.group())
            else:
                return JSONResponse(content={"error": "Invalid JSON from Gemini", "raw": raw_text}, status_code=500)

        return JSONResponse(content=form_json)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)