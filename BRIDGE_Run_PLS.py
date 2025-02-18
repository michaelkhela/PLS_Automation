# CREATORS: Michael Khela and Shefali Verma
# PURPOSE: For more details, see the PLS Automation Protocol

import sys

# USER INPUTS #

# INSERT YOUR FILE PATH TO THE AUTOMATED_ASSESSMENTS
root_filepath = r'\\RC-FS.tch.harvard.edu\dmc-nelson\Groups\LCN-Nelson-Clinical\Groups\P00025493 = Fragile X\BRIDGE Study\Data\Automated_Assessments/'

# UPDATE THE NAME OF THE CSV FILE CONTAINING THE RAW SCORES (REDcap export)
REDCap_filepath = ''

output_file_location = 'PLS/'

# DO NOT EDIT BELOW ------------------------------------------------
id_column = "subject_id"
event_name_column = "redcap_event_name"
age_column = "chron_age_pls"
ac_column = "pls_aud_comp_raw"
ec_column = "pls_exp_comm_raw"
REDCap_raw_scores_file = ("Assessment_Packages/PLS_package/PLS_inputs/" + REDCap_filepath)

# DO NOT EDIT BELOW ------------------------------------------------
sys.path.append(root_filepath + 'Assessment_Packages/PLS_package/PLS_Background_code/')
from BRIDGE_PLS import pls_Scoring_Fcn

pls_Scoring_Fcn(root_filepath, REDCap_raw_scores_file, 
                   id_column, 
                   event_name_column,
                   age_column, ac_column, ec_column, output_file_location)