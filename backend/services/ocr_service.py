import google.generativeai as genai
import base64, json, os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def parse_receipt(image_bytes: bytes, media_type: str) -> dict:
    model = genai.GenerativeModel("gemini-1.5-flash")
    image_part = {"mime_type": media_type, "data": base64.b64encode(image_bytes).decode()}
    response = model.generate_content([
        image_part,
        "Extract receipt data and return ONLY raw JSON with keys: merchant (string), date (YYYY-MM-DD), items (array of {name, price}), total (float), category (one of: Food, Shopping, Transport, Entertainment, Health, Utilities, Other). No markdown, no explanation, raw JSON only."
    ])
    raw = response.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
