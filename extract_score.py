import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_CAREER_EP = os.getenv("HF_CAREER_EP")

# Load processed data
OUTPUT_DATASET = "data\processed\processed_data.xlsx"
profiles = pd.read_excel(OUTPUT_DATASET, sheet_name="profiles")
positions = pd.read_excel(OUTPUT_DATASET, sheet_name="positions")

# Call the Hugging Face model with a prompt
def call_huggingface_llm(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.post(HF_CAREER_EP, headers=headers, json={"inputs": prompt})
    response.raise_for_status()
    return response.json()[0] if isinstance(response.json(), list) else response.text

# Parse model response like: "85 – Strong growth over 3 years"
def parse_llm_response(response: dict):
    # Extract the generated text safely
    generated_text = response.get("generated_text", "").strip()
    if not generated_text:
        raise ValueError("Model did not return a valid response.")

    # Split the text into lines and search for the "LAST" matching line
    lines = generated_text.strip().split("\n")
    for line in reversed(lines):
        match = re.match(r"(\d{1,3})\s*[--]\s*(.+)", line.strip())
        if match:
            score = int(match.group(1))
            rationale = match.group(2).strip()
            return score, rationale

    # If no valid line found
    print("Could not find a valid score line.")
    return 0, "Unable to parse career progression rating."


# Build and send the prompt
def grade_career(profile_id: str):
    profile = profiles[profiles['id'] == profile_id]
    jobs = positions[positions['profile_id'] == profile_id].sort_values(by='start_date')

    if profile.empty or jobs.empty:
        return None, "No data available"

    headline = profile.iloc[0]['headline']

    def format_position(row):
        start = row['start_date'].strftime('%b %Y') if pd.notna(row['start_date']) else "?"
        end = row['end_date'].strftime('%b %Y') if pd.notna(row['end_date']) else "Present"
        return f"Worked as {row['title']} at {row['company_name']} from {start} to {end}."

    job_summaries = "\n".join(jobs.apply(format_position, axis=1).str.strip())

    # Constructing my prompt (check: "Role definition", "Task clarity", "Instruction section", "Example block", "Polished tone")
    prompt = f"""You are a career evaluation expert. Your task is to assess a candidate's career progression based on their headline and summarized job history.
    Instructions:
    - Rate the candidate's career growth on a scale from 0 (stagnant) to 100 (rapid).
    - Return your answer as a single line in the exact format below.
    Required Format: `[score] - [one-sentence rationale]`
    Example: 75 - Rapid promotions in 2-year intervals with increasing responsibility.
    Candidate Headline:
    {headline}
    Career Summary:
    {job_summaries}
    Now provide your evaluation below:
    """

    raw_response = call_huggingface_llm(prompt)
    print("LLM Response:\n", raw_response)

    return parse_llm_response(raw_response)

# Test
if __name__ == "__main__":
    test_profile_id = profiles['id'].iloc[0]
    score, rationale = grade_career(test_profile_id)
    print(f"Final Result:\nScore: {score}\nRationale: {rationale}")
