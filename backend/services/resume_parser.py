import pdfplumber
import google.generativeai as genai
import json
import io
from config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


PARSE_PROMPT = """You are a resume parser. Extract the following from the resume text and return ONLY valid JSON, no markdown, no explanation.

Return this exact structure:
{
  "summary": "brief professional summary or objective (1-2 sentences)",
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Jan 2022 - Present",
      "description": "brief description"
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "University Name",
      "year": "2024"
    }
  ]
}

Resume text:
"""


async def parse_resume(pdf_bytes: bytes) -> dict:
    """Extract text from PDF and parse with Gemini."""
    # Extract raw text with pdfplumber
    raw_text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            raw_text += page.extract_text() or ""

    if not raw_text.strip():
        return {"raw_text": "", "skills": [], "experience": [], "education": [], "summary": ""}

    # Parse with Gemini
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(PARSE_PROMPT + raw_text[:8000])  # cap at 8k chars
        response_text = response.text.strip()

        # Strip markdown fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        parsed = json.loads(response_text)
        parsed["raw_text"] = raw_text
        return parsed

    except Exception as e:
        # Fallback: return raw text only, let user fill profile manually
        print(f"Gemini parsing error: {e}")
        return {
            "raw_text": raw_text,
            "skills": [],
            "experience": [],
            "education": [],
            "summary": "",
        }
