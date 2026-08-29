from sentence_transformers import SentenceTransformer
import chromadb
from ingest import load_and_clean_data

def build_vector_store():
    # Load and clean the job data
    df = load_and_clean_data("data/job_dataset.csv")

    # Load a lightweight embedding model (runs locally, no API needed)
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Set up a persistent Chroma client (saves to disk so we don't re-embed every time)
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_or_create_collection(name="jobs")

    # Generate embeddings for all job texts
    print("Generating embeddings for", len(df), "jobs...")
    texts = df["combined_text"].tolist()
    ids = [str(i) for i in range(len(df))]  # unique sequential IDs (JobID column has duplicates)
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    # Store in Chroma: embeddings + original text + job metadata
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {"title": row["Title"], "experience_level": row["ExperienceLevel"]}
            for _, row in df.iterrows()
        ]
    )

    print("Vector store built successfully with", collection.count(), "jobs.")

if __name__ == "__main__":
    build_vector_store()