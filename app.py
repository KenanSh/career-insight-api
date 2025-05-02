import os
import json
import pandas as pd
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv

from extract_tags import compute_tags
from extract_score import grade_career

# Load environment variables
load_dotenv()

OUTPUT_DATASET = "data\processed\processed_data.xlsx"
profiles = pd.read_excel(OUTPUT_DATASET, sheet_name="profiles")
positions = pd.read_excel(OUTPUT_DATASET, sheet_name="positions")

# Initialize Flask App
app = Flask(__name__)

@app.route("/generate-profile", methods=["POST"])
def generate_profile():
    data = request.get_json()

    # Validate input
    profile_id = data.get("profile_id") if data else None
    if not profile_id:
        return jsonify({"error": "Missing 'profile_id' in request"}), 400

    profile = profiles[profiles["id"] == profile_id]
    if profile.empty:
        return jsonify({"error": f"profile_id '{profile_id}' not found"}), 400

    try:
        # Compute experience tags
        tags = compute_tags(profile_id)
        years_of_exp = tags["years_of_experience"]
        pharma_dist = tags["pharma_experience_distribution"]

        # Compute LLM score
        score, rationale = grade_career(profile_id)

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

    # Build and return ordered response
    ordered_response = {
        "id": profile_id,
        "full_name": profile.iloc[0]["full_name"],
        "years_of_experience": years_of_exp,
        "pharma_experience_distribution": pharma_dist,
        "career_progression_score": score,
        "career_rationale": rationale
    }

    return Response(
        json.dumps(ordered_response, ensure_ascii=False, indent=2),
        content_type="application/json"
    )

# Start the Flask server
if __name__ == "__main__":
    app.run(debug=True)
