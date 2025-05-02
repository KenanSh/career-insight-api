# AI-Powered Career Insights API

This project implements a full pipeline for evaluating professional career profiles using AI and LLMs. It performs the following tasks:

- Cleans and preprocesses raw profile and job history data from Excel Workbook.

- Computes career tags including **total years of experience** and **industry-specific experience distribution** *(Big Pharma, Mid Pharma, Biotech, Other)*.

- Assesses career progression using a **Hugging Face-hosted LLM** `zephyr-7b-beta`, based on profile headlines and job history.

- Serves results through a **Flask API** that returns structured JSON for any `profile ID`.

The solution demonstrates strong capabilities in data cleaning, feature engineering, prompt design, and model integration for real-world talent analysis.

## Table of Contents
- [Project Pipeline](#project-pipeline)
- [Installation & Usage](#installation--usage)
- [Future Work](#future-work)


## Project Pipeline

Overview of the steps involved to make the API work end-to-end:

1. **Data Ingestion**
   * Load and inspect raw Excel sheets (`profiles`, `positions`, `education`) from the source Excel Workbook.
2. **Data Cleaning & Preprocessing** `data_preprocessing.py`
   * Handle missing values in key columns like `start_year`, `start_month`, `end_year`, `end_month`.
   * Infer missing dates based on career chronology in this logic:
     * `start_month`:
       * If the position is the first for the profile → set to '1' or 'January'.
       * Otherwise, use the end_month of the previous position (if available).
       * If that’s not reliable → fallback to '1' or 'January' as a default.
     * `end_year`:
       * If it's the last position for the profile → set to the current year **(for calculations purposes)**.
       * Otherwise, use the start_year of the next position.
       * If next position's start_year is missing → fallback to current year.
     * `end_month`:
       * If it's the last position for the profile → set to the current month **(for calculations purposes)**.
       * If the next position starts in January of the following year → set end_month to December (12).
       * If next position is in the same year and a later month → use next_start_month - 1.
       * Else, fallback to next_start_month or current month as default.
   * Normalize company names and categorize them into `Big Pharma`, `Mid Pharma`, `Biotech`, or `Other` (Note: Categorizing them based on constant information infered through small online search).
3. **Feature Engineering** `extract_tags.py`
   * Compute total years of experience for each profile by using the simple logic (today_daytime - earlist_position_start).
   * Calculate the percentage of time spent in each pharma category (company_category) by filtiring positions by `profile_id` then calculate duration per job then sum the duration by category in order to get the final percentage distribution.
4. **Career Progression Scoring** `extract_score.py`
   * Construct a natural language prompt combining a candidate’s headline and chronologically ordered job history, formatted to align with prompt engineering best practices:
     * Role Definition – instructs the LLM to act as a career evaluation expert.
     * Task Clarity – specifies the exact task: rate career growth and justify it in one sentence.
     * Instruction Section – lists expectations clearly (e.g., response format, scale meaning).
     * Example Block – provides a well-structured sample answer.
     * Polished Tone – maintains a formal, expert tone throughout the prompt.
   * Use the Hugging Face model zephyr-7b-beta for scoring due to its strong instruction-following performance and lightweight deployment footprint, making it ideal for structured API interactions.
   * Send the prompt to the LLM inference endpoint via POST request, using secure headers (HF_TOKEN, HF_CAREER_EP) from environment variables.
   * Parse the model’s response to extract:
     * career_progression_score – an integer between 0 and 100.
     * career_rationale – a single sentence explaining the score.
   * If the format deviates, fallback logic ensures robust parsing and informative error handling.
5. **REST API Development** `app.py`
   * Build a Flask API with a `/generate-profile` endpoint.
   * Accept a `profile_id`, return a full analysis including **name, experience, pharma breakdown, and career score**.


## Installation & Usage

### Prerequisites
1. [Anaconda](https://www.anaconda.com/download) installed for environment and dependency management.

2. [Git](https://git-scm.com/downloads) (Optional: in case of cloning the repository)

3. [Hugging Face](https://huggingface.co/) account with a valid Access Token

***Optional*** Postman or curl for testing the API endpoint manually

### Step(1): Clone the repository
```bash
   git clone https://github.com/KenanSh/career-insight-api.git
   cd career-insight-api
```

### Step(2): Setup the virtual environment (Anaconda)
```bash
   conda env create -f environment.yml
   conda activate pharma-api
```
**OR**
```bash
   conda create -n pharma-api python=3.9
   conda activate pharma-api
   pip install -r requirements.txt
```

### Step(3): Environment Variables
Create a `.env` file in the project root with the following values:
```bash
  # Replace with Your Hugging Face Reader Token (Settings -> Access Token -> Create New Token)
  export HF_TOKEN = hf_your_huggingface_token
  # Keep it set for the best model for this Task
  export HF_CAREER_EP=https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta
```
The final content in the `.env` file should look like:
```bash
  HF_TOKEN = hf_plcB....
  HF_CAREER_EP=https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta
```

### Step(4): Start the Data Preprocessing Code
**Run this command:**
```bash
  python data_preprocessing.py
```
*Note: I will upload the processed dataset because its small just for testing*

### Step(5): *(Optional)* Test Extracting Methods
**This step is just to test the methods of extracting Tags and score to see how the API works**
```bash
  python extract_tags.py
  python extract_score.py
```
*Note: If you want to test them you should uncomment the last few lines of each file*

### Step(6): Running the API Locally
**First you need to ensure that server is up and runing in separate CMD**
```bash
  python app.py
```
**Now Your API will be live at: `http://localhost:5000/generate-profile`**

**Test the API with `curl` Run this command**
```bash
  curl -X POST http://localhost:5000/generate-profile -H "Content-Type: application/json" -d "{\"profile_id\": \"0d3f2f3d-5b74-41ab-bd57-5b68a73afc6d\"}"
```
*Note: Here we pass the first profile_id for example*

**Sample Response (JSON Format)**
```bash
{
  "id": "0d3f2f3d-5b74-41ab-bd57-5b68a73afc6d",
  "full_name": "Sabine Kohncke",
  "years_of_experience": 16,
  "pharma_experience_distribution": {
    "Big Pharma": 67.89,
    "Mid Pharma": 0.0,
    "Biotech": 0.0,
    "Other": 32.11
  },
  "career_progression_score": 85,
  "career_rationale": "Candidate has consistently progressed through various marketing roles with increasing responsibility."
}
```


## Future Work
This project demonstrates a strong foundation for AI-powered talent analysis. Several future enhancements could further improve its accuracy, scalability, and value:

1. **Scale with Larger Datasets**
Expand the system to support tens of thousands of profiles across multiple organizations or sectors by optimizing data pipelines and leveraging cloud storage.

2. **Enhance Career Logic Calculations**
Refine the career tag computations with more accurate gap detection, overlapping job handling, and more nuanced date logic using vectorized or custom Python routines.

3. **Support Richer Industry Taxonomies**
Expand the pharma category mapping to include granular classifications (e.g., Rare Diseases, Oncology Biotech, CDMOs) or other industry verticals beyond life sciences.

4. **Use Larger, Fine-Tuned LLMs**
Upgrade to more powerful LLMs like GPT-4, Command-R, or Claude Opus for improved rationale quality and semantic understanding of ambiguous career trajectories.

5. **Add Confidence Scoring & Anomaly Detection**
Integrate uncertainty or confidence scores from LLM responses and flag inconsistencies or anomalous patterns in job histories.

6. **Deploy as a Scalable Microservice**
Containerize the API using Docker, integrate with FastAPI for production-grade deployment, and prepare for horizontal scaling on cloud platforms.

7. **UI Dashboard for Recruiters**
Build an interactive front-end dashboard to visualize profiles, scores, and distributions—enabling non-technical HR teams to interact with the insights.

8. **Batch API Support & Asynchronous Requests**
Add support for submitting and scoring batches of profiles with non-blocking execution for faster throughput.