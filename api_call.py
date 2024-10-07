import requests
import pandas as pd
import re
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


def scrape_clinical_trials_first_two_pages():
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
    max_pages = 2  # Limiting to first two pages

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

    # Convert trial data to DataFrame
    trial_df = pd.DataFrame(trial_data)
    return trial_df


# Fetch clinical trials for the first two pages
trial_df_first_two_pages = scrape_clinical_trials_first_two_pages()

# Display the first few rows of the DataFrame
print(trial_df_first_two_pages.info())