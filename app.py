import streamlit as st
import pandas as pd
import json
from api_call_new import scrape_clinical_trials, load_patient_data, run_matching, generate_statistics

# Load the clinical trial data when the app starts
trial_df = scrape_clinical_trials()
trial_df.fillna('N/A', inplace=True)

# Set up the Streamlit app
st.title("Patient-Trial Matching Application")

# Step 1: Load patient data
st.sidebar.title("Options")
patient_file_path = "patients.csv"
conditions_file_path = "conditions.csv"
patient_data = load_patient_data(patient_file_path, conditions_file_path)
patient_data.fillna('N/A', inplace=True)

# Sidebar options: Select Patient ID and Matching Technique
st.sidebar.subheader("Patient Selection")
patient_ids = patient_data["Id"].tolist()
selected_patient = st.sidebar.selectbox("Select Patient ID", patient_ids)

# Option to select the matching technique
st.sidebar.subheader("Matching Technique")
matching_technique = st.sidebar.radio("Choose Matching Technique", ("FuzzyWuzzy", "Sentence Transformers"))

# Number of patients to match (can also add a range or multiple patient selection if needed)
num_patients = 1  # For now, let's keep it 1 patient for selection simplicity

# Run matching when the user clicks the button
if st.sidebar.button("Run Matching"):
    # Determine the matching technique based on the user's choice
    use_sentence_transformers = matching_technique == "Sentence Transformers"

    # Filter selected patient
    selected_patient_data = patient_data[patient_data["Id"] == selected_patient]

    # Run matching for the selected patient
    matched_patients = run_matching(trial_df, selected_patient_data[
        ['Id', 'Age', 'GENDER', 'Past Conditions', 'Current Conditions']], num_patients=num_patients,
                                    use_sentence_transformers=use_sentence_transformers)

    # Generate and display statistics
    stats_df = generate_statistics(matched_patients)
    st.subheader("Detailed Statistics")
    st.dataframe(stats_df)

    # Display success message
    st.success(f"Matching completed for Patient ID: {selected_patient}")

    # Option to download the JSON file with matched trials
    json_filename = 'matched_patients.json'
    with open(json_filename, 'r') as f:
        json_data = f.read()

    # Provide a download link for the JSON file
    st.download_button(
        label="Download JSON",
        data=json_data,
        file_name=json_filename,
        mime="application/json"
    )

    # Indicate the method used for comparison
    if use_sentence_transformers:
        st.info("Comparison was done using Sentence Transformers.")
    else:
        st.info("Comparison was done using FuzzyWuzzy.")
