import os
import json
from dotenv import load_dotenv
from groq import Groq
from extract_resume import extract_text_from_pdf

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_ats_score(resume_text):
    prompt = f"""You are an ATS (Applicant Tracking System) and resume expert.
Analyze the following resume and respond with ONLY valid JSON (no markdown, no extra text) in this exact structure:

{{
  "overall_score": <number 0-100>,
  "sections": {{
    "Contact Information": {{"status": "good" or "warning", "note": "<short note>"}},
    "Professional Summary": {{"status": "good" or "warning", "note": "<short note>"}},
    "Skills": {{"status": "good" or "warning", "note": "<short note>"}},
    "Work Experience": {{"status": "good" or "warning", "note": "<short note>"}},
    "Education": {{"status": "good" or "warning", "note": "<short note>"}}
  }},
  "suggestions": ["<suggestion 1>", "<suggestion 2>", "<suggestion 3>"]
}}

RESUME:
{resume_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=700,
        reasoning_effort="low"
    )

    raw = response.choices[0].message.content.strip()

    # Clean up in case the model wraps JSON in markdown fences
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)

if __name__ == "__main__":
    resume_text = extract_text_from_pdf("data/my_resume.pdf")
    result = get_ats_score(resume_text)
    print(json.dumps(result, indent=2))