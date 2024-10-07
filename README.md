Turmerik: Patient-Trial Matching Application
README
Table of Contents
Introduction
Features
Project Structure
Prerequisites
Installation Guide
Usage
Running the Backend
Running the Streamlit Frontend
Backend Functionality
Streamlit UI Features
Sample Output
Future Improvements
1. Introduction
Turmerik: Patient-Trial Matching Application is designed to match patients with active clinical trials based on criteria such as age, gender, and medical history. The system leverages two different matching algorithms:

FuzzyWuzzy for string-based matching
Sentence Transformers for semantic-based matching.
Healthcare professionals can easily use the Streamlit-powered UI to upload patient data, select a matching technique, and download detailed reports of eligible clinical trials for each patient.

2. Features
Clinical Trial Scraping: Automatically fetches clinical trials from ClinicalTrials.gov.
Patient Data Processing: Loads and processes patient data with attributes like age, gender, and medical conditions.
Two Matching Techniques: Choose between FuzzyWuzzy (string-based) or Sentence Transformers (semantic-based).
Statistical Output: Generates a detailed summary of the matching process.
JSON Export: Export matched results in a JSON format for further analysis.
Streamlit UI: An intuitive interface for healthcare professionals to interact with the system.
3. Project Structure
bash
Copy code
📁 Turmerik-Patient-Trial-Matching
│
├── api_call_new.py               # Backend script for scraping and matching logic
├── app.py                        # Streamlit frontend script
├── patients.csv                  # Sample patient data file
├── conditions.csv                # Sample patient condition data file
├── matched_patients.json         # JSON file for storing matched patient-trial results
├── README.md                     # Project documentation
└── requirements.txt              # Python dependencies
4. Prerequisites
Make sure you have the following installed:

Python 3.8+
pip (Python package installer)
You’ll also need access to:

ClinicalTrials.gov API for scraping active clinical trials.
A working internet connection to download Sentence Transformers.
5. Installation Guide
Clone the Repository:

bash
Copy code
git clone https://github.com/your-username/Turmerik-Patient-Trial-Matching.git
cd Turmerik-Patient-Trial-Matching
Set Up a Virtual Environment (recommended):

bash
Copy code
python -m venv env
source env/bin/activate   # On Windows, use `env\Scripts\activate`
Install the Required Packages: Install all dependencies using the provided requirements.txt:

bash
Copy code
pip install -r requirements.txt
Download Sentence Transformer Model (if necessary): If using the Sentence Transformers option, ensure that the transformer model is downloaded:

bash
Copy code
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2')"
6. Usage
1. Running the Backend
The backend performs clinical trial scraping and patient matching. Run this when you need to process patients and retrieve matched trials.

Start the Backend:

bash
Copy code
python api_call_new.py
This will:

Scrape active clinical trials from ClinicalTrials.gov.
Process the patient data from the provided CSV files.
Perform matching based on the selected algorithm (FuzzyWuzzy or Sentence Transformers).
Save the results in matched_patients.json.
Backend Configuration:

Update the patient data (patients.csv) and condition data (conditions.csv) files as needed.
You can control the number of patients and clinical trials in the api_call_new.py script:
python
Copy code
num_patients_to_process = 5  # Number of patients
num_clinical_trials = 3000    # Number of clinical trials to scrape
2. Running the Streamlit Frontend
The Streamlit app provides a user-friendly interface for managing patient-trial matching.

Start the Streamlit App:

bash
Copy code
streamlit run app.py
Access the UI:

Open a browser and navigate to http://localhost:8501 (or the provided URL from the Streamlit terminal output).
UI Functionality:

Select Patient: Choose a patient from the sidebar dropdown.
Select Matching Technique: Choose either FuzzyWuzzy or Sentence Transformers.
Run Matching: Click the "Run Matching" button to start the matching process.
View Results: After matching, the app will display the statistics and allow you to download the results in JSON format.
7. Backend Functionality
Clinical Trial Scraping:

The function scrape_clinical_trials() scrapes up to 1000 trials per API call and handles pagination.
Trial data is extracted from ClinicalTrials.gov and stored in a structured DataFrame.
Patient Data Processing:

The function load_patient_data() processes patient demographic and medical history data.
It merges and structures the data, including age and condition calculations.
Matching Algorithms:

FuzzyWuzzy: Performs string-based matching between patient conditions and trial criteria.
Sentence Transformers: Uses embeddings to match patient conditions with trial criteria on a semantic level.
Statistics Generation:

After the matching process, generate_statistics() produces a DataFrame that shows how many trials each patient qualifies for based on their conditions.
8. Streamlit UI Features
Patient Selection: A dropdown to select individual patients from the provided dataset.
Matching Technique Selection: A radio button option to choose between FuzzyWuzzy and Sentence Transformers.
Run Matching: Starts the matching process for the selected patient using the chosen technique.
Detailed Statistics: Displays matching results in a table, showing how many trials match each patient based on their conditions.
Download JSON: The matched trials can be downloaded as a JSON file for further analysis or record-keeping.
9. Sample Output
Statistics Table Example:
Patient ID	Number of Trials	Conditions Matched
001	5	3
002	8	7
JSON Output Example (matched_patients.json):
json
Copy code
[
  {
    "patientId": "001",
    "eligibleTrials": [
      {
        "trialId": "NCT123456",
        "trialName": "COVID-19 Vaccine Trial",
        "eligibilityCriteriaMet": ["Age match", "Condition match"]
      }
    ]
  }
]
10. Future Improvements
Batch Processing: Allow users to process multiple patients at once.
Enhanced Matching: Add more advanced NLP models for better trial-patient matching.
Additional Data Sources: Integrate more clinical trial sources beyond ClinicalTrials.gov.
Role-Based Access: Different user roles (e.g., researchers vs. coordinators) with various levels of access and functionalities.
