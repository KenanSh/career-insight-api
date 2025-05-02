import pandas as pd

# Load processed data
OUTPUT_DATASET = "data\processed\processed_data.xlsx"
profiles = pd.read_excel(OUTPUT_DATASET, sheet_name="profiles")
positions = pd.read_excel(OUTPUT_DATASET, sheet_name="positions")

# Constants
EXPECTED_CATEGORIES = ["Big Pharma", "Mid Pharma", "Biotech", "Other"]

# Compute years_of_experience (finding earliest start date and subtract from todays_date divided by 365 to be in years)
def compute_years_of_experience(profile_id: str) -> int:
    profile_positions = positions[positions['profile_id'] == profile_id]
    if profile_positions.empty:
        return 0
    earliest_start_date = profile_positions['start_date'].min()
    if pd.isna(earliest_start_date):
        return 0
    today = pd.Timestamp.today()
    experience_years = (today - earliest_start_date).days // 365
    return experience_years

# Compute pharma_experience_distribution
def compute_pharma_experience_distribution(profile_id: str) -> dict:
    profile_positions = positions[positions['profile_id'] == profile_id].copy()
    if profile_positions.empty:
        return {category: 0.0 for category in EXPECTED_CATEGORIES}

    # Calculate duration in days
    profile_positions['duration_days'] = (
        profile_positions['end_date'] - profile_positions['start_date']
    ).dt.days

    # Group and normalize
    category_durations = profile_positions.groupby('company_category')['duration_days'].sum()
    total_duration = category_durations.sum()
    if total_duration == 0:
        return {category: 0.0 for category in EXPECTED_CATEGORIES}

    # Fill missing categories with 0 if any
    distribution = {
        category: round(float(category_durations.get(category, 0) / total_duration) * 100, 2)
        for category in EXPECTED_CATEGORIES
    }
    return distribution

# Combine Both Tags
def compute_tags(profile_id: str) -> dict:
    return {
        "profile_id": profile_id,
        "years_of_experience": compute_years_of_experience(profile_id),
        "pharma_experience_distribution": compute_pharma_experience_distribution(profile_id)
    }

# Test
# if __name__ == "__main__":
#     test_id = profiles['id'].iloc[0]
#     result = compute_tags(test_id)
#     print("Tags:")
#     print(result)