import pandas as pd
import requests
import json
from datetime import datetime
import re
from fuzzywuzzy import fuzz
from sentence_transformers import SentenceTransformer,util
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

use_sentence_transformers = True
if use_sentence_transformers:
    model = SentenceTransformer('all-MiniLM-L6-v2')

params = {
    "format": "json",
    "filter.overallStatus": "RECRUITING",
    "pageSize": 1000,
}


def scrape_clinical_trials():
    page_token = None
    trial_data = {
        "NCTId": [],
        "Title": [],
        "Condition": [],
        "Eligibility": [],
        "Status": [],
        "Inclusion": [],
        "Exclusion": [],
        "MinAgeCriteria": [],
        "MaxAgeCriteria": [],
        "GenderCriteria": []
    }

    page_count = 0
    max_pages = 2

    while page_count < max_pages:
        params = {
            "format": "json",
            "filter.overallStatus": "RECRUITING",
            "pageSize": 1000,  # Maximum allowed
        }

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(BASE_URL, params=params)

        if response.status_code == 200:
            data = response.json()

            if 'studies' in data:
                # Process each study
                for study in data['studies']:
                    nct_id = study['protocolSection']['identificationModule'].get('nctId', 'N/A')
                    title = study['protocolSection']['identificationModule'].get('briefTitle', 'N/A')
                    condition = ', '.join(study['protocolSection']['conditionsModule'].get('conditions', ['N/A']))
                    eligibility = study['protocolSection']['eligibilityModule'].get('sex', 'N/A')
                    status = study['protocolSection']['statusModule'].get('overallStatus', 'N/A')
                    gender_criteria = re.findall(r'(?i)(female|male|both genders|all genders|all sexes)', eligibility)
                    eligibilityCriteria = study['protocolSection']['eligibilityModule'].get('eligibilityCriteria',
                                                                                            'N/A')
                    if eligibilityCriteria != 'N/A':
                        eligibilityCriteria = eligibilityCriteria.split('\n\n')
                        try:
                            trial_data['Inclusion'].append(eligibilityCriteria[1])
                        except:
                            trial_data['Inclusion'].append('N/A')
                        try:
                            trial_data['Exclusion'].append(eligibilityCriteria[3])
                        except:
                            trial_data['Exclusion'].append('N/A')
                    else:
                        trial_data['Inclusion'].append('N/A')
                        trial_data['Exclusion'].append('N/A')
                    trial_data["NCTId"].append(nct_id)
                    trial_data["Title"].append(title)
                    trial_data["Condition"].append(condition)
                    trial_data["Eligibility"].append(eligibility)
                    trial_data["Status"].append(status)
                    trial_data["MinAgeCriteria"].append(
                        re.search(r'\d+', study['protocolSection']['eligibilityModule'].get('minimumAge', 'N/A')).group(
                            0) if study['protocolSection']['eligibilityModule'].get('minimumAge',
                                                                                    'N/A') != 'N/A' else 'N/A')
                    trial_data["MaxAgeCriteria"].append(
                        re.search(r'\d+', study['protocolSection']['eligibilityModule'].get('maximumAge', 'N/A')).group(
                            0) if study['protocolSection']['eligibilityModule'].get('maximumAge',
                                                                                    'N/A') != 'N/A' else 'N/A')
                    trial_data["GenderCriteria"].append(gender_criteria[0].lower() if gender_criteria else 'all')

            # Check if there is a next page token
            page_token = data.get('nextPageToken', None)

            if not page_token:
                # No more pages
                break

            # Increment the page count
            page_count += 1
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            print(response.text)
            break
        trial_df = pd.DataFrame(trial_data)
        return trial_df

    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        print(response.text)
        return None


def load_patient_data(patient_file_path, conditions_file_path):
    patient_df = pd.read_csv(patient_file_path)
    conditions_df = pd.read_csv(conditions_file_path)

    patient_df['BIRTHDATE'] = pd.to_datetime(patient_df['BIRTHDATE'])
    current_year = datetime.now().year
    patient_df['Age'] = current_year - patient_df['BIRTHDATE'].dt.year

    def classify_conditions(group):
        past_conditions = group[~group['STOP'].isna()]['DESCRIPTION'].tolist()
        current_conditions = group[group['STOP'].isna()][
            'DESCRIPTION'].tolist()
        return pd.Series({
            'Past Conditions': past_conditions,
            'Current Conditions': current_conditions
        })
    result = conditions_df.groupby('PATIENT').apply(classify_conditions).reset_index()
    merged_df = pd.merge(patient_df, result, left_on='Id', right_on='PATIENT', how='left')
    merged_df['GENDER'] = merged_df['GENDER'].fillna('')
    return merged_df


def Exclusion_matching(input_text_list, target_text_list, use_sentence_transformers):
    """
    Matches exclusion criteria based on either FuzzyWuzzy or Sentence Transformers.

    Args:
    input_text_list (list): List of input conditions from the patient.
    target_text_list (list): List of exclusion criteria from the trial.
    use_sentence_transformers (bool): Whether to use Sentence Transformers (True) or FuzzyWuzzy (False).

    Returns:
    bool: True if the exclusion criteria match, False otherwise.
    """
    if isinstance(target_text_list, list) and len(target_text_list) == 0:
        return True
    if isinstance(target_text_list, list):
        target_text_list = [text for text in target_text_list if pd.notna(text)]
    if not target_text_list:
        return True

    # If Sentence Transformers is chosen
    if use_sentence_transformers:
        input_text = ' '.join(input_text_list)
        target_text = ' '.join(target_text_list)
        input_embedding = model.encode(input_text, convert_to_tensor=True)
        target_embedding = model.encode(target_text, convert_to_tensor=True)
        cosine_sim = util.pytorch_cos_sim(input_embedding, target_embedding)
        return cosine_sim >= 0.5  # Adjust similarity threshold as needed

    # FuzzyWuzzy matching (default)
    for start in range(len(input_text_list)):
        for i in range(len(target_text_list)):
            if fuzz.partial_ratio(input_text_list[start].lower(), target_text_list[i].lower()) >= 50:
                return False
    return True


def Inclusion_matching(input_text_list, target_text_list, use_sentence_transformers):
    """
    Matches inclusion criteria based on either FuzzyWuzzy or Sentence Transformers.

    Args:
    input_text_list (list): List of input conditions from the patient.
    target_text_list (list): List of inclusion criteria from the trial.
    use_sentence_transformers (bool): Whether to use Sentence Transformers (True) or FuzzyWuzzy (False).

    Returns:
    bool: True if the inclusion criteria match, False otherwise.
    """
    if isinstance(target_text_list, list) and len(target_text_list) == 0:
        return True
    if isinstance(target_text_list, list):
        target_text_list = [text for text in target_text_list if pd.notna(text)]
    if not target_text_list:
        return True

    # If Sentence Transformers is chosen
    if use_sentence_transformers:
        input_text = ' '.join(input_text_list)
        target_text = ' '.join(target_text_list)
        input_embedding = model.encode(input_text, convert_to_tensor=True)
        target_embedding = model.encode(target_text, convert_to_tensor=True)
        cosine_sim = util.pytorch_cos_sim(input_embedding, target_embedding)
        return cosine_sim >= 0.5  # Adjust similarity threshold as needed

    # FuzzyWuzzy matching (default)
    for start in range(len(input_text_list)):
        for i in range(len(target_text_list)):
            if fuzz.partial_ratio(input_text_list[start].lower(), target_text_list[i].lower()) <= 35:
                return False
    return True


def matching_patient(trial_df, single_patient, use_sentence_transformers=False):
    """
    Match a single patient to the available clinical trials based on the selected matching technique.

    Args:
    trial_df (pd.DataFrame): The dataframe containing trial data.
    single_patient (dict): The patient data as a dictionary.
    use_sentence_transformers (bool): Whether to use Sentence Transformers for matching (default is False, uses FuzzyWuzzy).

    Returns:
    dict: A dictionary containing the patientId and eligible trials.
    """

    matched_trials = []

    for _, trial in trial_df.iterrows():
        if (
                (trial['MinAgeCriteria'] == 'N/A' or single_patient['Age'] >= int(trial['MinAgeCriteria'])) and
                (trial['MaxAgeCriteria'] == 'N/A' or single_patient['Age'] <= int(trial['MaxAgeCriteria'])) and
                (trial['GenderCriteria'] == 'all' or trial['GenderCriteria'] == 'N/A' or trial['GenderCriteria'] ==
                 single_patient['GENDER'].lower()) and
                Exclusion_matching(trial['Exclusion'].split('\n'),
                                   single_patient['Past Conditions'] + single_patient['Current Conditions'],
                                   use_sentence_transformers) and
                Inclusion_matching(trial['Condition'].split(','),
                                   single_patient['Past Conditions'] + single_patient['Current Conditions'],
                                   use_sentence_transformers)
        ):
            matched_trials.append({
                "trialId": trial['NCTId'],
                "trialName": trial['Title'],
                "eligibilityCriteriaMet": [
                    "Age match", "Gender match", "Condition match"
                ]
            })

    return {
        "patientId": single_patient['Id'],
        "eligibleTrials": matched_trials
    }


def run_matching(trial_df, patient_data, num_patients=5, use_sentence_transformers=False):
    """
    Run the matching process for the given patient data and clinical trials.

    Args:
    trial_df (pd.DataFrame): The dataframe containing trial data.
    patient_data (pd.DataFrame): The dataframe containing patient data.
    num_patients (int): Number of patients to process (default is 10).
    use_sentence_transformers (bool): Whether to use Sentence Transformers for matching (default is False, uses FuzzyWuzzy).

    Returns:
    list: A list of matched patients with eligible trials.
    """

    output_records = []

    for i in range(num_patients):
        patient = patient_data.iloc[i].to_dict()
        # Pass the matching technique to the matching_patient function
        result = matching_patient(trial_df, patient, use_sentence_transformers)
        output_records.append(result)

    # Save output to JSON
    with open('matched_patients.json', 'w') as json_file:
        json.dump(output_records, json_file, indent=4)

    print(f"Processed {num_patients} patients. JSON saved as 'matched_patients.json'")
    return output_records


def generate_statistics(matched_patients):
    """
    Generate statistics based on matched patient data.

    For each patient, this function calculates:
    1. The number of eligible trials for the patient.
    2. The number of trials that matched based on the conditions.

    Args:
    matched_patients (list): A list of dictionaries where each dictionary contains
                             the 'patientId', and 'eligibleTrials' (the matched trials
                             for that patient).

    Returns:
    pd.DataFrame: A DataFrame containing the statistics for each patient.
                  Columns:
                    - patientId: The unique identifier for the patient.
                    - number_of_trials: Total number of eligible trials for the patient.
                    - conditions_matched: Number of trials where the patient's conditions matched.
    """

    # Initialize an empty list to hold the statistics for each patient
    stats = []

    # Loop over each patient in the matched_patients list
    for patient in matched_patients:
        # Extract the patient ID
        patient_id = patient["patientId"]

        # Get the total number of eligible trials for this patient
        num_trials = len(patient["eligibleTrials"])

        # Initialize a counter for the number of trials where conditions matched
        condition_matches = 0

        # Loop through each eligible trial for this patient
        for trial in patient["eligibleTrials"]:
            # Check if the trial has a "Condition match" in its eligibility criteria
            if "Condition match" in trial["eligibilityCriteriaMet"]:
                condition_matches += 1
        stats.append({
            "patientId": patient_id,
            "number_of_trials": num_trials,
            "conditions_matched": condition_matches
        })
    stats_df = pd.DataFrame(stats)
    return stats_df


if __name__ == "__main__":
    trial_df = scrape_clinical_trials()
    trial_df.fillna('N/A', inplace=True)
    patient_data = load_patient_data(r"patients.csv", r"conditions.csv")
    patient_data.fillna('N/A', inplace=True)
    matched_patients = run_matching(trial_df, patient_data[['Id', 'Age', 'GENDER', 'Past Conditions', 'Current Conditions']], num_patients=2)
    if use_sentence_transformers:
        print("Comparison was done using Sentence Transformers.")
    else:
        print("Comparison was done using FuzzyWuzzy.")
    stats_df = generate_statistics(matched_patients)
    print(stats_df)
