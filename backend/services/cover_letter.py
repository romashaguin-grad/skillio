import google.generativeai as genai
from config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

COVER_LETTER_PROMPT = """You are a professional cover letter writer. Write a concise, tailored cover letter based on the candidate's resume and the job description below.

Requirements:
- 3 short paragraphs maximum
- Professional but warm tone
- Highlight specific skills from the resume that match the job requirements
- Do not include date, address headers, or "Dear Hiring Manager" -- start directly with the first paragraph
- Do not use em dashes
- Keep it under 200 words

Candidate Resume:
{resume_text}

Job Title: {job_title}
Company: {company}
Job Description: {job_description}
Job Requirements: {job_requirements}

Write the cover letter now:"""


async def generate_cover_letter(
    resume_text: str,
    job_title: str,
    company: str,
    job_description: str,
    job_requirements: str,
) -> str:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = COVER_LETTER_PROMPT.format(
            resume_text=resume_text[:4000],
            job_title=job_title,
            company=company,
            job_description=job_description,
            job_requirements=job_requirements,
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Cover letter generation error: {e}")
        return ""