# PLS Auto-Scoring  

## Overview  

PLS Auto-Scoring is a Python-based tool designed to automate the scoring of Preschool Language Scale (PLS) assessments for the BRIDGE study. This script processes raw scores from a REDCap export, calculating additional scores except for total raw and standard total scores, which are auto-calculated in REDCap.  

This tool was created by Shefali Verma and Michael Khela for use across the LCN, tailored specifically for the BRIDGE REDCap build.  

## Authors  

Michael Khela  
Email: michael.khela99@gmail.com  

Shefali Verma
Email: 

## Requirements  

**Python Version:** 3.12.1  

**Required Python libraries:**  
- pandas (2.2.0)  
- openpyxl (3.1.2)  

To install dependencies, run:  

```sh
pip install pandas openpyxl
```

## Installation  

1. Clone or download this repository.  
2. Copy the relevant scripts to your working directory.  
3. Ensure the input CSV file is formatted correctly with the required columns.  

## Usage  

### 1. Identify Participants for Scoring  
- Access the `BRIDGE_FRAXA_Data_Tracker` to find participants with PLS data ready for scoring.  
- Only score participants labeled as **"Verified raw score entry"** in the PLS column.  

### 2. Export Data from REDCap  
1. Navigate to Internal REDCap and edit the `PLS_raw_for_auto_scoring` report.  
2. Filter for specific `subject_id` and `visit#`.  
3. Click **Export Data** and choose **Raw Data** format.  
4. Save the file in the `PLS_inputs` folder.  
5. Ensure the file remains a CSV and is not renamed.  

### 3. Run the Script  
Run the following command in your terminal:  

```sh
python BRIDGE_Run_PLS.py
```

Alternatively, run the script in **Spyder** (Anaconda) by:  
- Opening `BRIDGE_Run_PLS.py`.  
- Updating the `Automated_Assessments` path if necessary.  
- Ensuring the `REDCap_file name` matches the downloaded CSV.  
- Clicking **Run** to execute the script.  

Once completed, a message should confirm successful execution.  

### 4. Output  
The script generates an output CSV file in the `PLS` directory, following this format:  

```
Importable_PLS_YYYY-MM-DD.csv
```  

This file is structured for direct import into REDCap.  

## Importing Data into REDCap  

1. Navigate to **Data Import Tool** in REDCap.  
2. Upload the generated file (`Importable_PLS_YYYY-MM-DD.csv`).  
3. Review the **data display table**:  
   - No data should be highlighted in red, except `preschool_language_scale_complete`.  
   - Verify the correct IDs, arms, and visits.  
   - Check for `-999` values and confirm they make sense.  
4. If correct, click **Import Data**.  

### 5. Update the BRIDGE_FRAXA_Data_Tracker  
- Mark `Verified` in the PLS column for all imported participants.  
- This ensures clarity for future assessments.  

---

## Notes  

- This script is specifically tailored for the BRIDGE study.  
- If a `-999` value appears, it indicates missing data.  
- Only **Research Assistants** should import the script's output into Internal REDCap.  

## Contact  

For issues or inquiries, contact:  
Michael Khela – michael.khela99@gmail.com  
