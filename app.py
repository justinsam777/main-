import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def clean_h_no(h_no):
    return re.sub(
        r'^\s*h\s*\.?\s*no\s*[:.]?\s*',
        '',
        str(h_no),
        flags=re.IGNORECASE
    ).strip()

def encode_h_no(h_no):
    address = str(h_no) + "-0"
    s, main = "", ""
    count, zero_count = 1, 0

    for ch in address:
        if ch.isalnum():
            s += ch
        else:
            try:
                if count == 1:
                    main = str(int(s) + 100)
                elif count == 2:
                    main += "-" + ("0" + str(int(s)))
                else:
                    main += "-" + str(len(s) - 1) + s
                    zero_count += 1
                count += 1
            except:
                main += "-" + s
            s = ""
            if ch in [' ', ',']:
                break

    main += " " + ("0" * (zero_count + 2))
    return main.strip()

def dh_sort_key(val):
    return re.sub(r'[^0-9]', '', str(val)).zfill(30)

def load_file(file):
    return pd.read_excel(file) if file.name.endswith(('xls', 'xlsx')) else pd.read_csv(file)

# =========================================================
# STREAMLIT UI
# =========================================================

st.set_page_config(page_title="PS_No and Section_No Assignment", layout="centered")
st.title("PS_No and Section_No Assignment")

# =========================================================
# UPLOAD ROW 1 – REF HOUSE
# =========================================================

col1, col2 = st.columns([5, 1])

with col1:
    uploaded_ref = st.file_uploader(
        "Upload Ref_House Excel/CSV file",
        type=['xls', 'xlsx', 'csv']
    )

with col2:
    st.markdown("###")
    with open("Ref_House.xlsx", "rb") as f:
        st.download_button(
            "⬇ Sample",
            f,
            file_name="Ref_House.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =========================================================
# UPLOAD ROW 2 – MAIN ASSIGN
# =========================================================

col3, col4 = st.columns([5, 1])

with col3:
    uploaded_main = st.file_uploader(
        "Upload Main_Assing Excel/CSV file",
        type=['xls', 'xlsx', 'csv']
    )

with col4:
    st.markdown("###")
    with open("Main_assign.xlsx", "rb") as f:
        st.download_button(
            "⬇ Sample",
            f,
            file_name="Main_assign.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =========================================================
# PROCESS FILES
# =========================================================

if uploaded_ref and uploaded_main:
    st.info("Processing files, please wait...")

    df_ref = load_file(uploaded_ref)
    df_main = load_file(uploaded_main)

    # ---- REF PROCESSING ----
    df_ref['clean_H_No'] = df_ref['H_No'].apply(clean_h_no)
    df_ref['dh_no'] = df_ref['clean_H_No'].apply(encode_h_no)
    df_ref['dh_key'] = df_ref['dh_no'].apply(dh_sort_key)

    # ---- MAIN RANGE PROCESSING ----
    df_main['from_dh'] = df_main['from'].apply(encode_h_no)
    df_main['to_dh'] = df_main['to'].apply(encode_h_no)

    df_main['start'] = df_main[['from_dh', 'to_dh']].min(axis=1).apply(dh_sort_key)
    df_main['end'] = df_main[['from_dh', 'to_dh']].max(axis=1).apply(dh_sort_key)

    df_main = df_main.sort_values('start').reset_index(drop=True)

    # ---- FAST RANGE MATCH ----
    starts = df_main['start'].values
    ends = df_main['end'].values

    idx = np.searchsorted(starts, df_ref['dh_key'], side='right') - 1
    valid = (idx >= 0) & (df_ref['dh_key'].values <= ends[idx])

    df_ref['ps'] = np.where(valid, df_main.loc[idx, 'ps'].values, np.nan)
    df_ref['sec'] = np.where(valid, df_main.loc[idx, 'sec'].values, np.nan)

    # ---- OUTPUT ----
    output_df = pd.DataFrame({
        's_no': df_ref['S_No'],
        'dh_no': df_ref['dh_no'],
        'ps': df_ref['ps'].astype('Int64'),
        'sec': df_ref['sec'].astype('Int64'),
        'odh_no': df_ref['H_No'],
        'ref_no': df_ref['Ref_no']
    })

    buffer = BytesIO()
    output_df.to_excel(buffer, index=False)
    buffer.seek(0)

    st.success("Processing complete ✅")

    st.download_button(
        "📥 Download Result Excel",
        buffer,
        "F_Output_Final.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
