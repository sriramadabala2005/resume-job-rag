from sentence_transformers import SentenceTransformer
import chromadb
from extract_resume import extract_text_from_pdf

def retrieve_matching_jobs(resume_path, top_k=5):
    # Load the same embedding model used for jobs (must match!)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Connect to the existing vector store
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_collection(name="jobs")

    # Extract resume text and convert to embedding
    resume_text = extract_text_from_pdf(resume_path)
    resume_embedding = model.encode([resume_text]).tolist()

    # Search for the top_k most similar jobs
    results = collection.query(
        query_embeddings=resume_embedding,
        n_results=top_k
    )

    return results

if __name__ == "__main__":
    results = retrieve_matching_jobs("data/my_resume.pdf", top_k=5)

    print("Top matching jobs:\n")
    for i in range(len(results["ids"][0])):
        title = results["metadatas"][0][i]["title"]
        exp_level = results["metadatas"][0][i]["experience_level"]
        distance = results["distances"][0][i]
        print(f"{i+1}. {title} ({exp_level}) — similarity distance: {distance:.4f}")