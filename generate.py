import os
from dotenv import load_dotenv
from groq import Groq
from retrieve import retrieve_matching_jobs
from extract_resume import extract_text_from_pdf

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_match_explanation(resume_text, job_text, job_title):
    prompt = f"""You are a career advisor. Given a candidate's resume and a job description, 
write a short 2-3 sentence explanation of how well the candidate matches this job.
Mention specific matching skills/experience, and note any gaps if relevant.

RESUME:
{resume_text}

JOB TITLE: {job_title}
JOB DESCRIPTION:
{job_text}

Match explanation:"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
        reasoning_effort="low"
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    resume_path = "data/my_resume.pdf"
    resume_text = extract_text_from_pdf(resume_path)

    results = retrieve_matching_jobs(resume_path, top_k=3)

    print("Top matches with AI-generated explanations:\n")
    for i in range(len(results["ids"][0])):
        title = results["metadatas"][0][i]["title"]
        job_text = results["documents"][0][i]
        explanation = generate_match_explanation(resume_text, job_text, title)
        print(f"{i+1}. {title}")
        print(f"   {explanation}\n")