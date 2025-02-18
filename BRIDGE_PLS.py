# CREATORS: Michael Khela and Shefali Verma
# PURPOSE: For more details, see the PLS Automation Protocol

import pandas as pd
import numpy as np
import re
import datetime

def pls_Scoring_Fcn(root_filepath, REDCap_raw_scores_file, 
                    id_column, event_name_column, age_column, ac_column, ec_column, output_file_location):

    # import the REDCap raw scores
    file_ext = REDCap_raw_scores_file[-4:]

    if file_ext == ".xlsx":
        raw_scores_df = pd.read_excel(root_filepath + REDCap_raw_scores_file)
    elif file_ext == ".csv":
        raw_scores_df = pd.read_csv(root_filepath + REDCap_raw_scores_file)

    # Modifies the df to consist of only those columns
    raw_scores_df = raw_scores_df[[id_column, event_name_column, age_column, ac_column, ec_column]]

    # Change column names
    raw_scores_df.columns = ['id', 'Event Name', 'AGE', 'AC Raw', 'EC Raw']
    raw_scores_df = raw_scores_df.dropna(subset=['AGE'], how='all')

    # Reformatting the age to accommodate the y:m
    def format_age_value(ae_value):
        ae_value = ae_value.strip()
        if ':' in ae_value:
            return ae_value
        elif 'y' in ae_value and 'm' in ae_value:
            match = re.match(r'(\d+)y(\d+)m', ae_value)
            if match:
                years, months = map(int, match.groups())
                return f'{years}.{months}'
            else:
                raise ValueError(f"Unsupported format for ae_value: {ae_value}")
        else:
            return ae_value.replace(':', '.')

    raw_scores_df["AGE"] = raw_scores_df["AGE"].apply(format_age_value)

    # Remove rows where age is 0
    raw_scores_df = raw_scores_df[raw_scores_df["AGE"] != 0]
    
    # Create a unique study ID
    raw_scores_df['study_id'] = raw_scores_df[['id', 'AGE']].apply(lambda x: '-'.join(x.dropna().astype(str)), axis=1)
    raw_scores_df.set_index("study_id", inplace=True)
    raw_scores_df.drop(columns=["id"], inplace=True)

    # Define age ranges and associated sheet names for AC and EC sheets
    key_sheet_mapping = {
        '0.0-0.2': '0.0-0.2',
        '0.3-0.5': '0.3-0.5',
        '0.6-0.8': '0.6-0.8',
        '0.9-1.1': '0.9-1.1',
        '1.0-1.5': '1.0-1.5',
        '1.6-1.11': '1.6-1.11',
        '2.0-2.5': '2.0-2.5',
        '2.6-2.11': '2.6-2.11',
        '3.0-3.5': '3.0-3.5',
        '3.6-3.11': '3.6-3.11',
        '4.0-4.5': '4.0-4.5',
        '4.6-4.11': '4.6-4.11',
        '5.0-5.5': '5.0-5.5',
        '5.6-5.11': '5.6-5.11',
        '6.0-6.5': '6.0-6.5',
        '6.6-6.11': '6.6-6.11',
        '7.0-7.5': '7.0-7.5',
        '7.6-7.11': '7.6-7.11',
    }

    # Convert the dictionary to a DataFrame for easy manipulation
    df_key_map = pd.DataFrame.from_dict(key_sheet_mapping, orient="index", columns=["age range sheet name"])
    df_key_map.index = pd.RangeIndex(start=1, stop=len(df_key_map) + 1, name="sheet number")

    # Generate a DataFrame that maps sheet number to ages
    # Each sheet number is specific to a particular set of ages
    df_ref_key = pd.DataFrame(index=df_key_map.index)
    df_ref_key["age range"] = df_key_map.apply(
        lambda row: f"{row['age range sheet name']}: {', '.join(map(str, [f'{x:.1f}' for x in list(float(age) for age in row['age range sheet name'].split('-'))]))}",
        axis=1
    )

    def find_ref_table(age_to_ref, df_ref_key):
        # Split the age into integer and decimal parts
        age_int, age_dec = map(int, age_to_ref.split('.'))

        # Iterate over each row in the reference key DataFrame
        for idx, row in df_ref_key.iterrows():
            # Get the age range sheet name from the DataFrame
            age_range_sheet_name = row['age range sheet name']
            # Split the start and end ages of the age range
            start_age_str, end_age_str = age_range_sheet_name.split('-')
            # Split the start and end ages into integer and decimal parts
            start_age_int, start_age_dec = map(int, start_age_str.split('.'))
            end_age_int, end_age_dec = map(int, end_age_str.split('.'))

            # Compare the age to the age range
            # Check if the age falls within the range based on integer and decimal parts
            if (age_int == start_age_int and age_int == end_age_int) and (start_age_dec <= age_dec <= end_age_dec):
                return age_range_sheet_name
            elif age_int == start_age_int and age_int < end_age_int and age_dec >= start_age_dec:
                return age_range_sheet_name
            elif age_int > start_age_int and age_int == end_age_int and age_dec <= end_age_dec:
                return age_range_sheet_name
            elif start_age_int < age_int and age_int < end_age_int:
                return age_range_sheet_name
        return None

    # Create an empty DataFrame to store the T scores
    df_ss_scores = pd.DataFrame()

    # Loop through each individual ID's row of raw scores
    for i in raw_scores_df.index:
        # Get the age of the participant
        age_to_ref_float = str(raw_scores_df.loc[i, "AGE"])
        # Find the correct age group to pull the correct reference tables
        age_group = find_ref_table(age_to_ref_float, df_key_map)
        print("Reference table for", i, "with", age_to_ref_float, "is:", age_group)

        # Read in the reference tables for AC and EC, make sure age is valid
        if age_group not in key_sheet_mapping:
            raw_scores_df.loc[i, 'age_validity'] = f'FIX AGE INPUT FOR {i}'
            continue

        '''
        Purpose: Returns AC and EC Standard Scores and Percentile Ranks

        - Takes participant's raw AC and EC scores from raw_scores_df
        - Using AC and EC raw scores, finds corresponding standard scores in (ac/ec)_ref_table
        - Using AC and EC raw scores, finds corresponding percentile rank in (ac/ec)_ref_table
        - Saves AC and EC standard scores and percentile rank in new dataframe: df_ss_scores
        '''
        # reads ref_material
        ac_ref_table = pd.read_excel(root_filepath + 'Assessment_Packages/PLS_package/PLS_ref_materials/A.1 AC Scores.xlsx', key_sheet_mapping[age_group], header=None)
        ec_ref_table = pd.read_excel(root_filepath + 'Assessment_Packages/PLS_package/PLS_ref_materials/A.2 EC Scores.xlsx', key_sheet_mapping[age_group], header=None)

        ac_raw = raw_scores_df.loc[i, "AC Raw"]
        ec_raw = raw_scores_df.loc[i, "EC Raw"]

        # Match AC Raw score to the corresponding range in the AC reference table
        ac_ss_score = -999
        ac_percentile_rank = -999
        if ac_raw == -999:
            ac_ss_score = -999
            ac_percentile_rank = -999
        else:
            for index, row in ac_ref_table.iterrows():  # Iterate through the rows of the ac_ref_table DataFrame
                if ac_raw == row.iloc[0]:  # Check if raw score matches value in first column of ac_ref_table
                    ac_ss_score = row.iloc[1]  # If a match is found, retrieve the standard score from the second column
                    # If the raw score is less than the value in the second row of the first column in "ac_ref_table",
                elif ac_raw < ac_ref_table.iloc[1, 0]:
                    ac_ss_score = ac_ref_table.iloc[0, 1]  # Set ss_score to the value in the first row of second column
                elif ac_raw == 999:  # Account for empty values
                    ac_ss_score = 999

            for index, row in ac_ref_table.iterrows(): # Iterate through the rows of the ac_ref_table DataFrame
                if ac_raw == row.iloc[0]:  # Check if raw score matches value in first column of ac_ref_table
                    ac_percentile_rank = row.iloc[2]  # If match is found, retrieve percentile rank from third column
                # If the raw score is less than the value in the second row of the first column in "ac_ref_table",
                elif ac_raw < ac_ref_table.iloc[1, 0]:
                    ac_percentile_rank = ac_ref_table.iloc[0, 2]  # Set PR to value in 1st row of 3rd column
                elif ac_raw == 999:  # Account for empty values
                    ac_percentile_rank = 999

        # Match EC Raw score to the corresponding range in the EC reference table
        ec_ss_score = -999
        ec_percentile_rank = -999
        if ec_raw == -999:
            ec_ss_score = -999
            ec_percentile_rank = -999
        else:
            # Iterate through each row in the EC reference table
            for index, row in ec_ref_table.iterrows():
                # Check if the raw score matches the value in the first column of ec_ref_table
                if ec_raw == row.iloc[0]:
                    ec_ss_score = row.iloc[1]  # Retrieve the standard score from the second column
                    # If the raw score is less than the value in the second row of the first column in "ec_ref_table",
                elif ec_raw < ec_ref_table.iloc[1, 0]:
                    ec_ss_score = ec_ref_table.iloc[0, 1]  # Set ss_score to the value in the first row of second column
                elif ec_raw == 999:  # Account for empty values
                    ec_ss_score = 999

            # Iterate through each row in the EC reference table
            for index, row in ec_ref_table.iterrows():
                # Check if the raw score matches the value in the first column of ec_ref_table
                if ec_raw == row.iloc[0]:
                    ec_percentile_rank = row.iloc[2]  # Retrieve percentile rank from the third column
                # If the raw score is less than the value in the second row of the first column in "ec_ref_table",
                elif ec_raw < ec_ref_table.iloc[1, 0]:
                    ec_percentile_rank = ec_ref_table.iloc[0, 2]  # Set PR to value in 1st row of 3rd column
                elif ec_raw == 999:  # Account for empty values
                    ec_percentile_rank = 999

        df_ss_scores.loc[i, "AC_SS"] = ac_ss_score
        df_ss_scores.loc[i, "AC_Percentile_Rank"] = ac_percentile_rank
        df_ss_scores.loc[i, "EC_SS"] = ec_ss_score
        df_ss_scores.loc[i, "EC_Percentile_Rank"] = ec_percentile_rank


    # Calculate Total Language Standard Score and Percentile Rank
    df_total_lang_ss_scores = pd.DataFrame(columns=["Total Language Standard Score", "Total Language Percentile Rank"])
    total_ss_ref_table = pd.read_excel(root_filepath + 'Assessment_Packages/PLS_package/PLS_ref_materials/A.3 Total Standard Score.xlsx', header=None)

    # Iterate through each row in df_ss_scores
    for i, row in df_ss_scores.iterrows():
        if row['AC_SS'] == 999 or row['EC_SS'] == 999:
            # If either AC_SS or EC_SS is 999, set total_ss_score and total_pr_score to 999
            total_ss_score = 999
            total_pr_score = 999
        else:
            # Calculate sum of AC_SS and EC_SS
            sum_ac_ec_ss_score = row['AC_SS'] + row['EC_SS']
            
            # Iterate through each row in the total_ss_ref_table
            for index, ref_row in total_ss_ref_table.iterrows():
                range_of_sum = ref_row.iloc[0]  # Get the range of sum from the reference table
                total_ss_value = ref_row.iloc[1]  # Get the corresponding total standard score
                total_pr_value = ref_row.iloc[2]  # Get the corresponding total percentile rank
                
                # Check if sum_ac_ec_ss_score is 999 (accounting for empty values)
                if sum_ac_ec_ss_score == 999:
                    total_ss_score = 999
                    total_pr_score = 999
                    break

                # Check if range_of_sum contains a hyphen (indicating a range)
                elif '-' in str(range_of_sum):
                    lower, upper = map(int, range_of_sum.split('-'))  # Split range into lower and upper bounds
                    # If sum_ac_ec_ss_score falls within the range, assign corresponding scores
                    if lower <= sum_ac_ec_ss_score <= upper:
                        total_ss_score = total_ss_value
                        total_pr_score = total_pr_value
                        break
                # If range_of_sum is a single value
                elif int(range_of_sum) == sum_ac_ec_ss_score:
                    total_ss_score = total_ss_value
                    total_pr_score = total_pr_value
                    break

        # Store total language standard scores and percentile ranks in df_total_lang_ss_scores after the inner loop
        df_total_lang_ss_scores.loc[i, "Total Language Standard Score"] = total_ss_score
        df_total_lang_ss_scores.loc[i, "Total Language Percentile Rank"] = total_pr_score

    """
    Purpose: Returns Total Language Age Equivalents in Years and Months

    - Initializes empty dataframe (df_total_ae_scores)
    - reads in Total Age Equivalent reference table
    - Takes participant's raw AC and EC scores from raw_scores_df, and calculates their sum (sum_ac_ec_raw)
    - Using sum of raw scores, finds corresponding Total Age Equivalent in Total Age Equivalent reference table
    - Converts age equivalent into both years format (#y#m) and months format (##)
    - Saves age equivalents in new dataframe: df_total_ae_scores
    """
    # AC and EC Age Equivalents- Years and Months
    df_ac_ec_ae_scores = pd.DataFrame()  # Initialize a DataFrame to store age equivalents

    # AC Age Equivalents
    ac_ae_ref_table = pd.read_excel(root_filepath + 'Assessment_Packages/PLS_package/PLS_ref_materials/A.4 AC gsv + ae.xlsx')  # Read AC reference table

    # EC Age Equivalents
    ec_ae_ref_table = pd.read_excel(root_filepath + 'Assessment_Packages/PLS_package/PLS_ref_materials/A.5 EC gsv + ae.xlsx')  # Read EC reference table

    # Iterate over each participant in the raw_scores_df DataFrame
    for i, row in raw_scores_df.iterrows():
        # Extract raw scores for AC and EC subscales
        ac_raw = raw_scores_df.loc[i, "AC Raw"]
        ec_raw = raw_scores_df.loc[i, "EC Raw"]

        # Find AC Age Equivalent
        ac_age_equivalent = -999
        if ac_raw != -999:
            ac_match = ac_ae_ref_table.loc[ac_ae_ref_table.iloc[:, 0] == ac_raw]
            if not ac_match.empty:
                ac_age_equivalent = ac_match.iloc[0, 1]

        # Calculate AC age equivalent in years and months
        if ac_age_equivalent == -999:
            ac_age_equivalent_years = -999
            ac_age_equivalent_months = -999
        else:
            # Extract years and months
            match = re.match(r'([<>]?)(\d+)-(\d+)', ac_age_equivalent)
            if match:
                prefix = match.group(1)
                years = int(match.group(2))
                months = int(match.group(3))
                ac_age_equivalent_years = f'{prefix}{years}y{months}m' if prefix else f'{years}y{months}m'
                ac_age_equivalent_months = f'{prefix}{years * 12 + months}' if prefix else f'{years * 12 + months}'
            else:
                raise ValueError(f"Unsupported format for ac_age_equivalent: {ac_age_equivalent}")

        # Store AC age equivalents in the DataFrame
        df_ac_ec_ae_scores.loc[i, "AC AE Years"] = ac_age_equivalent_years
        df_ac_ec_ae_scores.loc[i, "AC AE Months"] = ac_age_equivalent_months

        # Find EC Age Equivalent
        ec_age_equivalent = -999
        if ec_raw != -999:
            ec_match = ec_ae_ref_table.loc[ec_ae_ref_table.iloc[:, 0] == ec_raw]
            if not ec_match.empty:
                ec_age_equivalent = ec_match.iloc[0, 1]

        if ec_age_equivalent == -999:
            ec_age_equivalent_years = -999
            ec_age_equivalent_months = -999
        else:
            # Extract years and months
            match = re.match(r'([<>]?)(\d+)-(\d+)', ec_age_equivalent)
            if match:
                prefix = match.group(1)
                years = int(match.group(2))
                months = int(match.group(3))
                ec_age_equivalent_years = f'{prefix}{years}y{months}m' if prefix else f'{years}y{months}m'
                ec_age_equivalent_months = f'{prefix}{years * 12 + months}' if prefix else f'{years * 12 + months}'
            else:
                raise ValueError(f"Unsupported format for ec_age_equivalent: {ec_age_equivalent}")

        # Store EC age equivalents in the DataFrame
        df_ac_ec_ae_scores.loc[i, "EC AE Years"] = ec_age_equivalent_years
        df_ac_ec_ae_scores.loc[i, "EC AE Months"] = ec_age_equivalent_months

    # Initialize empty dataframe for total age equivalents
    df_total_ae_scores = pd.DataFrame()

    # Reading Total Age Equivalents reference table
    total_ae_ref_table = pd.read_excel(root_filepath + 'Assessment_Packages/PLS_package/PLS_ref_materials/A.6 Total ae.xlsx')

    # Iterate over rows of the DataFrame
    for i, row in raw_scores_df.iterrows():
        # Extract AC and EC raw scores from the DataFrame
        ac_raw = row["AC Raw"]
        ec_raw = row["EC Raw"]

        if ac_raw == -999 or ec_raw == -999:
            sum_ac_ec_raw = -999
        else:
            sum_ac_ec_raw = ac_raw + ec_raw

        total_age_equivalent = -999
        if sum_ac_ec_raw != -999:
            total_match = total_ae_ref_table.loc[total_ae_ref_table.iloc[:, 0] == sum_ac_ec_raw]
            if not total_match.empty:
                total_age_equivalent = total_match.iloc[0, 1]

        if total_age_equivalent == -999:
            total_age_equivalent_years = -999
            total_age_equivalent_months = -999
        else:
            # Extract years and months
            match = re.match(r'([<>]?)(\d+)-(\d+)', total_age_equivalent)
            if match:
                prefix = match.group(1)
                years = int(match.group(2))
                months = int(match.group(3))
                total_age_equivalent_years = f'{prefix}{years}y{months}m' if prefix else f'{years}y{months}m'
                total_age_equivalent_months = f'{prefix}{years * 12 + months}' if prefix else f'{years * 12 + months}'
            else:
                raise ValueError(f"Unsupported format for total_age_equivalent: {total_age_equivalent}")

        # Append the Total Age Equivalents to df_total_ae_scores dataframe
        df_total_ae_scores.loc[i, "Total AE Years"] = total_age_equivalent_years
        df_total_ae_scores.loc[i, "Total AE Months"] = total_age_equivalent_months

    '''
    Purpose:  Returns AC and EC Growth Scale Values (GSVs)

    - Initializes empty dataframe (df_gsv_scores)

    For both AC and EC:
    - Reads in (ac/ec) gsv reference table (same as age equivalent tables)
    - Takes participant's raw scores from raw_scores_df
    - Using raw scores, finds corresponding GSV in age equivalent reference table
    - Saves age equivalents in new dataframe: df_gsv_scores    
    '''

    # Initialize empty dataframe for Growth Scale Values
    df_gsv_scores = pd.DataFrame()

    # Iterate over rows of the DataFrame
    for i, row in raw_scores_df.iterrows():
        # Extract AC and EC raw scores from the DataFrame
        ac_raw = row["AC Raw"]
        ec_raw = row["EC Raw"]

        # Initialize AC and EC GSV
        ac_gsv = -999
        ec_gsv = -999

        if ac_raw != -999:
            ac_match = ac_ae_ref_table.loc[ac_ae_ref_table.iloc[:, 0] == ac_raw]
            if not ac_match.empty:
                ac_gsv = ac_match.iloc[0, 2]

        if ec_raw != -999:
            ec_match = ec_ae_ref_table.loc[ec_ae_ref_table.iloc[:, 0] == ec_raw]
            if not ec_match.empty:
                ec_gsv = ec_match.iloc[0, 2]

        # Store GSVs in df_gsv_scores
        df_gsv_scores.loc[i, "AC GSV"] = str(ac_gsv)
        df_gsv_scores.loc[i, "EC GSV"] = str(ec_gsv)

    # Merge all score dataframes together
    dfs_to_merge = [raw_scores_df, df_ss_scores, df_total_lang_ss_scores,
                    df_total_ae_scores, df_gsv_scores, df_ac_ec_ae_scores]

    # Sequentially merge DataFrames
    df_complete = raw_scores_df
    for df in dfs_to_merge[1:]:
        df_complete = df_complete.merge(df, left_index=True, right_index=True, how="left")

    # Clean up the study id to take out the appended age value
    df_complete.index = df_complete.index.str.split("-").str[0]
    df_complete.index = df_complete.index.rename("subject_id")

    # Rename columns
    column_mapping = {
        "id": id_column,
        "Event Name": event_name_column,
        "AC Raw": "pls_aud_comp_raw",
        "EC Raw": "pls_exp_comm_raw",
        "AC_SS": "pls_aud_comp_ss",
        "AC_Percentile_Rank": "pls_aud_comp_pr",
        "EC_SS": "pls_exp_comm_ss",
        "EC_Percentile_Rank": "pls_exp_comm_pr",
        "AC AE Years": "pls_aud_comp_ae_ym",
        "Total Language Standard Score": "pls_total_ss_2",
        "Total Language Percentile Rank": "pls_total_pr",
        "AC AE Months": "pls_aud_comp_ae_m",
        "EC AE Years": "pls_exp_comm_ae_ym",
        "EC AE Months": "pls_exp_comm_ae_m",
        "Total AE Years": "pls_total_ae_ym",
        "Total AE Months": "pls_total_ae_m",
        "AC GSV": "pls_gsv_ac",
        "EC GSV": "pls_gsv_ec"
    }
    df_complete.rename(columns=column_mapping, inplace=True)

    # Adds column to indicate PLS form completion status
    df_complete['preschool_language_scale_complete'] = 2

    # Convert columns ending in _raw, _ae_m, _ss, and _pr to integers
    columns_to_convert = df_complete.filter(regex='_raw$|_ss$|_pr$').columns
    df_complete[columns_to_convert] = df_complete[columns_to_convert].astype(int)

    # Define the columns to include in the final DataFrame
    columns_to_include = [
        'redcap_event_name', 'pls_aud_comp_raw', 'pls_aud_comp_ss',
        'pls_aud_comp_pr', 'pls_aud_comp_ae_ym', 'pls_aud_comp_ae_m', 'pls_exp_comm_raw',
        'pls_exp_comm_ss', 'pls_exp_comm_pr', 'pls_exp_comm_ae_ym', 'pls_exp_comm_ae_m', 'pls_total_ss_2', "pls_total_pr",
        'pls_total_ae_ym', 'pls_total_ae_m', 'pls_gsv_ac', 'pls_gsv_ec', 'preschool_language_scale_complete'
    ]

    # Create the final DataFrame by selecting only the desired columns
    df_final = df_complete[columns_to_include].copy()

    # Save the final DataFrame
    if file_ext == ".xlsx":
        df_final.to_excel(f'{root_filepath}{output_file_location}/Importable_PLS_{datetime.datetime.now().date()}.xlsx')
    elif file_ext == ".csv":
        df_final.to_csv(f'{root_filepath}{output_file_location}/Importable_PLS_{datetime.datetime.now().date()}.csv')
    
    print("PLS Auto-Scoring Complete!")
    
    return df_final