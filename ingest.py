import pandas as pd

def load_and_clean_data(csv_path):
    # Load the dataset
    df = pd.read_csv(csv_path)

    # Drop the row with a null Title (we found 1 earlier)
    df = df.dropna(subset=["Title"])

    # Normalize inconsistent ExperienceLevel labels
    experience_mapping = {
        "Fresher": "Fresher",
        "Entry-Level": "Fresher",
        "Junior": "Junior",
        "Mid-Level": "Mid",
        "Mid-level": "Mid",
        "Mid-Senior": "Mid-Senior",
        "Mid-Senior Level": "Mid-Senior",
        "Senior": "Senior",
        "Senior-Level": "Senior",
        "Lead": "Lead",
        "Experienced": "Mid",  # treat generic "Experienced" as Mid
    }
    df["ExperienceLevel"] = df["ExperienceLevel"].map(experience_mapping).fillna(df["ExperienceLevel"])

    # Create a single combined text field per job (this is what gets embedded later)
    df["combined_text"] = (
        "Title: " + df["Title"] + "\n" +
        "Experience Level: " + df["ExperienceLevel"] + " (" + df["YearsOfExperience"].astype(str) + " years)\n" +
        "Skills: " + df["Skills"] + "\n" +
        "Responsibilities: " + df["Responsibilities"]
    )

    return df

if __name__ == "__main__":
    df = load_and_clean_data("data/job_dataset.csv")
    print("Total jobs after cleaning:", len(df))
    print("\nSample combined_text for first job:\n")
    print(df["combined_text"].iloc[0])