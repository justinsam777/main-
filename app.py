import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

# Function to clean house numbers by removing common prefixes
def clean_h_no(h_no_str):
    h_no_str = re.sub(r'^\s*h\s*\.?\s*no\s*[:.]?\s*', '', str(h_no_str), flags=re.IGNORECASE)
    return h_no_str.strip()

# Java-style house number encoding
def encode_h_no(h_no):
    address = str(h_no) + "-0"
    s = ""
    main = ""
    count = 1
    zero_count = 0
    for ch in address:
        if ch.isalpha() or ch.isdigit():
            s += ch
        else:
            if count == 1:
                try:
                    n = int(s) + 100
                    main = str(n)
                    count += 1
                except:
                    main += "-" + s
            elif count == 2:
                try:
                    n1 = int(s)
                    s2 = "0" + str(n1)
                    main += "-" + s2
                    count += 1
                except:
                    main += "-" + s
            else:
                try:
                    n6 = int(s)
                    length = len(s) - 1
                    s6 = str(length) + s
                    main += "-" + s6
                    zero_count += 1
                except:
                    main += "-" + s
            s = ""
            if ch in [' ', ',', 'r', 'R', 't', 'T']:
                break
    zero = "0" * (zero_count + 2)
    main += " " + zero
    return main

# Streamlit UI
st.title("PS_No and Section_No Assignment Prakash")

uploaded_ref = st.file_uploader("Upload Ref_House Excel/CSV file", type=['xls', 'xlsx', 'csv'])
uploaded_main = st.file_uploader("Upload Main_Assing Excel/CSV file", type=['xls', 'xlsx', 'csv'])

def process_files(ref_file, main_file):
    # Load dataframes respecting file extension
    if ref_file.name.endswith(('xls', 'xlsx')):
        df_ref = pd.read_excel(ref_file)
    else:
        df_ref = pd.read_csv(ref_file)

    if main_file.name.endswith(('xls', 'xlsx')):
        df_main = pd.read_excel(main_file)
    else:
        df_main = pd.read_csv(main_file)

    # Cleanup and encode
    df_ref['clean_H_No'] = df_ref['H_No'].apply(clean_h_no)
    df_ref['dh_no'] = df_ref['clean_H_No'].apply(encode_h_no)

    df_main['from_dh_no'] = df_main['from'].apply(encode_h_no)
    df_main['to_dh_no'] = df_main['to'].apply(encode_h_no)

    # Matching function
    def find_ps_sec(h_dh_no):
        for _, row in df_main.iterrows():
            start = min(row['from_dh_no'], row['to_dh_no'])
            end = max(row['from_dh_no'], row['to_dh_no'])
            if start <= h_dh_no <= end:
                return pd.Series([row['ps'], row['sec']])
        return pd.Series([np.nan, np.nan])

    df_ref[['ps', 'sec']] = df_ref['dh_no'].apply(find_ps_sec)

    # Prepare output DataFrame
    df_out = pd.DataFrame({
        's_no': df_ref['S_No'],
        'dh_no': df_ref['dh_no'],
        'ps': df_ref['ps'].astype('Int64'),
        'sec': df_ref['sec'].astype('Int64'),
        'odh_no': df_ref['H_No'],
        'ref_no': df_ref['Ref_no']
    })

    return df_out

if uploaded_ref and uploaded_main:
    st.write("Processing files, please wait...")
    result_df = process_files(uploaded_ref, uploaded_main)

    # Convert to Excel bytes
    output = BytesIO()
    result_df.to_excel(output, index=False)
    output.seek(0)

    st.success("Processing complete!")

    st.download_button(
        label="Download Result Excel",
        data=output,
        file_name="F_Output_Final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
