from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from extract_resume import extract_text_from_pdf

model = SentenceTransformer("all-MiniLM-L6-v2")

def rank_resumes_against_jd(jd_text, resume_paths):
    """
    jd_text: plain text of the job description
    resume_paths: list of file paths to resume PDFs (max 5)
    Returns a list of dicts sorted by best match first
    """
    jd_embedding = model.encode([jd_text])

    results = []
    for path in resume_paths:
        resume_text = extract_text_from_pdf(path)
        resume_embedding = model.encode([resume_text])
        similarity = cosine_similarity(jd_embedding, resume_embedding)[0][0]

        results.append({
            "path": path,
            "resume_text": resume_text,
            "similarity": similarity
        })

    # Sort by similarity, highest first
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results

if __name__ == "__main__":
    jd_text = """
    We are looking for an AI Engineer with experience in Python, computer vision (OpenCV, YOLO),
    and machine learning frameworks. Experience with real-time systems is a plus.
    """

    resume_paths = ["data/my_resume.pdf"]  # add more paths here later for a real test

    results = rank_resumes_against_jd(jd_text, resume_paths)

    for r in results:
        print(f"{r['path']} — similarity: {r['similarity']:.4f}")